#!/usr/bin/env python3
"""
RAG Backend API for AI/ML Educational Platform
- POST /query  (guardrail → intent → Milvus (+ Neo4j) → (rerank) → LLM → answer + citations + next_concepts)
- POST /star   (store a user's starred doc_id)
- GET  /stars  (list user's stars)
- GET  /next   (Neo4j next-concepts)
"""

from typing import List, Literal, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field
import os
import math
import time
import httpx
from dotenv import load_dotenv

# Load environment variables and configure SSL
load_dotenv()
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'

# Initialize OpenAI client
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
try:
    from openai import OpenAI
    oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if USE_OPENAI else None
except Exception as e:
    print(f"⚠️ OpenAI initialization failed: {e}")
    oai = None

# Milvus Cloud (Zilliz) configuration
from pymilvus import connections, Collection
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")

# Neo4j Aura configuration
from neo4j import GraphDatabase
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Collection names
COLL_RICH_EDUCATION = "rich_ml_education"      # Your main education collection (1393 concepts)
COLL_YOUTUBE_VIDEOS = "youtube_creator_videos"  # StatQuest videos with generated content

# --------------------------------- Data models ----------------------------------

Intent = Literal["explain", "define", "compare", "related", "next"]

class QueryRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="Supabase user id (JWT-verified in prod)")
    question: str
    audience: Literal["kid", "teen", "adult"] = "kid"
    top_k: int = 12
    use_graph: bool = True

class Citation(BaseModel):
    doc_id: str
    title: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    kind: Optional[str] = None
    score: Optional[float] = None

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    next_concepts: List[str] = []
    intent: Intent
    latency_ms: int

class StarRequest(BaseModel):
    user_id: str
    doc_id: str
    note: Optional[str] = None

class StarRecord(BaseModel):
    doc_id: str
    note: Optional[str] = None
    created_at: Optional[str] = None

app = FastAPI(title="AI/ML Tutor API")

# --------------------------------- Utilities ------------------------------------

def guardrail_ml_only(text: str) -> tuple[bool, str]:
    """Cheap ML-only gate + basic moderation fallback."""
    t = text.lower().strip()
    if not t or len(t) < 2:
        return False, "Empty or too short."
    # allow common follow-ups
    cont = {"yes","ok","okay","continue","next","why","how","what","explain","example"}
    if t in cont:
        return True, "Follow-up allowed."
    # quick denylist (extend as needed)
    deny = ["recipe","cooking","celebrity","politics","dating","religion","sports betting"]
    if any(x in t for x in deny):
        return False, "Out of scope (non-ML)."
    # allow if contains ML-ish tokens
    allow = ["machine learning","ml","ai","deep learning","neural","regression","classification",
             "clustering","transformer","embedding","vector","pca","statistic","statquest"]
    if any(x in t for x in allow):
        return True, "Looks ML-related."
    # fallback: allow if question-like
    if any(x in t for x in ["what is","how does","explain","difference","compare","when to use"]):
        return True, "Generic question allowed."
    return True, "Permissive default (tighten later)."

def classify_intent(text: str) -> Intent:
    t = text.lower()
    if any(x in t for x in ["compare","difference","vs","versus","contrast"]):
        return "compare"
    if any(x in t for x in ["related","relation","how is x related","connection"]):
        return "related"
    if any(x in t for x in ["what next","what should i learn next","next after","prereq","prerequisite"]):
        return "next"
    if any(x in t for x in ["define","definition","meaning of"]):
        return "define"
    return "explain"

def mmr_select(results: List[Dict], k: int = 8, lambda_mult: float = 0.6) -> List[Dict]:
    """Basic MMR: assumes each result has 'embedding' (vector) and 'score' (float).
       If you don’t have embeddings here, just return top-k by score."""
    if not results:
        return []
    if "embedding" not in results[0]:
        return sorted(results, key=lambda r: r.get("score", 0), reverse=True)[:k]
    selected = []
    cand = results[:]
    # normalize: sort by score first
    cand.sort(key=lambda r: r.get("score", 0), reverse=True)
    while cand and len(selected) < k:
        if not selected:
            selected.append(cand.pop(0))
            continue
        # pick candidate that maximizes lambda*relevance - (1-lambda)*max_sim(selected)
        def cosine(a,b):
            dot = sum(x*y for x,y in zip(a,b))
            na = math.sqrt(sum(x*x for x in a))
            nb = math.sqrt(sum(x*x for x in b))
            return dot/(na*nb+1e-9)
        best_i, best_val = 0, -1e9
        for i,c in enumerate(cand):
            rel = c.get("score", 0)
            sim = max(cosine(c["embedding"], s["embedding"]) for s in selected)
            val = lambda_mult*rel - (1-lambda_mult)*sim
            if val > best_val:
                best_val, best_i = val, i
        selected.append(cand.pop(best_i))
    return selected

# ---------------------------- Milvus retrieval --------------------------

def connect_milvus():
    """Connect to Zilliz Cloud"""
    try:
        if not MILVUS_URI or not MILVUS_TOKEN:
            print("❌ MILVUS_URI or MILVUS_TOKEN not configured")
            return False
        
        connections.connect(
            alias="default",
            uri=MILVUS_URI,
            token=MILVUS_TOKEN
        )
        print("✅ Connected to Zilliz Cloud")
        return True
    except Exception as e:
        print(f"❌ Milvus connection failed: {e}")
        return False

def generate_query_embedding(query: str) -> List[float]:
    """Generate embedding for search query using OpenAI"""
    if not oai:
        return []
    
    try:
        response = oai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return []

def milvus_search(collection_name: str, query: str, top_k: int = 12) -> List[Dict[str, Any]]:
    """Search Milvus collection with vector similarity"""
    try:
        # Generate query embedding
        query_embedding = generate_query_embedding(query)
        if not query_embedding:
            return []
        
        # Get collection
        collection = Collection(collection_name)
        collection.load()
        
        # Define search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        # Perform search based on collection type
        if collection_name == COLL_RICH_EDUCATION:
            # Rich education collection
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["id", "concept_slug", "concept_title", "slice", "text", "tags"]
            )
        else:
            # YouTube videos collection
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["doc_id", "title", "source_url", "source", "kind", "text", "tags"]
            )
        
        # Process results
        hits = []
        for result_batch in results:
            for hit in result_batch:
                if collection_name == COLL_RICH_EDUCATION:
                    hits.append({
                        "doc_id": hit.entity.get("id", ""),
                        "title": hit.entity.get("concept_title", ""),
                        "source": "rich_education",
                        "source_url": "",
                        "kind": hit.entity.get("slice", ""),
                        "text": hit.entity.get("text", ""),
                        "score": hit.score,
                        "concept_slug": hit.entity.get("concept_slug", ""),
                        "tags": hit.entity.get("tags", [])
                    })
                else:
                    hits.append({
                        "doc_id": hit.entity.get("doc_id", ""),
                        "title": hit.entity.get("title", ""),
                        "source": hit.entity.get("source", ""),
                        "source_url": hit.entity.get("source_url", ""),
                        "kind": hit.entity.get("kind", ""),
                        "text": hit.entity.get("text", ""),
                        "score": hit.score,
                        "tags": hit.entity.get("tags", "")
                    })
        
        return hits
        
    except Exception as e:
        print(f"❌ Milvus search failed for {collection_name}: {e}")
        return []

def merged_search(query: str, top_k: int = 12) -> List[Dict]:
    """Search across both Milvus collections and merge results"""
    hits = []
    
    # Search rich education collection (primary)
    hits += milvus_search(COLL_RICH_EDUCATION, query, top_k=int(top_k * 0.7))
    
    # Search YouTube videos collection (secondary)  
    hits += milvus_search(COLL_YOUTUBE_VIDEOS, query, top_k=int(top_k * 0.3))
    
    # Sort by score and return top results
    hits.sort(key=lambda r: r.get("score", 0), reverse=True)
    return hits[:top_k]

# ---------------------------- Neo4j graph queries -----------------------

def neo4j_driver():
    """Connect to Neo4j Aura Cloud"""
    try:
        if not NEO4J_URI or not NEO4J_PASSWORD:
            print("❌ NEO4J_URI or NEO4J_PASSWORD not configured")
            return None
        
        # Use bolt+s for direct connection (from our SSL learning)
        uri = NEO4J_URI
        if uri.startswith("neo4j+s://"):
            uri = uri.replace("neo4j+s://", "bolt+s://")
        
        driver = GraphDatabase.driver(uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        
        return driver
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return None

def graph_next_concepts(concept_or_query: str, limit: int = 3) -> List[str]:
    """Return suggested next concepts from the knowledge graph"""
    drv = neo4j_driver()
    if not drv:
        return []
    
    try:
        with drv.session() as session:
            # Try multiple strategies to find related concepts
            
            # Strategy 1: Direct concept match
            cypher1 = """
            MATCH (c:Concept)-[:REQUIRES|RELATES_TO|CONTRASTS_WITH]->(n:Concept)
            WHERE toLower(c.name) CONTAINS toLower($q) OR toLower(c.slug) CONTAINS toLower($q)
            RETURN DISTINCT n.name AS name, n.slug AS slug, n.level AS level
            LIMIT $lim
            """
            
            result = session.run(cypher1, q=concept_or_query, lim=limit)
            concepts = [record["name"] for record in result]
            
            # Strategy 2: If no direct matches, try video connections
            if not concepts:
                cypher2 = """
                MATCH (v:Video)-[:COVERS]->(c:Concept)-[:REQUIRES|RELATES_TO]->(n:Concept)
                WHERE toLower(v.title) CONTAINS toLower($q)
                RETURN DISTINCT n.name AS name, n.level AS level
                ORDER BY n.level
                LIMIT $lim
                """
                
                result = session.run(cypher2, q=concept_or_query, lim=limit)
                concepts = [record["name"] for record in result]
            
            # Strategy 3: Fallback to popular beginner concepts
            if not concepts:
                cypher3 = """
                MATCH (c:Concept)
                WHERE c.level = 'beginner'
                RETURN c.name AS name
                ORDER BY c.name
                LIMIT $lim
                """
                
                result = session.run(cypher3, lim=limit)
                concepts = [record["name"] for record in result]
            
            return concepts
            
    except Exception as e:
        print(f"❌ Neo4j query failed: {e}")
        return []
    finally:
        if drv:
            drv.close()

def get_concept_relationships(concept_name: str) -> Dict[str, List[str]]:
    """Get detailed relationships for a concept"""
    drv = neo4j_driver()
    if not drv:
        return {}
    
    try:
        with drv.session() as session:
            cypher = """
            MATCH (c:Concept)
            WHERE toLower(c.name) CONTAINS toLower($concept) OR toLower(c.slug) CONTAINS toLower($concept)
            OPTIONAL MATCH (c)-[:REQUIRES]->(req:Concept)
            OPTIONAL MATCH (c)-[:RELATES_TO]->(rel:Concept)
            OPTIONAL MATCH (c)-[:CONTRASTS_WITH]->(con:Concept)
            OPTIONAL MATCH (prerequisite:Concept)-[:REQUIRES]->(c)
            RETURN c.name as concept,
                   collect(DISTINCT req.name) as requires,
                   collect(DISTINCT rel.name) as related,
                   collect(DISTINCT con.name) as contrasts,
                   collect(DISTINCT prerequisite.name) as prerequisites
            """
            
            result = session.run(cypher, concept=concept_name)
            record = result.single()
            
            if record:
                return {
                    "concept": record["concept"],
                    "requires": [r for r in record["requires"] if r],
                    "related": [r for r in record["related"] if r],
                    "contrasts": [r for r in record["contrasts"] if r],
                    "prerequisites": [r for r in record["prerequisites"] if r]
                }
            
            return {}
            
    except Exception as e:
        print(f"❌ Neo4j relationship query failed: {e}")
        return {}
    finally:
        if drv:
            drv.close()

# ---------------------------- Re-rank (LLM-as-judge, optional) ------------------

def rerank_with_llm(question: str, items: List[Dict], top_k: int = 5) -> List[Dict]:
    """Send brief snippets to LLM asking for best ordering. Fallback to score sort if OpenAI not set."""
    if not USE_OPENAI or not oai or not items:
        return items[:top_k]
    # Build a compact list: index + title + 1-2 lines of text
    lines = []
    for i, it in enumerate(items[:12], 1):
        snippet = (it.get("text","") or "")[:200].replace("\n"," ")
        title = it.get("title") or it.get("doc_id", f"doc{i}")
        lines.append(f"{i}. {title}: {snippet}")
    prompt = (
        "You are ranking context passages for answering a question. "
        "Return a JSON array of the top 5 indices in best-to-worst order.\n\n"
        f"Question: {question}\nPassages:\n" + "\n".join(lines)
    )
    try:
        r = oai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role":"system","content":"Return only valid JSON like [3,1,5,2,4]."},
                {"role":"user","content":prompt}
            ]
        )
        import json
        arr = json.loads(r.choices[0].message.content.strip())
        # map chosen indices (1-based) back to items
        ranked = []
        for idx in arr:
            if 1 <= idx <= len(items[:12]):
                ranked.append(items[idx-1])
        # pad if fewer than top_k
        ranked = ranked[:top_k]
        if len(ranked) < top_k:
            # fill from remaining by score
            rest = [x for x in items if x not in ranked]
            rest.sort(key=lambda r: r.get("score", 0), reverse=True)
            ranked += rest[: (top_k - len(ranked))]
        return ranked
    except Exception:
        return items[:top_k]

# ---------------------------- Prompt builder & LLM call -------------------------

def build_prompt(audience: str, question: str, contexts: List[Dict], next_concepts: List[str]) -> str:
    citations = []
    parts = []
    for c in contexts[:3]:
        title = c.get("title") or c.get("doc_id","")
        url = c.get("source_url","")
        citations.append(f"- {title} | {url}".strip())
        parts.append(c.get("text","") or "")
    ctx_text = "\n\n---\n\n".join(parts)

    return (
        f"System: You are a kind ML tutor for a {audience}. "
        "Use plain words, short sentences, no equations unless asked. Be accurate and safe.\n\n"
        f"Context (use to answer):\n{ctx_text}\n\n"
        f"User question: {question}\n\n"
        "Write the answer with this structure:\n"
        "1) Simple explanation (≤3 short sentences)\n"
        "2) Analogy (1–2 sentences)\n"
        "3) Real-life example (1 sentence)\n"
        "4) Visual idea (start with 'Image: ...')\n"
        "5) Next concepts (2 bullets) — you may use the provided list\n\n"
        f"Suggested next concepts: {', '.join(next_concepts) if next_concepts else 'None'}\n"
        "Keep it under 180 words."
    )

def generate_answer(prompt: str) -> str:
    if not USE_OPENAI or not oai:
        # Safe fallback for dev
        return "This is a placeholder answer (connect OpenAI to generate real text)."
    r = oai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role":"user","content":prompt}]
    )
    return (r.choices[0].message.content or "").strip()

# -------------------------------- Supabase helpers ------------------------------

def supabase_headers():
    """Get headers for Supabase API calls"""
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    }

async def supabase_insert_star(user_id: str, doc_id: str, note: Optional[str]) -> None:
    """Save a starred item for a user"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("⚠️ Supabase not configured")
        return
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # First check if star already exists
            check_url = f"{SUPABASE_URL}/rest/v1/user_stars"
            check_params = {
                "user_id": f"eq.{user_id}",
                "doc_id": f"eq.{doc_id}",
                "select": "id"
            }
            
            check_response = await client.get(check_url, headers=supabase_headers(), params=check_params)
            existing = check_response.json()
            
            if existing:
                # Update existing star
                update_url = f"{SUPABASE_URL}/rest/v1/user_stars"
                update_params = {
                    "user_id": f"eq.{user_id}",
                    "doc_id": f"eq.{doc_id}"
                }
                payload = {"note": note, "updated_at": "now()"}
                
                await client.patch(update_url, headers=supabase_headers(), json=payload, params=update_params)
            else:
                # Insert new star
                payload = {
                    "user_id": user_id,
                    "doc_id": doc_id,
                    "note": note,
                    "created_at": "now()"
                }
                
                await client.post(check_url, headers=supabase_headers(), json=payload, params={"return": "minimal"})
                
    except Exception as e:
        print(f"❌ Supabase insert star failed: {e}")

async def supabase_select_stars(user_id: str) -> List[StarRecord]:
    """Get all starred items for a user"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return []
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{SUPABASE_URL}/rest/v1/user_stars"
            params = {
                "user_id": f"eq.{user_id}",
                "select": "doc_id,note,created_at",
                "order": "created_at.desc"
            }
            
            response = await client.get(url, headers=supabase_headers(), params=params)
            response.raise_for_status()
            
            return [StarRecord(**row) for row in response.json()]
            
    except Exception as e:
        print(f"❌ Supabase select stars failed: {e}")
        return []

# --------------------------------- Endpoints ------------------------------------

@app.post("/query", response_model=QueryResponse)
def query_api(req: QueryRequest):
    """Main query endpoint implementing your requirements"""
    t0 = time.time()

    # 1) Guardrail: ML-only intent gate + moderation
    allowed, reason = guardrail_ml_only(req.question)
    if not allowed:
        raise HTTPException(status_code=400, detail=f"Out of scope: {reason}")

    # 2) Intent router
    intent = classify_intent(req.question)

    # 3) Connect to databases
    if not connect_milvus():
        raise HTTPException(status_code=503, detail="Vector database connection failed")

    # 4) Retrieval based on intent
    if intent in ["explain", "define"]:
        # Milvus only - prioritize rich education content
        hits = milvus_search(COLL_RICH_EDUCATION, req.question, top_k=req.top_k)
        if len(hits) < req.top_k // 2:
            # Supplement with YouTube content if needed
            hits += milvus_search(COLL_YOUTUBE_VIDEOS, req.question, top_k=req.top_k // 3)
    else:
        # Milvus + Neo4j for compare/related/next
        hits = merged_search(req.question, top_k=req.top_k)

    if not hits:
        raise HTTPException(status_code=404, detail="No results found in vector search")

    # 5) Diverse retrieval (MMR) - keep metadata
    mmr_hits = mmr_select(hits, k=min(8, req.top_k))

    # 6) Graph context for compare/related/next intents (≤3 hops)
    next_concepts = []
    if req.use_graph and intent in {"compare", "related", "next"}:
        next_concepts = graph_next_concepts(req.question, limit=3)
        
        # For compare queries, get detailed relationships
        if intent == "compare":
            relationships = get_concept_relationships(req.question)
            if relationships:
                next_concepts.extend(relationships.get("related", [])[:2])

    # 7) Re-rank: LLM-as-judge returning top-5
    final_ctx = rerank_with_llm(req.question, mmr_hits, top_k=5)

    # 8) Compose structured prompt (audience=child; sections: explanation, analogy, example, visual idea, next concepts)
    prompt = build_prompt(req.audience, req.question, final_ctx, next_concepts)
    answer = generate_answer(prompt)

    # 9) Build citations with stable JSON shape (at least 2 citations)
    citations = []
    for item in final_ctx:
        citations.append(Citation(
            doc_id=item.get("doc_id", ""),
            title=item.get("title", ""),
            source=item.get("source", ""),
            source_url=item.get("source_url", ""),
            kind=item.get("kind", ""),
            score=round(item.get("score", 0.0), 3)
        ))

    # Ensure at least 2 citations
    if len(citations) < 2 and len(hits) >= 2:
        for item in hits[:2]:
            if item.get("doc_id") not in [c.doc_id for c in citations]:
                citations.append(Citation(
                    doc_id=item.get("doc_id", ""),
                    title=item.get("title", ""),
                    source=item.get("source", ""),
                    source_url=item.get("source_url", ""),
                    kind=item.get("kind", ""),
                    score=round(item.get("score", 0.0), 3)
                ))

    # 10) Include next_concepts for compare/related queries
    if intent not in {"compare", "related", "next"}:
        next_concepts = []

    latency_ms = int((time.time() - t0) * 1000)
    
    return QueryResponse(
        answer=answer,
        citations=citations[:5],  # Return top 5 citations max
        next_concepts=next_concepts,
        intent=intent,
        latency_ms=latency_ms
    )

@app.post("/star")
async def star_api(req: StarRequest):
    if not req.user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    if not req.doc_id:
        raise HTTPException(status_code=400, detail="doc_id required")
    await supabase_insert_star(req.user_id, req.doc_id, req.note)
    return {"ok": True}

@app.get("/stars", response_model=List[StarRecord])
async def stars_api(user_id: str = Query(..., description="Supabase user id")):
    return await supabase_select_stars(user_id)

@app.get("/next")
def next_api(concept: str = Query(..., description="Concept or query text"), limit: int = 3):
    """Get suggested learning path from Neo4j (2-3 nodes)"""
    next_concepts = graph_next_concepts(concept, limit=limit)
    relationships = get_concept_relationships(concept)
    
    # Combine suggested next concepts with relationship data
    response = {
        "concept": concept,
        "next_concepts": next_concepts,
        "relationships": relationships if relationships else {},
        "learning_path": []
    }
    
    # Build a simple learning path if relationships exist
    if relationships:
        path = []
        
        # Add prerequisites first
        if relationships.get("prerequisites"):
            path.extend([f"📚 Review: {p}" for p in relationships["prerequisites"][:2]])
        
        # Add current concept
        path.append(f"📖 Current: {relationships.get('concept', concept)}")
        
        # Add what this concept requires
        if relationships.get("requires"):
            path.extend([f"🎯 Next: {r}" for r in relationships["requires"][:2]])
        
        # Add related concepts for broader understanding
        if relationships.get("related"):
            path.extend([f"🔗 Related: {r}" for r in relationships["related"][:1]])
        
        response["learning_path"] = path
    
    return response

#!/usr/bin/env python3
"""
Unified AI/ML Educational Platform
Combines authentication with advanced RAG backend pipeline
"""

import os
import time
import math
import httpx
from typing import List, Literal, Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request, Depends, status, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import existing authentication modules
from auth_models import UserRegistration, UserLogin, UserProfile
from auth_service import AuthService

# Import database clients
from pymilvus import connections, Collection
from neo4j import GraphDatabase
from openai import OpenAI

# Load environment variables and configure SSL
load_dotenv()
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")  # Fixed: using correct env var name
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Collection names
COLL_RICH_EDUCATION = "rich_ml_education"
COLL_YOUTUBE_VIDEOS = "youtube_creator_videos"

# Initialize clients
oai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting AI/ML Educational Platform")
    
    # Test connections
    milvus_status = connect_milvus()
    if milvus_status:
        print("✅ Milvus connection established")
    else:
        print("⚠️ Milvus connection failed - app will run with fallback responses")
    
    if test_neo4j_connection():
        print("✅ Neo4j connection established")
    else:
        print("⚠️ Neo4j connection failed")
    
    if oai:
        print("✅ OpenAI client initialized")
    else:
        print("⚠️ OpenAI client not configured")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down AI/ML Educational Platform")

# Create FastAPI app
app = FastAPI(
    title="AI/ML Educational Platform",
    description="Advanced RAG-powered AI tutoring with user authentication",
    version="2.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize authentication service
auth_service = AuthService()

# ================================= DATA MODELS =================================

# RAG Models
Intent = Literal["explain", "define", "compare", "related", "next", "blocked", "fallback"]

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []
    audience: Literal["kid", "teen", "adult"] = "kid"
    use_graph: bool = True

class Citation(BaseModel):
    doc_id: str
    title: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    kind: Optional[str] = None
    score: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    next_concepts: List[str] = []
    intent: Intent
    latency_ms: int

class StarRequest(BaseModel):
    doc_id: str
    note: Optional[str] = None

class StarRecord(BaseModel):
    doc_id: str
    note: Optional[str] = None
    created_at: Optional[str] = None

# ================================= UTILITIES =================================

def connect_milvus() -> bool:
    """Connect to Zilliz Cloud"""
    try:
        if not MILVUS_URI or not MILVUS_TOKEN:
            print("❌ MILVUS_URI or MILVUS_TOKEN not configured in environment")
            return False
        
        print(f"🔗 Attempting to connect to Milvus at: {MILVUS_URI[:50]}...")
        
        # Disconnect any existing connections first
        try:
            connections.disconnect("default")
        except:
            pass
        
        connections.connect(
            alias="default",
            uri=MILVUS_URI,
            token=MILVUS_TOKEN
        )
        
        # Test the connection by listing collections
        from pymilvus import utility
        collections = utility.list_collections()
        print(f"✅ Milvus connected successfully. Collections: {len(collections)}")
        return True
        
    except Exception as e:
        print(f"❌ Milvus connection failed: {e}")
        print(f"   URI: {MILVUS_URI[:50] if MILVUS_URI else 'Not set'}...")
        print(f"   Token: {'Set' if MILVUS_TOKEN else 'Not set'}")
        return False

def test_neo4j_connection() -> bool:
    """Test Neo4j Aura connection"""
    try:
        if not NEO4J_URI or not NEO4J_PASSWORD:
            return False
        
        # Use bolt+s for direct connection
        uri = NEO4J_URI
        if uri.startswith("neo4j+s://"):
            uri = uri.replace("neo4j+s://", "bolt+s://")
        
        driver = GraphDatabase.driver(uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

# Old guardrail function removed - now using advanced LLM-based guardrails from run_gaurdrails.py

def classify_intent(text: str) -> Intent:
    """Classify user intent"""
    t = text.lower()
    if any(x in t for x in ["compare", "difference", "vs", "versus", "contrast"]):
        return "compare"
    if any(x in t for x in ["related", "relation", "how is x related", "connection"]):
        return "related"
    if any(x in t for x in ["what next", "what should i learn next", "next after", "prereq", "prerequisite"]):
        return "next"
    if any(x in t for x in ["define", "definition", "meaning of"]):
        return "define"
    return "explain"

def generate_query_embedding(query: str) -> List[float]:
    """Generate embedding for search query"""
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
    """Search Milvus collection"""
    try:
        query_embedding = generate_query_embedding(query)
        if not query_embedding:
            return []
        
        collection = Collection(collection_name)
        collection.load()
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        if collection_name == COLL_RICH_EDUCATION:
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["id", "concept_slug", "concept_title", "slice", "text", "tags"]
            )
        else:
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["doc_id", "title", "source_url", "source", "kind", "text", "tags"]
            )
        
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

def neo4j_query_next_concepts(concept_or_query: str, limit: int = 3) -> List[str]:
    """Get next concepts from Neo4j knowledge graph"""
    try:
        if not NEO4J_URI or not NEO4J_PASSWORD:
            return []
        
        uri = NEO4J_URI
        if uri.startswith("neo4j+s://"):
            uri = uri.replace("neo4j+s://", "bolt+s://")
        
        driver = GraphDatabase.driver(uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        with driver.session() as session:
            # Try direct concept match
            cypher = """
            MATCH (c:Concept)-[:REQUIRES|RELATES_TO|CONTRASTS_WITH]->(n:Concept)
            WHERE toLower(c.name) CONTAINS toLower($q) OR toLower(c.slug) CONTAINS toLower($q)
            RETURN DISTINCT n.name AS name
            LIMIT $lim
            """
            
            result = session.run(cypher, q=concept_or_query, lim=limit)
            concepts = [record["name"] for record in result]
            
            # If no matches, try video connections
            if not concepts:
                cypher2 = """
                MATCH (v:Video)-[:COVERS]->(c:Concept)-[:REQUIRES|RELATES_TO]->(n:Concept)
                WHERE toLower(v.title) CONTAINS toLower($q)
                RETURN DISTINCT n.name AS name
                LIMIT $lim
                """
                
                result = session.run(cypher2, q=concept_or_query, lim=limit)
                concepts = [record["name"] for record in result]
        
        driver.close()
        return concepts
        
    except Exception as e:
        print(f"❌ Neo4j query failed: {e}")
        return []

def rerank_with_llm(question: str, items: List[Dict], top_k: int = 5) -> List[Dict]:
    """Re-rank results using LLM"""
    if not oai or not items:
        return items[:top_k]
    
    try:
        lines = []
        for i, item in enumerate(items[:12], 1):
            snippet = (item.get("text", "") or "")[:200].replace("\n", " ")
            title = item.get("title") or item.get("doc_id", f"doc{i}")
            lines.append(f"{i}. {title}: {snippet}")
        
        prompt = (
            "You are ranking context passages for answering a question. "
            "Return a JSON array of the top 5 indices in best-to-worst order.\n\n"
            f"Question: {question}\nPassages:\n" + "\n".join(lines)
        )
        
        response = oai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": "Return only valid JSON like [3,1,5,2,4]."},
                {"role": "user", "content": prompt}
            ]
        )
        
        import json
        indices = json.loads(response.choices[0].message.content.strip())
        
        ranked = []
        for idx in indices:
            if 1 <= idx <= len(items[:12]):
                ranked.append(items[idx-1])
        
        # Fill remaining slots
        if len(ranked) < top_k:
            rest = [x for x in items if x not in ranked]
            rest.sort(key=lambda r: r.get("score", 0), reverse=True)
            ranked += rest[:(top_k - len(ranked))]
        
        return ranked[:top_k]
        
    except Exception as e:
        print(f"❌ Reranking failed: {e}")
        return items[:top_k]

def build_prompt(audience: str, question: str, contexts: List[Dict], next_concepts: List[str]) -> str:
    """Build structured prompt for LLM"""
    parts = []
    for ctx in contexts[:3]:
        parts.append(ctx.get("text", "") or "")
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
    """Generate answer using OpenAI"""
    if not oai:
        return "I'm sorry, but I'm having trouble processing your request right now."
    
    try:
        response = oai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"❌ Answer generation failed: {e}")
        return "I apologize, but I'm having trouble generating a response right now."

# ================================= AUTHENTICATION =================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """Get current authenticated user"""
    try:
        payload = auth_service.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user_profile = await auth_service.get_user_profile(payload["sub"])
        if not user_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user_profile
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

async def get_current_user_optional(request: Request) -> Optional[UserProfile]:
    """Get current user if authenticated, otherwise None"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = auth_service.verify_token(token)
        if not payload:
            return None
        
        return await auth_service.get_user_profile(payload["sub"])
    except:
        return None

# ================================= SUPABASE HELPERS =================================

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
        return
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{SUPABASE_URL}/rest/v1/user_stars"
            
            # Check if exists
            check_params = {"user_id": f"eq.{user_id}", "doc_id": f"eq.{doc_id}", "select": "id"}
            check_response = await client.get(url, headers=supabase_headers(), params=check_params)
            existing = check_response.json()
            
            if existing:
                # Update existing
                update_params = {"user_id": f"eq.{user_id}", "doc_id": f"eq.{doc_id}"}
                payload = {"note": note, "updated_at": "now()"}
                await client.patch(url, headers=supabase_headers(), json=payload, params=update_params)
            else:
                # Insert new
                payload = {"user_id": user_id, "doc_id": doc_id, "note": note, "created_at": "now()"}
                await client.post(url, headers=supabase_headers(), json=payload, params={"return": "minimal"})
                
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

# ================================= WEB ROUTES =================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard - authentication handled by JavaScript"""
    # Don't check authentication server-side for initial page load
    # Let JavaScript handle the authentication check and redirect if needed
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": None,  # Will be loaded by JavaScript
        "title": "AI/ML Learning Dashboard"
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request):
    """Redirect /dashboard to / for backward compatibility"""
    return RedirectResponse(url="/", status_code=302)

# ================================= API ROUTES =================================

@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
        result = await auth_service.register_user(user_data)
        return {"message": "User registered successfully", "user_id": result["user_id"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login_user(credentials: UserLogin):
    """Login user"""
    try:
        # Get user data from auth service
        user_data = await auth_service.authenticate_user(credentials.email, credentials.password)
        if user_data:
            # Create access token
            access_token = auth_service.create_access_token(data={"sub": user_data["id"]})
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/profile")
async def get_profile(current_user: UserProfile = Depends(get_current_user)):
    """Get user profile"""
    return current_user

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: UserProfile = Depends(get_current_user)):
    """Advanced RAG chat endpoint with comprehensive data tracking"""
    t0 = time.time()
    
    # 📊 TRACKING: Log the incoming query
    print(f"\n{'='*60}")
    print(f"🔍 USER QUERY RECEIVED:")
    print(f"   User: {current_user.username} (ID: {current_user.id})")
    print(f"   Query: {request.message}")
    print(f"   Age Group: {current_user.age_group}")
    print(f"   Study Level: {current_user.study_level}")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    # 1) Advanced Guardrails
    from run_gaurdrails import run_guardrails
    
    print(f"   🛡️ Running comprehensive guardrails...")
    guardrail_result = await run_guardrails(
        request.message,
        use_llm_scope=True,
        use_moderation=True
    )
    
    if guardrail_result["allowed"] == False:
        reason = guardrail_result["reason"]
        latency = guardrail_result.get("latency_ms", 0)
        total_latency = int((time.time() - t0) * 1000)
        print(f"   ❌ GUARDRAIL: Query blocked - {reason} (latency: {latency}ms)")
        
        # Return a friendly chat response instead of HTTP error
        return ChatResponse(
            answer=reason,
            citations=[],
            next_concepts=[],
            intent="blocked",
            latency_ms=total_latency
        )
    
    elif guardrail_result["allowed"] == "fallback_llm":
        # Use fallback LLM with strict ML-only system prompt
        from run_gaurdrails import fallback_ml_response
        
        reason = guardrail_result["reason"]
        latency = guardrail_result.get("latency_ms", 0)
        print(f"   🔄 GUARDRAIL: Using fallback LLM - {reason} (latency: {latency}ms)")
        
        # Generate response using fallback LLM
        fallback_answer = fallback_ml_response(request.message, current_user.age_group)
        total_latency = int((time.time() - t0) * 1000)
        
        print(f"   ✅ FALLBACK: Generated {len(fallback_answer)} character response (total latency: {total_latency}ms)")
        
        return ChatResponse(
            answer=fallback_answer,
            citations=[],
            next_concepts=[],
            intent="fallback",
            latency_ms=total_latency
        )
    
    guardrail_latency = guardrail_result.get("latency_ms", 0)
    print(f"   ✅ GUARDRAIL: Query allowed - {guardrail_result['reason']} (latency: {guardrail_latency}ms)")
    
    # 2) Intent classification
    intent = classify_intent(request.message)
    print(f"   🎯 INTENT: {intent}")
    
    # 3) Connect to databases
    if not connect_milvus():
        # Provide a helpful fallback response without RAG
        fallback_answers = {
            "explain": f"I'd be happy to explain {request.message}, but I'm currently unable to access my knowledge base. This usually means my vector database is temporarily unavailable. You can try: 1) Asking again in a few minutes, 2) Checking if this is a basic ML concept I can answer from general knowledge, or 3) Contacting support.",
            "define": f"I'd like to define that for you, but my knowledge base is currently offline. This is typically a temporary issue with the vector database connection.",
            "compare": f"Comparing concepts requires access to my knowledge base, which is currently unavailable. Please try again shortly.",
            "related": f"I need my knowledge graph to find related concepts, but it's currently offline. Please check back in a few minutes.",
            "next": f"To suggest what to learn next, I need access to my learning path database, which is currently unavailable."
        }
        
        return ChatResponse(
            answer=fallback_answers.get(intent, "I'm currently unable to access my knowledge base. Please try again in a moment."),
            citations=[],
            next_concepts=[],
            intent=intent,
            latency_ms=int((time.time() - t0) * 1000)
        )
    
    # 4) Retrieval based on intent
    print(f"\n📚 DATA RETRIEVAL:")
    if intent in ["explain", "define"]:
        # Milvus only - prioritize rich education content
        print(f"   🔍 Searching rich_ml_education collection...")
        hits = milvus_search(COLL_RICH_EDUCATION, request.message, top_k=12)
        print(f"   📊 Retrieved {len(hits)} results from rich_ml_education")
        
        if len(hits) < 6:
            print(f"   🔍 Supplementing with youtube_creator_videos...")
            youtube_hits = milvus_search(COLL_YOUTUBE_VIDEOS, request.message, top_k=6)
            print(f"   📊 Retrieved {len(youtube_hits)} results from youtube_creator_videos")
            hits += youtube_hits
    else:
        # Combined search for compare/related/next
        print(f"   🔍 Combined search across both collections...")
        rich_hits = milvus_search(COLL_RICH_EDUCATION, request.message, top_k=8)
        youtube_hits = milvus_search(COLL_YOUTUBE_VIDEOS, request.message, top_k=4)
        print(f"   📊 Rich education: {len(rich_hits)} results")
        print(f"   📊 YouTube videos: {len(youtube_hits)} results")
        hits = rich_hits + youtube_hits
    
    print(f"   📈 TOTAL RETRIEVED: {len(hits)} documents")
    
    if not hits:
        print(f"   ❌ No results found for query")
        raise HTTPException(status_code=404, detail="No results found")
    
    # 📊 TRACKING: Log top retrieved concepts
    print(f"\n🎯 TOP RETRIEVED CONCEPTS:")
    for i, hit in enumerate(hits[:5], 1):
        source = hit.get('source', 'unknown')
        title = hit.get('title', 'No title')[:50]
        score = hit.get('score', 0)
        doc_id = hit.get('doc_id', 'unknown')
        print(f"   {i}. [{source}] {title}... (score: {score:.3f}, id: {doc_id})")
    
    # 5) Graph context for compare/related/next intents
    next_concepts = []
    if request.use_graph and intent in {"compare", "related", "next"}:
        print(f"\n🌐 NEO4J KNOWLEDGE GRAPH:")
        print(f"   🔍 Querying for related concepts...")
        next_concepts = neo4j_query_next_concepts(request.message, limit=3)
        print(f"   📊 Found {len(next_concepts)} related concepts: {[c.get('name', 'Unknown') for c in next_concepts]}")
    else:
        print(f"\n🌐 NEO4J: Skipped (intent: {intent}, use_graph: {request.use_graph})")
    
    # 6) Re-rank using LLM
    print(f"\n🔄 RE-RANKING:")
    print(f"   📊 Re-ranking {len(hits)} results to top 5...")
    final_contexts = rerank_with_llm(request.message, hits, top_k=5)
    print(f"   ✅ Final selection: {len(final_contexts)} contexts")
    
    # 📊 TRACKING: Log final selected contexts
    print(f"\n🎯 FINAL SELECTED CONTEXTS:")
    for i, ctx in enumerate(final_contexts, 1):
        source = ctx.get('source', 'unknown')
        title = ctx.get('title', 'No title')[:40]
        doc_id = ctx.get('doc_id', 'unknown')
        print(f"   {i}. [{source}] {title}... (id: {doc_id})")
    
    # 7) Generate structured response
    print(f"\n💭 RESPONSE GENERATION:")
    print(f"   🎯 Audience: {request.audience}")
    print(f"   📝 Building structured prompt...")
    prompt = build_prompt(request.audience, request.message, final_contexts, next_concepts)
    print(f"   🤖 Generating answer with GPT...")
    answer = generate_answer(prompt)
    print(f"   ✅ Generated {len(answer)} character response")
    
    # 8) Build citations
    citations = []
    for item in final_contexts:
        citations.append(Citation(
            doc_id=item.get("doc_id", ""),
            title=item.get("title", ""),
            source=item.get("source", ""),
            source_url=item.get("source_url", ""),
            kind=item.get("kind", ""),
            score=round(item.get("score", 0.0), 3)
        ))
    
    latency_ms = int((time.time() - t0) * 1000)
    
    # 📊 TRACKING: Final response summary
    print(f"\n📋 RESPONSE SUMMARY:")
    print(f"   📝 Answer length: {len(answer)} characters")
    print(f"   📚 Citations provided: {len(citations)}")
    print(f"   🔗 Next concepts: {len(next_concepts)}")
    print(f"   ⏱️ Total latency: {latency_ms}ms")
    print(f"   💡 Intent processed: {intent}")
    print(f"{'='*60}\n")
    
    return ChatResponse(
        answer=answer,
        citations=citations,
        next_concepts=next_concepts,
        intent=intent,
        latency_ms=latency_ms
    )

@app.post("/api/star")
async def star_content(request: StarRequest, current_user: UserProfile = Depends(get_current_user)):
    """Star/bookmark content"""
    await supabase_insert_star(current_user.id, request.doc_id, request.note)
    return {"message": "Content starred successfully"}

@app.get("/api/stars", response_model=List[StarRecord])
async def get_stars(current_user: UserProfile = Depends(get_current_user)):
    """Get user's starred content"""
    return await supabase_select_stars(current_user.id)

@app.get("/api/next")
async def get_next_concepts(concept: str = Query(...), limit: int = 3):
    """Get next learning concepts"""
    next_concepts = neo4j_query_next_concepts(concept, limit)
    return {"concept": concept, "next_concepts": next_concepts}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "milvus": connect_milvus(),
        "neo4j": test_neo4j_connection(),
        "openai": oai is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

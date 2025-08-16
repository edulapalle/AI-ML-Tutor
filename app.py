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

# Import agentic learning system
from agentic_learning_system import AgenticLearningSystem
from email_service import get_email_service

# Import abuse protection system
from protection_middleware import validate_chat_message

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

# Initialize agentic learning system
agentic_system = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global agentic_system
    
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
    
    # Initialize agentic learning system
    try:
        agentic_system = AgenticLearningSystem()
        print("🤖 Agentic Learning System initialized")
    except Exception as e:
        print(f"⚠️ Agentic Learning System failed to initialize: {e}")
        agentic_system = None
    
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

# In-memory quiz storage (in production, use Redis or database)
quiz_sessions: Dict[str, Any] = {}

# ================================= DATA MODELS =================================

# RAG Models
Intent = Literal["explain", "define", "compare", "related", "next", "examples", "quiz", "blocked", "fallback"]

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []
    audience: Literal["kid", "teen", "adult"] = "kid"
    use_graph: bool = True

# Quiz Models
class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: int  # Index of correct option
    explanation: str
    topic: str
    difficulty: Literal["beginner", "intermediate", "advanced"]

class QuizSession(BaseModel):
    session_id: str
    user_id: str
    topic: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    questions: List[QuizQuestion]
    current_question: int = 0
    score: int = 0
    answers: List[int] = []  # User's answers
    started_at: datetime
    completed_at: Optional[datetime] = None

class QuizRequest(BaseModel):
    topic: str
    difficulty: Literal["beginner", "intermediate", "advanced"] = "beginner"
    num_questions: int = Field(default=5, ge=1, le=10)

class QuizAnswer(BaseModel):
    session_id: str
    answer: int  # Index of selected option

class QuizResponse(BaseModel):
    session_id: str
    question: QuizQuestion
    is_correct: Optional[bool] = None
    feedback: Optional[str] = None
    score: int
    progress: str  # e.g., "3/5"
    completed: bool = False

class QuizResult(BaseModel):
    session_id: str
    topic: str
    final_score: int
    total_questions: int
    percentage: float
    feedback: str
    recommendations: List[str]

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
    """Enhanced intent classification for educational interactions"""
    t = text.lower()
    
    # Question patterns with more specific detection
    if any(x in t for x in ["compare", "difference", "vs", "versus", "contrast", "better than", "which is"]):
        return "compare"
    
    if any(x in t for x in ["related", "relation", "how is x related", "connection", "connects to", "builds on"]):
        return "related"
    
    if any(x in t for x in ["what next", "what should i learn next", "next after", "prereq", "prerequisite", 
                           "after learning", "what comes after", "learning path", "roadmap"]):
        return "next"
    
    # More specific definition patterns
    if any(x in t for x in ["define", "definition", "meaning of", "what is", "what are", "what does", 
                           "tell me about"]) and len(t.split()) <= 6:  # Short definition requests
        return "define"
    
    # Example-focused requests - New intent type
    if any(x in t for x in ["example", "examples", "show me", "demonstrate", "illustrate", "instance"]):
        return "examples"
    
    # Quiz/test requests - New intent type  
    if any(x in t for x in ["quiz", "test", "question", "check my understanding", "practice"]):
        return "quiz"
    
    # Default to explain for comprehensive coverage
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

def extract_topic_from_question(question: str) -> str:
    """Extract main topic from user's question using simple keyword matching"""
    import re
    
    # Common ML/AI topics and patterns
    ml_topics = {
        'machine learning': ['machine learning', 'ml'],
        'deep learning': ['deep learning', 'neural network', 'neural net'],
        'natural language processing': ['nlp', 'natural language', 'text processing'],
        'computer vision': ['computer vision', 'image recognition', 'cv'],
        'reinforcement learning': ['reinforcement learning', 'rl'],
        'supervised learning': ['supervised learning', 'classification', 'regression'],
        'unsupervised learning': ['unsupervised learning', 'clustering', 'dimensionality reduction'],
        'neural networks': ['neural network', 'neuron', 'activation function'],
        'convolutional neural networks': ['cnn', 'convolutional', 'convolution'],
        'recurrent neural networks': ['rnn', 'lstm', 'gru', 'recurrent'],
        'transformers': ['transformer', 'attention', 'bert', 'gpt'],
        'gradient descent': ['gradient descent', 'optimization', 'backpropagation'],
        'overfitting': ['overfitting', 'underfitting', 'regularization'],
        'data preprocessing': ['preprocessing', 'data cleaning', 'feature engineering'],
        'model evaluation': ['evaluation', 'accuracy', 'precision', 'recall', 'f1'],
        'cross validation': ['cross validation', 'validation', 'train test split'],
        'ensemble methods': ['ensemble', 'random forest', 'bagging', 'boosting'],
        'support vector machines': ['svm', 'support vector'],
        'decision trees': ['decision tree', 'random forest'],
        'linear regression': ['linear regression', 'logistic regression'],
        'clustering': ['clustering', 'kmeans', 'hierarchical'],
        'pca': ['pca', 'principal component']
    }
    
    question_lower = question.lower()
    
    # Find matching topics
    for topic, keywords in ml_topics.items():
        for keyword in keywords:
            if keyword in question_lower:
                return topic
    
    # If no specific match, try to extract general concepts
    tech_words = re.findall(r'\b(?:algorithm|model|training|prediction|data|learning|neural|network|deep|machine|ai|artificial|intelligence)\b', question_lower)
    if tech_words:
        return ' '.join(tech_words[:2])  # Take first 2 technical words
    
    # Fallback: if question contains "what is" or similar, extract the main concept
    what_patterns = [
        r'what is (\w+(?:\s+\w+)*)',
        r'tell me about (\w+(?:\s+\w+)*)',
        r'explain (\w+(?:\s+\w+)*)',
        r'how does (\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*) work'
    ]
    
    for pattern in what_patterns:
        match = re.search(pattern, question_lower)
        if match:
            concept = match.group(1).strip()
            # Only return if it's likely to be ML-related
            if any(word in concept for word in ['learning', 'network', 'algorithm', 'model', 'data', 'ai', 'intelligence']):
                return concept
    
    # Last resort: if question has ML keywords, return a generic topic
    if any(keyword in question_lower for keyword in ['learn', 'model', 'algorithm', 'data', 'ai', 'ml']):
        return 'machine learning'
    
    return None

async def store_user_topic(user_id: str, topic: str):
    """Store a topic in user's learning path"""
    try:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            print(f"   ❌ Supabase config missing")
            return
        
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{SUPABASE_URL}/rest/v1/user_learning_path"
            headers = supabase_headers()
            
            # Check if topic already exists for this user
            check_params = {"user_id": f"eq.{user_id}", "topic": f"eq.{topic}", "select": "id"}
            check_response = await client.get(url, headers=headers, params=check_params)
            
            if check_response.status_code == 200 and check_response.json():
                # Update existing topic timestamp
                update_params = {"user_id": f"eq.{user_id}", "topic": f"eq.{topic}"}
                payload = {"explored_at": "now()"}
                await client.patch(url, headers=headers, json=payload, params=update_params)
                print(f"   🔄 Updated existing topic timestamp: {topic}")
            elif check_response.status_code == 404:
                print(f"   📝 Table doesn't exist - learning path storage disabled for now")
                return
            else:
                # Insert new topic
                payload = {"user_id": user_id, "topic": topic, "explored_at": "now()"}
                insert_response = await client.post(url, headers=headers, json=payload)
                if insert_response.status_code in [200, 201]:
                    print(f"   ✅ Added new topic to learning path: {topic}")
                elif insert_response.status_code == 404:
                    print(f"   📝 Table doesn't exist - learning path storage disabled for now")
                else:
                    print(f"   ❌ Failed to insert topic: {insert_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Failed to store topic: {e}")

async def get_user_learning_path(user_id: str) -> List[str]:
    """Get user's learning path topics"""
    try:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            print(f"   ❌ Supabase config missing")
            return []
        
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{SUPABASE_URL}/rest/v1/user_learning_path"
            headers = supabase_headers()
            params = {
                "user_id": f"eq.{user_id}",
                "select": "topic",
                "order": "explored_at.desc",
                "limit": 10
            }
            
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                topics = [row["topic"] for row in data]
                print(f"   📚 Retrieved {len(topics)} topics from user's path: {topics}")
                return topics
            else:
                print(f"   ❌ Failed to get learning path: {response.status_code}")
                if response.status_code == 404:
                    print(f"   📝 Table likely doesn't exist - this is normal for new setups")
                return []
        
    except Exception as e:
        print(f"   ❌ Failed to get learning path: {e}")
        return []

def generate_next_concepts_from_path(user_topics: List[str], current_topic: str = None) -> List[str]:
    """Generate next learning concepts based on user's learning path"""
    
    # Learning progression map
    learning_map = {
        'machine learning': ['supervised learning', 'unsupervised learning', 'model evaluation'],
        'supervised learning': ['linear regression', 'decision trees', 'neural networks'],
        'unsupervised learning': ['clustering', 'pca', 'dimensionality reduction'],
        'neural networks': ['deep learning', 'convolutional neural networks', 'recurrent neural networks'],
        'deep learning': ['convolutional neural networks', 'recurrent neural networks', 'transformers'],
        'convolutional neural networks': ['computer vision', 'image recognition', 'transfer learning'],
        'recurrent neural networks': ['natural language processing', 'sequence modeling', 'lstm'],
        'transformers': ['bert', 'gpt', 'attention mechanisms'],
        'natural language processing': ['transformers', 'word embeddings', 'sentiment analysis'],
        'computer vision': ['convolutional neural networks', 'object detection', 'image segmentation'],
        'model evaluation': ['cross validation', 'overfitting', 'performance metrics'],
        'gradient descent': ['optimization', 'learning rate', 'momentum'],
        'overfitting': ['regularization', 'dropout', 'early stopping']
    }
    
    next_concepts = []
    
    # If user has a current topic, suggest natural progressions
    if current_topic and current_topic in learning_map:
        next_concepts.extend(learning_map[current_topic])
    
    # Look at user's recent topics and suggest related concepts
    for topic in user_topics[:5]:  # Last 5 topics
        if topic in learning_map:
            for concept in learning_map[topic]:
                if concept not in user_topics and concept not in next_concepts:
                    next_concepts.append(concept)
    
    # If no specific suggestions, provide foundational topics
    if not next_concepts:
        # Starter topics for new users
        if not user_topics:  # Completely new user
            foundational = [
                'machine learning basics', 
                'what is artificial intelligence', 
                'data and algorithms',
                'supervised vs unsupervised learning',
                'neural networks introduction'
            ]
        else:
            # User has some topics but no specific progressions
            foundational = ['machine learning', 'supervised learning', 'neural networks', 'model evaluation', 'data preprocessing']
        
        next_concepts = [topic for topic in foundational if topic not in user_topics]
    
    return next_concepts[:3]  # Return top 3 suggestions

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

def build_intent_based_prompt(intent: str, audience: str, question: str, contexts: List[Dict], next_concepts: List[str], conversation_history: Optional[List[Dict]] = None) -> str:
    """Build intent-aware structured prompt for LLM with educational focus"""
    
    # Extract context text
    parts = []
    for ctx in contexts[:3]:
        parts.append(ctx.get("text", "") or "")
    ctx_text = "\n\n---\n\n".join(parts)
    
    # Check if this is a quiz follow-up response
    is_quiz_response = False
    if conversation_history:
        recent_messages = conversation_history[-2:] if len(conversation_history) >= 2 else conversation_history
        for msg in recent_messages:
            if msg.get("role") == "assistant" and "quiz" in msg.get("content", "").lower():
                is_quiz_response = True
                break
    
    # Base system message
    base_system = f"You are a kind ML tutor for a {audience}. Use clear, educational language. Be accurate and safe."
    
    # Add conversation context if this is a quiz response
    conversation_context = ""
    if is_quiz_response and conversation_history:
        conversation_context = "\n\nConversation context (recent exchanges):\n"
        for msg in conversation_history[-3:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Limit context length
            conversation_context += f"{role.title()}: {content}\n"
        conversation_context += "\n"
    
    # Intent-specific prompt templates
    if intent == "explain":
        structure = (
            "Provide a comprehensive explanation with:\n"
            "1) Clear definition (2-3 sentences)\n"
            "2) Simple analogy to help understanding\n"
            "3) Practical example or use case\n"
            "4) Key points to remember (2-3 bullets)\n"
            "5) What to explore next (mention related topics)"
        )
        
    elif intent == "define":
        structure = (
            "Provide a focused definition with:\n"
            "1) Precise definition (1-2 sentences)\n"
            "2) Why this concept matters\n"
            "3) Simple example to illustrate\n"
            "4) Common misconceptions to avoid\n"
            "5) Related concepts worth learning"
        )
        
    elif intent == "compare":
        structure = (
            "Provide a clear comparison with:\n"
            "1) Brief explanation of each concept\n"
            "2) Key similarities between them\n"
            "3) Important differences\n"
            "4) When to use each one\n"
            "5) Learning path: which to study first"
        )
        
    elif intent == "related":
        structure = (
            "Show the connections with:\n"
            "1) How these concepts relate\n"
            "2) Dependencies (what builds on what)\n"
            "3) Practical scenarios where they work together\n"
            "4) Common patterns or principles\n"
            "5) Suggested learning sequence"
        )
        
    elif intent == "next":
        structure = (
            "Provide learning guidance with:\n"
            "1) Your current understanding level\n"
            "2) Logical next steps to take\n"
            "3) Prerequisites you might need\n"
            "4) Practical projects to try\n"
            "5) Resources to explore further"
        )
        
    elif intent == "examples":
        structure = (
            "Focus on practical examples with:\n"
            "1) Real-world scenario or application\n"
            "2) Step-by-step walkthrough\n"
            "3) Why this example works\n"
            "4) Variations you might encounter\n"
            "5) Try it yourself: next steps"
        )
        
    elif intent == "quiz":
        structure = (
            "I'd love to quiz you! However, I work best with interactive quizzes through the dedicated quiz feature.\n\n"
            "Here's how to get started:\n"
            "1) Look for the 'Quiz' button in the interface, or\n"
            "2) Use the quiz endpoints if you're using the API directly\n"
            "3) Choose your topic and difficulty level\n"
            "4) Get immediate feedback on each question\n\n"
            "For now, I can provide some quick study questions based on the content available, but for a full interactive quiz experience, please use the quiz feature!\n\n"
            "Quick study questions based on your topic:"
        )
        
    else:  # fallback for any other intent
        structure = (
            "Provide an educational response with:\n"
            "1) Direct answer to the question\n"
            "2) Context and background\n"
            "3) Practical examples\n"
            "4) Key takeaways\n"
            "5) Further learning opportunities"
        )
    
    # Special handling for quiz responses
    if is_quiz_response:
        quiz_instruction = "\n\nIMPORTANT: The user is responding to a quiz question. Provide feedback on their answer, explain why it's correct/incorrect, and continue the educational conversation naturally."
    else:
        quiz_instruction = ""

    return f"""{base_system}{conversation_context}
Context (use to answer):
{ctx_text}

User question: {question}

{structure}

Suggested next concepts: {', '.join(next_concepts) if next_concepts else 'Explore related ML topics'}

Keep response educational, engaging, and under 200 words. Always maintain learning focus.{quiz_instruction}"""

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

def generate_quiz_questions(topic: str, difficulty: str, num_questions: int, audience: str = "kid") -> List[QuizQuestion]:
    """Generate quiz questions using LLM and knowledge base"""
    
    # Search for relevant content from knowledge base
    if not connect_milvus():
        # Fallback to LLM-only generation
        return generate_questions_llm_only(topic, difficulty, num_questions, audience)
    
    # Get relevant educational content
    hits = milvus_search(COLL_RICH_EDUCATION, topic, top_k=10)
    
    # Extract context for question generation
    context_parts = []
    for hit in hits[:5]:  # Use top 5 most relevant
        text = hit.get('text', '')
        if text and len(text) > 50:  # Only use substantial content
            context_parts.append(text[:300])  # Limit length
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Generate questions using LLM with context
    prompt = f"""You are an educational quiz generator for {audience} learners studying AI/ML concepts.

Topic: {topic}
Difficulty: {difficulty}
Number of questions: {num_questions}

Context from knowledge base:
{context}

Generate {num_questions} multiple choice questions with exactly 4 options each.

Requirements:
1. Questions appropriate for {difficulty} level
2. Language suitable for {audience} learners
3. Exactly 4 options (A, B, C, D) per question
4. One clearly correct answer
5. Educational explanations for correct answers
6. Focus on understanding, not memorization

Format as JSON array:
[
  {{
    "id": "q1",
    "question": "What is...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "The correct answer is A because...",
    "topic": "{topic}",
    "difficulty": "{difficulty}"
  }}
]

Generate educational, engaging questions that test understanding."""
    
    try:
        response = oai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        questions_json = response.choices[0].message.content or "[]"
        
        # Extract JSON from response
        import json
        import re
        
        # Find JSON array in response
        json_match = re.search(r'\[.*\]', questions_json, re.DOTALL)
        if json_match:
            questions_data = json.loads(json_match.group())
            
            questions = []
            for i, q_data in enumerate(questions_data[:num_questions]):
                questions.append(QuizQuestion(
                    id=f"q{i+1}",
                    question=q_data.get("question", ""),
                    options=q_data.get("options", []),
                    correct_answer=q_data.get("correct_answer", 0),
                    explanation=q_data.get("explanation", ""),
                    topic=topic,
                    difficulty=difficulty
                ))
            
            return questions
        else:
            return generate_questions_llm_only(topic, difficulty, num_questions, audience)
            
    except Exception as e:
        print(f"Error generating quiz questions: {e}")
        return generate_questions_llm_only(topic, difficulty, num_questions, audience)

def generate_questions_llm_only(topic: str, difficulty: str, num_questions: int, audience: str) -> List[QuizQuestion]:
    """Fallback question generation without knowledge base"""
    
    # Create simple fallback questions based on common ML topics
    fallback_questions = {
        "machine learning": [
            {
                "question": "What is machine learning?",
                "options": ["A way to teach computers to learn", "A type of computer game", "A programming language", "A type of robot"],
                "correct_answer": 0,
                "explanation": "Machine learning is a way to teach computers to learn patterns from data without being explicitly programmed for every task."
            }
        ],
        "neural networks": [
            {
                "question": "What is a neural network inspired by?",
                "options": ["The human brain", "Computer circuits", "Mathematical equations", "Internet connections"],
                "correct_answer": 0,
                "explanation": "Neural networks are inspired by how neurons in the human brain work together to process information."
            }
        ]
    }
    
    # Return fallback questions or generate simple ones
    questions = []
    base_questions = fallback_questions.get(topic.lower(), fallback_questions["machine learning"])
    
    for i in range(min(num_questions, len(base_questions))):
        q_data = base_questions[i]
        questions.append(QuizQuestion(
            id=f"fallback_q{i+1}",
            question=q_data["question"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
            topic=topic,
            difficulty=difficulty
        ))
    
    return questions

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
    print(f"🌟 SUPABASE INSERT STAR: user_id={user_id}, doc_id={doc_id}, note={note}")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print(f"❌ SUPABASE CONFIG MISSING: URL={bool(SUPABASE_URL)}, KEY={bool(SUPABASE_ANON_KEY)}")
        return
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{SUPABASE_URL}/rest/v1/user_stars"
            headers = supabase_headers()
            print(f"🔗 SUPABASE URL: {url}")
            print(f"📤 SUPABASE HEADERS: {headers}")
            
            # Check if exists
            check_params = {"user_id": f"eq.{user_id}", "doc_id": f"eq.{doc_id}", "select": "id"}
            print(f"🔍 CHECKING EXISTING: {check_params}")
            check_response = await client.get(url, headers=headers, params=check_params)
            print(f"📥 CHECK RESPONSE: {check_response.status_code}, {check_response.text}")
            
            existing = check_response.json()
            print(f"📋 EXISTING RECORDS: {existing}")
            
            if existing:
                # Update existing
                print(f"🔄 UPDATING EXISTING STAR")
                update_params = {"user_id": f"eq.{user_id}", "doc_id": f"eq.{doc_id}"}
                payload = {"note": note}
                update_response = await client.patch(url, headers=headers, json=payload, params=update_params)
                print(f"📥 UPDATE RESPONSE: {update_response.status_code}, {update_response.text}")
            else:
                # Insert new
                print(f"➕ INSERTING NEW STAR")
                payload = {"user_id": user_id, "doc_id": doc_id, "note": note}
                print(f"📤 INSERT PAYLOAD: {payload}")
                insert_response = await client.post(url, headers=headers, json=payload)
                print(f"📥 INSERT RESPONSE: {insert_response.status_code}, {insert_response.text}")
                
    except Exception as e:
        print(f"❌ Supabase insert star failed: {e}")
        import traceback
        traceback.print_exc()

async def supabase_delete_star(user_id: str, doc_id: str) -> None:
    """Delete a starred item for a user"""
    print(f"🗑️ SUPABASE DELETE STAR: user_id={user_id}, doc_id={doc_id}")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print(f"❌ SUPABASE CONFIG MISSING: URL={bool(SUPABASE_URL)}, KEY={bool(SUPABASE_ANON_KEY)}")
        return
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{SUPABASE_URL}/rest/v1/user_stars"
            headers = supabase_headers()
            
            # Delete the record
            delete_params = {"user_id": f"eq.{user_id}", "doc_id": f"eq.{doc_id}"}
            print(f"🗑️ DELETE PARAMS: {delete_params}")
            delete_response = await client.delete(url, headers=headers, params=delete_params)
            print(f"📥 DELETE RESPONSE: {delete_response.status_code}, {delete_response.text}")
                
    except Exception as e:
        print(f"❌ Supabase delete star failed: {e}")
        import traceback
        traceback.print_exc()

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
async def chat(request: ChatRequest, fastapi_request: Request, current_user: UserProfile = Depends(get_current_user)):
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
    
    # 🛡️ ABUSE PROTECTION: Comprehensive validation before processing
    print(f"   🛡️ Running abuse protection checks...")
    protection_result = await validate_chat_message(fastapi_request, request.message, current_user.id)
    
    if not protection_result["is_valid"]:
        error_message = protection_result["error_message"]
        status_code = protection_result["status_code"]
        
        print(f"   ❌ Request blocked: {protection_result['error_type']}")
        
        # Return appropriate error based on protection result
        if status_code == 429:
            raise HTTPException(
                status_code=429, 
                detail=error_message,
                headers={"Retry-After": str(int(protection_result.get("retry_after", 60)))}
            )
        elif status_code == 403:
            raise HTTPException(status_code=403, detail=error_message)
        else:
            raise HTTPException(status_code=400, detail=error_message)
    
    print(f"   ✅ ABUSE PROTECTION: Query allowed - {protection_result.get('validation_method', 'N/A')} validation (latency: {int((time.time() - t0) * 1000)}ms)")
    
    # 1) Advanced Guardrails with conversation context (keeping existing guardrails as backup)
    from run_gaurdrails import run_guardrails
    
    print(f"   🛡️ Running comprehensive guardrails...")
    guardrail_result = await run_guardrails(
        request.message,
        conversation_history=request.conversation_history,
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
            "next": f"To suggest what to learn next, I need access to my learning path database, which is currently unavailable.",
            "examples": f"I'd love to show you examples, but I need access to my knowledge base which is currently offline. Please try again shortly.",
            "quiz": f"I'd like to create a quiz for you, but my knowledge base is currently unavailable. Please check back in a few minutes."
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
        # Milvus only - prioritize rich education content for explanations/definitions
        print(f"   🔍 Searching rich_ml_education collection...")
        rich_hits = milvus_search(COLL_RICH_EDUCATION, request.message, top_k=8)
        print(f"   📊 Retrieved {len(rich_hits)} results from rich_ml_education")
        
        print(f"   🔍 Searching youtube_creator_videos collection...")
        youtube_hits = milvus_search(COLL_YOUTUBE_VIDEOS, request.message, top_k=4)
        print(f"   📊 Retrieved {len(youtube_hits)} results from youtube_creator_videos")
        
        # Combine results (rich education first, then YouTube)
        hits = rich_hits + youtube_hits
    
    elif intent == "examples":
        # For examples, prioritize YouTube videos first for practical demonstrations
        print(f"   🔍 Searching for practical examples...")
        youtube_hits = milvus_search(COLL_YOUTUBE_VIDEOS, request.message, top_k=6)
        rich_hits = milvus_search(COLL_RICH_EDUCATION, request.message, top_k=6)
        print(f"   📊 YouTube videos: {len(youtube_hits)} results")
        print(f"   📊 Rich education: {len(rich_hits)} results")
        
        # YouTube first for examples
        hits = youtube_hits + rich_hits
    
    elif intent == "quiz":
        # For quizzes, prioritize rich educational content for structured knowledge
        print(f"   🔍 Searching for quiz-worthy content...")
        rich_hits = milvus_search(COLL_RICH_EDUCATION, request.message, top_k=10)
        youtube_hits = milvus_search(COLL_YOUTUBE_VIDEOS, request.message, top_k=2)
        print(f"   📊 Rich education: {len(rich_hits)} results")
        print(f"   📊 YouTube videos: {len(youtube_hits)} results")
        
        # Rich education first for quizzes
        hits = rich_hits + youtube_hits
        
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
    
    # 5) Dynamic Learning Path - Extract topic from user question
    print(f"\n🌱 DYNAMIC LEARNING PATH:")
    print(f"   📝 User question: '{request.message}'")
    extracted_topic = extract_topic_from_question(request.message)
    print(f"   🔍 Extracted topic: {extracted_topic}")
    
    # Store topic in user's learning path
    if extracted_topic and current_user:
        await store_user_topic(current_user.id, extracted_topic)
        print(f"   💾 Stored topic for user: {current_user.id}")
    
    # Get user's learning path for next concepts
    next_concepts = []
    if current_user:
        user_topics = await get_user_learning_path(current_user.id)
        next_concepts = generate_next_concepts_from_path(user_topics, extracted_topic)
        print(f"   📈 Generated {len(next_concepts)} next concepts from user's path")
    
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
    prompt = build_intent_based_prompt(intent, request.audience, request.message, final_contexts, next_concepts, request.conversation_history)
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
    
    # 🤖 AGENTIC BEHAVIOR: Run background analysis and interventions
    if agentic_system:
        try:
            # Background task - don't wait for completion to avoid slowing chat response
            import asyncio
            async def background_agentic_analysis():
                try:
                    print(f"🤖 Running background agentic analysis for user {current_user.id}")
                    
                    # Quick comprehension monitoring
                    chat_patterns = await agentic_system._get_user_chat_patterns(current_user.id)
                    insights = await agentic_system.comprehension_monitor.analyze_understanding_patterns(
                        current_user.id, chat_patterns[-5:]  # Just last 5 messages for speed
                    )
                    
                    # Check for autonomous interventions needed
                    if insights:
                        for insight in insights:
                            if insight.confidence > 0.7 and "adjust" in insight.action_suggestion.lower():
                                print(f"🤖 AUTONOMOUS ACTION: {insight.action_suggestion}")
                                # Log the action for admin review
                                print(f"   📊 Evidence: {insight.evidence[:2]}")
                    
                    # Quick learning path adjustment
                    learning_history = await agentic_system._get_user_learning_history(current_user.id)
                    if len(learning_history) % 5 == 0 and len(learning_history) > 0:  # Every 5th interaction
                        print(f"🤖 LEARNING PATH: Triggering path analysis after {len(learning_history)} topics")
                        # This could update next_concepts for future responses
                        
                except Exception as e:
                    print(f"⚠️ Background agentic analysis failed (non-critical): {e}")
            
            # Fire and forget - don't wait for completion
            asyncio.create_task(background_agentic_analysis())
            
        except Exception as e:
            print(f"⚠️ Failed to start agentic analysis: {e}")
    
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
    print(f"🌟 STAR REQUEST: user={current_user.username} (id={current_user.id}), doc_id={request.doc_id}, note={request.note}")
    try:
        await supabase_insert_star(current_user.id, request.doc_id, request.note)
        print(f"✅ STAR SUCCESS: Content starred for user {current_user.username}")
        return {"message": "Content starred successfully"}
    except Exception as e:
        print(f"❌ STAR FAILED: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to star content: {str(e)}")

@app.get("/api/stars", response_model=List[StarRecord])
async def get_stars(current_user: UserProfile = Depends(get_current_user)):
    """Get user's starred content"""
    return await supabase_select_stars(current_user.id)

@app.delete("/api/star/{doc_id}")
async def delete_star(doc_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Delete/unstar content"""
    print(f"🗑️ DELETE STAR REQUEST: user={current_user.username} (id={current_user.id}), doc_id={doc_id}")
    try:
        await supabase_delete_star(current_user.id, doc_id)
        print(f"✅ STAR DELETED: Content unstarred for user {current_user.username}")
        return {"message": "Content unstarred successfully"}
    except Exception as e:
        print(f"❌ DELETE STAR FAILED: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete star: {str(e)}")

@app.get("/api/bookmark/{doc_id}")
async def get_bookmark_content(doc_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get the original content for a bookmarked item"""
    print(f"📖 BOOKMARK CONTENT REQUEST: user={current_user.username}, doc_id={doc_id}")
    
    try:
        # Search in both Milvus collections for the specific doc_id
        rich_content = None
        youtube_content = None
        
        # Try rich education collection first
        if connect_milvus():
            try:
                collection = Collection(COLL_RICH_EDUCATION)
                collection.load()
                
                results = collection.query(
                    expr=f"id == '{doc_id}'",
                    output_fields=["id", "concept_slug", "concept_title", "slice", "text", "tags"]
                )
                
                if results:
                    print(f"🔍 RAW RESULTS: {len(results)} items")
                    hit = results[0]
                    print(f"🔍 HIT TYPE: {type(hit)}")
                    print(f"🔍 HIT CONTENT: {hit}")
                    
                    # Convert Milvus result to plain dict - handle different result formats
                    try:
                        # Try treating as dict-like object
                        rich_content = {
                            "doc_id": str(hit.get("id", "") if hasattr(hit, 'get') else hit["id"] if "id" in hit else ""),
                            "title": str(hit.get("concept_title", "") if hasattr(hit, 'get') else hit.get("concept_title", "") if hasattr(hit, 'get') else hit["concept_title"] if "concept_title" in hit else ""),
                            "source": "rich_education",
                            "source_url": "",
                            "kind": str(hit.get("slice", "") if hasattr(hit, 'get') else hit["slice"] if "slice" in hit else ""),
                            "text": str(hit.get("text", "") if hasattr(hit, 'get') else hit["text"] if "text" in hit else ""),
                            "concept_slug": str(hit.get("concept_slug", "") if hasattr(hit, 'get') else hit["concept_slug"] if "concept_slug" in hit else ""),
                            "tags": list(hit.get("tags", []) if hasattr(hit, 'get') else hit["tags"] if "tags" in hit and hit["tags"] else [])
                        }
                    except Exception as field_error:
                        print(f"⚠️ Field extraction error: {field_error}")
                        # Fallback to manual field extraction
                        rich_content = {
                            "doc_id": str(doc_id),
                            "title": "Content Found",
                            "source": "rich_education", 
                            "source_url": "",
                            "kind": "content",
                            "text": str(hit) if hit else "",
                            "concept_slug": "",
                            "tags": []
                        }
                    print(f"📚 FOUND in rich_education: {rich_content['title']}")
                else:
                    print(f"🔍 NO RESULTS in rich_education for: {doc_id}")
                
            except Exception as e:
                print(f"⚠️ Rich education search failed: {e}")
            
            # Try YouTube collection if not found in rich education
            if not rich_content:
                try:
                    collection = Collection(COLL_YOUTUBE_VIDEOS)
                    collection.load()
                    
                    results = collection.query(
                        expr=f"doc_id == '{doc_id}'",
                        output_fields=["doc_id", "title", "source_url", "source", "kind", "text", "tags"]
                    )
                    
                    if results:
                        hit = results[0]
                        print(f"🔍 YT HIT TYPE: {type(hit)}")
                        print(f"🔍 YT HIT CONTENT: {hit}")
                        
                        # Convert Milvus result to plain dict - handle different result formats
                        try:
                            youtube_content = {
                                "doc_id": str(hit.get("doc_id", "") if hasattr(hit, 'get') else hit["doc_id"] if "doc_id" in hit else ""),
                                "title": str(hit.get("title", "") if hasattr(hit, 'get') else hit["title"] if "title" in hit else ""),
                                "source": str(hit.get("source", "") if hasattr(hit, 'get') else hit["source"] if "source" in hit else ""),
                                "source_url": str(hit.get("source_url", "") if hasattr(hit, 'get') else hit["source_url"] if "source_url" in hit else ""),
                                "kind": str(hit.get("kind", "") if hasattr(hit, 'get') else hit["kind"] if "kind" in hit else ""),
                                "text": str(hit.get("text", "") if hasattr(hit, 'get') else hit["text"] if "text" in hit else ""),
                                "tags": list(hit.get("tags", []) if hasattr(hit, 'get') else hit["tags"] if "tags" in hit and hit["tags"] else [])
                            }
                        except Exception as field_error:
                            print(f"⚠️ YT Field extraction error: {field_error}")
                            # Fallback to manual field extraction
                            youtube_content = {
                                "doc_id": str(doc_id),
                                "title": "YouTube Content Found",
                                "source": "youtube_creator_videos",
                                "source_url": "",
                                "kind": "video",
                                "text": str(hit) if hit else "",
                                "tags": []
                            }
                        print(f"🎥 FOUND in youtube_videos: {youtube_content['title']}")
                    else:
                        print(f"🔍 NO RESULTS in youtube_videos for: {doc_id}")
                        
                except Exception as e:
                    print(f"⚠️ YouTube search failed: {e}")
        
        # Return the found content
        content = rich_content or youtube_content
        if content:
            print(f"✅ BOOKMARK CONTENT FOUND: {content['title']}")
            print(f"📄 CONTENT TYPE: {type(content)}")
            print(f"📄 CONTENT KEYS: {content.keys()}")
            
            # Ensure all values are JSON serializable
            safe_content = {}
            for key, value in content.items():
                if value is None:
                    safe_content[key] = ""
                elif isinstance(value, (str, int, float, bool)):
                    safe_content[key] = value
                elif isinstance(value, (list, tuple)):
                    safe_content[key] = list(value) if value else []
                else:
                    safe_content[key] = str(value)
            
            print(f"✅ SAFE CONTENT: {safe_content}")
            return safe_content
        else:
            print(f"❌ BOOKMARK CONTENT NOT FOUND: {doc_id}")
            raise HTTPException(status_code=404, detail=f"Content not found for doc_id: {doc_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ BOOKMARK CONTENT FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bookmark content: {str(e)}")

@app.get("/api/next")
async def get_next_concepts(concept: str = Query(...), limit: int = 3, current_user: UserProfile = Depends(get_current_user)):
    """Get next learning concepts based on user's dynamic learning path"""
    user_topics = await get_user_learning_path(current_user.id)
    next_concepts = generate_next_concepts_from_path(user_topics, concept)
    return {"concept": concept, "next_concepts": next_concepts[:limit]}

@app.get("/api/learning-path")
async def get_learning_path(current_user: UserProfile = Depends(get_current_user)):
    """Get user's complete learning path"""
    try:
        user_topics = await get_user_learning_path(current_user.id)
        next_suggestions = generate_next_concepts_from_path(user_topics)
        
        return {
            "explored_topics": user_topics,
            "suggested_next": next_suggestions,
            "total_topics": len(user_topics)
        }
    except Exception as e:
        print(f"❌ Failed to get learning path: {e}")
        return {
            "explored_topics": [],
            "suggested_next": ["machine learning basics", "what is artificial intelligence", "data and algorithms"],
            "total_topics": 0
        }

# ================================= QUIZ ENDPOINTS =================================

@app.post("/api/quiz/start", response_model=QuizResponse)
async def start_quiz(request: QuizRequest, current_user: UserProfile = Depends(get_current_user)):
    """Start a new quiz session"""
    import uuid
    
    session_id = str(uuid.uuid4())
    
    print(f"🎯 STARTING QUIZ SESSION: {session_id}")
    print(f"   👤 User: {current_user.username}")
    print(f"   📚 Topic: {request.topic}")
    print(f"   🎚️ Difficulty: {request.difficulty}")
    print(f"   🔢 Questions: {request.num_questions}")
    
    # Generate questions
    questions = generate_quiz_questions(
        topic=request.topic,
        difficulty=request.difficulty,
        num_questions=request.num_questions,
        audience=current_user.age_group
    )
    
    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate quiz questions")
    
    # Create quiz session
    session = QuizSession(
        session_id=session_id,
        user_id=current_user.id,
        topic=request.topic,
        difficulty=request.difficulty,
        questions=questions,
        started_at=datetime.now()
    )
    
    # Store session
    quiz_sessions[session_id] = session
    
    print(f"   ✅ Generated {len(questions)} questions")
    print(f"   📝 First question: {questions[0].question[:50]}...")
    
    # Return first question
    return QuizResponse(
        session_id=session_id,
        question=questions[0],
        score=0,
        progress="1/" + str(len(questions)),
        completed=False
    )

@app.post("/api/quiz/answer", response_model=QuizResponse)
async def answer_quiz(request: QuizAnswer, current_user: UserProfile = Depends(get_current_user)):
    """Submit an answer to a quiz question"""
    
    session = quiz_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to quiz session")
    
    if session.completed_at:
        raise HTTPException(status_code=400, detail="Quiz already completed")
    
    current_q = session.questions[session.current_question]
    is_correct = request.answer == current_q.correct_answer
    
    print(f"🎯 QUIZ ANSWER: {request.session_id}")
    print(f"   📝 Question: {current_q.question[:50]}...")
    print(f"   ✅ User answer: {current_q.options[request.answer] if request.answer < len(current_q.options) else 'Invalid'}")
    print(f"   ✅ Correct: {is_correct}")
    
    # Record answer
    session.answers.append(request.answer)
    if is_correct:
        session.score += 1
    
    # Move to next question
    session.current_question += 1
    
    # Check if quiz is completed
    if session.current_question >= len(session.questions):
        session.completed_at = datetime.now()
        
        # Generate final feedback
        percentage = (session.score / len(session.questions)) * 100
        
        if percentage >= 80:
            feedback = f"Excellent work! You scored {session.score}/{len(session.questions)} ({percentage:.0f}%). You have a strong understanding of {session.topic}!"
        elif percentage >= 60:
            feedback = f"Good job! You scored {session.score}/{len(session.questions)} ({percentage:.0f}%). Consider reviewing some concepts to strengthen your understanding."
        else:
            feedback = f"Keep learning! You scored {session.score}/{len(session.questions)} ({percentage:.0f}%). Don't worry - practice makes perfect in {session.topic}!"
        
        return QuizResponse(
            session_id=session.session_id,
            question=current_q,
            is_correct=is_correct,
            feedback=current_q.explanation,
            score=session.score,
            progress=f"{len(session.questions)}/{len(session.questions)}",
            completed=True
        )
    
    # Return next question
    next_question = session.questions[session.current_question]
    
    return QuizResponse(
        session_id=session.session_id,
        question=next_question,
        is_correct=is_correct,
        feedback=current_q.explanation,
        score=session.score,
        progress=f"{session.current_question + 1}/{len(session.questions)}",
        completed=False
    )

@app.get("/api/quiz/result/{session_id}", response_model=QuizResult)
async def get_quiz_result(session_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get detailed quiz results"""
    
    session = quiz_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to quiz session")
    
    if not session.completed_at:
        raise HTTPException(status_code=400, detail="Quiz not yet completed")
    
    percentage = (session.score / len(session.questions)) * 100
    
    # Generate personalized feedback
    if percentage >= 80:
        feedback = f"Outstanding performance! You've mastered {session.topic} at the {session.difficulty} level."
        recommendations = [
            f"Try advanced topics in {session.topic}",
            "Explore related ML concepts",
            "Consider practical projects"
        ]
    elif percentage >= 60:
        feedback = f"Good foundation in {session.topic}! A few areas could use more practice."
        recommendations = [
            f"Review key {session.topic} concepts",
            "Take more practice quizzes",
            "Study specific topics you missed"
        ]
    else:
        feedback = f"You're learning! {session.topic} takes practice - keep going!"
        recommendations = [
            f"Start with basic {session.topic} concepts",
            "Use simpler learning materials",
            "Practice with easier quizzes first"
        ]
    
    return QuizResult(
        session_id=session_id,
        topic=session.topic,
        final_score=session.score,
        total_questions=len(session.questions),
        percentage=percentage,
        feedback=feedback,
        recommendations=recommendations
    )

# =============================================================================
# AGENTIC LEARNING ENDPOINTS
# =============================================================================

@app.post("/api/agentic/analyze")
async def analyze_user_learning(current_user: UserProfile = Depends(get_current_user)):
    """Run comprehensive agentic analysis of user's learning state"""
    if not agentic_system:
        raise HTTPException(status_code=503, detail="Agentic learning system not available")
    
    print(f"🤖 Running comprehensive analysis for user {current_user.id}")
    
    try:
        analysis = await agentic_system.analyze_user_completely(current_user.id)
        
        print(f"✅ Analysis complete. Found {len(analysis.get('learning_path_recommendations', []))} path recommendations")
        print(f"📊 Comprehension insights: {len(analysis.get('comprehension_insights', []))}")
        print(f"🎯 Goal analysis: {analysis.get('goal_analysis', {}).get('goals_analysis', [])}")
        print(f"📖 Content gaps: {len(analysis.get('content_gaps', []))}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error in agentic analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/agentic/insights/{user_id}")
async def get_learning_insights(user_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get learning insights for a specific user (admin or self only)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only access your own insights")
    
    if not agentic_system:
        raise HTTPException(status_code=503, detail="Agentic learning system not available")
    
    try:
        # Get just comprehension insights quickly
        insights = await agentic_system.comprehension_monitor.analyze_understanding_patterns(
            user_id, 
            await agentic_system._get_user_chat_patterns(user_id)
        )
        
        return {
            "user_id": user_id,
            "insights": [
                {
                    "type": insight.insight_type,
                    "topic": insight.topic,
                    "confidence": insight.confidence,
                    "action_suggestion": insight.action_suggestion,
                    "evidence": insight.evidence[:3]  # Limit evidence for API response
                }
                for insight in insights
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

@app.get("/api/agentic/recommendations")
async def get_learning_recommendations(current_user: UserProfile = Depends(get_current_user)):
    """Get personalized learning path recommendations"""
    if not agentic_system:
        raise HTTPException(status_code=503, detail="Agentic learning system not available")
    
    try:
        # Get learning history and progress
        learning_history = await agentic_system._get_user_learning_history(current_user.id)
        progress = await agentic_system._get_user_progress_tracking(current_user.id)
        
        # Generate recommendations
        recommendations = await agentic_system.learning_path_agent.analyze_and_recommend(
            current_user.id, learning_history, progress
        )
        
        return {
            "user_id": current_user.id,
            "recommendations": [
                {
                    "current_topic": rec.current_topic,
                    "next_topics": rec.next_topics,
                    "reasoning": rec.reasoning,
                    "prerequisites_needed": rec.prerequisites_needed,
                    "estimated_difficulty": rec.estimated_difficulty,
                    "confidence": rec.confidence
                }
                for rec in recommendations
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@app.get("/api/agentic/goal-progress")
async def get_goal_progress(current_user: UserProfile = Depends(get_current_user)):
    """Get autonomous goal progress analysis"""
    if not agentic_system:
        raise HTTPException(status_code=503, detail="Agentic learning system not available")
    
    try:
        goals = await agentic_system._get_user_goals(current_user.id)
        learning_history = await agentic_system._get_user_learning_history(current_user.id)
        
        analysis = await agentic_system.goal_achievement_assistant.analyze_goal_progress(
            current_user.id, goals, learning_history
        )
        
        return {
            "user_id": current_user.id,
            "goal_analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting goal progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get goal progress: {str(e)}")

@app.get("/api/agentic/content-suggestions")
async def get_content_suggestions(current_user: UserProfile = Depends(get_current_user)):
    """Get AI-curated content suggestions"""
    if not agentic_system:
        raise HTTPException(status_code=503, detail="Agentic learning system not available")
    
    try:
        learning_history = await agentic_system._get_user_learning_history(current_user.id)
        bookmarks = await agentic_system._get_user_bookmarks(current_user.id)
        
        suggestions = await agentic_system.content_curation_agent.identify_content_gaps(
            current_user.id, learning_history, bookmarks
        )
        
        return {
            "user_id": current_user.id,
            "content_suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting content suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get content suggestions: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "milvus": connect_milvus(),
        "neo4j": test_neo4j_connection(),
        "openai": oai is not None,
        "agentic_system": agentic_system is not None
    }

# ================================= EMAIL ENDPOINTS =================================

@app.post("/api/email/weekly-report")
async def send_weekly_report(current_user: UserProfile = Depends(get_current_user)):
    """Send weekly learning report to current user"""
    
    print(f"📧 Sending weekly report to user {current_user.id}")
    
    try:
        email_service = get_email_service()
        success = await email_service.send_weekly_report(current_user.id, test_mode=False)
        
        if success:
            return {
                "status": "sent",
                "message": "Weekly report sent successfully!",
                "user_id": current_user.id,
                "sent_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send weekly report")
            
    except Exception as e:
        print(f"❌ Error sending weekly report: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending report: {str(e)}")

@app.post("/api/email/weekly-report/preview")
async def preview_weekly_report(current_user: UserProfile = Depends(get_current_user)):
    """Preview weekly learning report (test mode - doesn't send email)"""
    
    print(f"📧 Generating weekly report preview for user {current_user.id}")
    
    try:
        email_service = get_email_service()
        success = await email_service.send_weekly_report(current_user.id, test_mode=True)
        
        if success:
            return {
                "status": "preview_generated",
                "message": "Weekly report preview generated (check server logs)",
                "user_id": current_user.id,
                "generated_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate preview")
            
    except Exception as e:
        print(f"❌ Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")

@app.get("/api/email/user-data/{user_id}")
async def get_user_email_data(
    user_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get user's weekly learning data for email generation (for debugging)"""
    
    # Only allow users to see their own data
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only access your own data")
    
    try:
        email_service = get_email_service()
        weekly_data = await email_service.get_user_weekly_data(user_id)
        
        if not weekly_data:
            raise HTTPException(status_code=404, detail="User data not found")
        
        # Generate insights
        insights = email_service.generate_learning_insights(weekly_data)
        
        return {
            "user_id": user_id,
            "weekly_data": {
                "topics_learned": len(weekly_data["weekly_topics"]),
                "questions_asked": len([chat for chat in weekly_data["weekly_chats"] if chat.get('role') == 'user']),
                "concepts_bookmarked": len(weekly_data["weekly_stars"]),
                "week_start": weekly_data["week_start"].isoformat(),
                "week_end": weekly_data["week_end"].isoformat()
            },
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting user email data: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

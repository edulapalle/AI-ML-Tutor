import os
import mmh3
import json
import requests
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import openai
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Import authentication modules
from auth_models import UserRegistration, UserLogin, UserProfile
from auth_service import AuthService

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "youtube_creator_videos")

# Reranking configuration
ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "true").lower() == "true"
RERANKING_MODEL = os.getenv("RERANKING_MODEL", "o3")  # GPT model for prompt-based reranking
INITIAL_SEARCH_MULTIPLIER = int(os.getenv("INITIAL_SEARCH_MULTIPLIER", "3"))  # How many more results to fetch initially

# Initialize OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

# Security scheme for JWT tokens
security = HTTPBearer()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """
    Dependency to get current authenticated user from JWT token
    """
    try:
        # Verify the JWT token
        token = credentials.credentials
        payload = AuthService.verify_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID from token
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user profile from database
        user = await AuthService.get_user_profile(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Pydantic models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_history: List[ChatMessage] = Field(default=[], description="Conversation history")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    sources: List[Dict[str, Any]] = Field(default=[], description="RAG sources")
    reranking_info: Dict[str, Any] = Field(default={}, description="Reranking information")

class AddDocumentRequest(BaseModel):
    text: str = Field(..., description="Document text to add")
    metadata: str = Field(default="", description="Optional metadata for the document")

class RerankingConfig(BaseModel):
    enabled: bool = Field(..., description="Whether reranking is enabled")
    model: str = Field(..., description="Reranking model to use")
    initial_search_multiplier: int = Field(..., description="Multiplier for initial search results")

# Create FastAPI app
app = FastAPI(
    title="AI Study Assistant",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Dependency for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token for authentication"""
    try:
        payload = AuthService.verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await AuthService.get_user_profile(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page for user authentication"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Serve the registration page for new user signup"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user with comprehensive study information"""
    try:
        result = await AuthService.register_user(user_data)
        return {
            "access_token": result["access_token"],
            "token_type": "bearer",
            "user": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/auth/login")
async def login_user(user_data: UserLogin):
    """Authenticate user and return access token for secure login"""
    try:
        user = await AuthService.authenticate_user(user_data.email, user_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        access_token = AuthService.create_access_token(data={"sub": user["id"]})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Login failed")

@app.get("/api/auth/validate")
async def validate_token(current_user: UserProfile = Depends(get_current_user)):
    """Validate JWT token and return user information"""
    return {"valid": True, "user": current_user}

@app.get("/api/auth/profile")
async def get_profile(current_user: UserProfile = Depends(get_current_user)):
    """Get current user profile information"""
    return current_user

@app.post("/api/auth/logout")
async def logout():
    """Logout user by clearing session data"""
    return {"message": "Logged out successfully"}

# Protected dashboard route
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard for authenticated users"""
    # Frontend handles authentication and will populate user data after page load
    return templates.TemplateResponse("index.html", {"request": request})

# Redirect root to login if not authenticated
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to login page for unauthenticated users"""
    return RedirectResponse(url="/login")

# Missing routes that are referenced in templates
@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Serve the forgot password page"""
    return templates.TemplateResponse("forgot-password.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """Serve the terms of service page"""
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Serve the privacy policy page"""
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Serve the settings page for system configuration"""
    return templates.TemplateResponse("settings.html", {"request": request})

# Utility functions
async def get_embedding(text: str) -> List[float]:
    """Get embedding for text using OpenAI."""
    if not client:
        return []
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return []

async def rerank_results(query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """Rerank search results using OpenAI's GPT model with prompt-based evaluation."""
    if not client or not documents or not ENABLE_RERANKING:
        return documents[:top_k]
    
    try:
        print(f"Reranking {len(documents)} documents using prompt-based evaluation")
        
        # Prepare documents for reranking
        doc_texts = []
        for doc in documents:
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            # Create a formatted document string for reranking
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            # Format document with metadata context for better semantic matching
            channel_name = metadata.get('channel_name', 'Unknown')
            video_title = metadata.get('video_title', 'Unknown Video')
            doc_str = f"Channel: {channel_name}\nVideo: {video_title}\nContent: {text}"
            doc_texts.append(doc_str)
        
        # Create evaluation prompt
        evaluation_prompt = f"""
You are an expert at evaluating the relevance of documents to a user query. 

User Query: "{query}"

Please evaluate each document below and assign a relevance score from 0.0 to 1.0, where:
- 0.0 = Completely irrelevant
- 0.5 = Somewhat relevant
- 1.0 = Highly relevant

Consider factors like:
- Semantic similarity to the query
- Whether the document directly addresses the query
- Contextual relevance
- Information completeness

Documents to evaluate:

"""
        
        # Add each document to the prompt with a number
        for i, doc_text in enumerate(doc_texts, 1):
            evaluation_prompt += f"\nDocument {i}:\n{doc_text}\n"
        
        evaluation_prompt += f"""

Please respond with ONLY a JSON array of scores, one for each document, in order.
Example format: [0.8, 0.3, 0.9, 0.1, 0.7]

Scores:"""
        
        # Get relevance scores from GPT
        try:
            response = await client.chat.completions.create(
                model=RERANKING_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise evaluator. Respond only with the JSON array of scores."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                max_tokens=200,
                temperature=0.1  # Low temperature for consistent scoring
            )
            
            # Parse the response to get scores
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON array from response
            import re
            json_match = re.search(r'\[[0-9.,\s]+\]', response_text)
            if json_match:
                scores_text = json_match.group()
                scores = [float(score.strip()) for score in scores_text.strip('[]').split(',')]
            else:
                # Fallback: try to parse the entire response as JSON
                scores = json.loads(response_text)
            
            # Ensure we have the right number of scores
            if len(scores) != len(documents):
                print(f"Warning: Expected {len(documents)} scores, got {len(scores)}")
                # Pad or truncate scores
                if len(scores) < len(documents):
                    scores.extend([0.0] * (len(documents) - len(scores)))
                else:
                    scores = scores[:len(documents)]
            
        except Exception as e:
            print(f"Error getting GPT scores: {e}")
            # Fallback to uniform scores
            scores = [0.5] * len(documents)
        
        # Create list of (score, index) tuples and sort by score
        scored_docs = [(scores[i], i) for i in range(len(documents))]
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Return reranked documents
        reranked_docs = []
        for score, idx in scored_docs[:top_k]:
            doc = documents[idx]
            # Add relevance score to metadata for debugging
            if 'rerank_score' not in doc:
                doc['rerank_score'] = score
            reranked_docs.append(doc)
        
        print(f"Reranking completed. Top relevance scores: {[f'{s:.3f}' for s, _ in scored_docs[:3]]}")
        return reranked_docs
        
    except Exception as e:
        print(f"Error in reranking: {e}")
        return documents[:top_k]

async def get_embedding_with_model(text: str, model: str) -> List[float]:
    """Get embedding for text using specified OpenAI model."""
    if not client:
        return []
    try:
        response = await client.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding with {model}: {e}")
        return []

async def search_similar_documents(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for similar documents using Zilliz dedicated API over HTTP with reranking."""        
    try:
        # Get query embedding
        query_embedding = await get_embedding(query)
        print('embeeding', query_embedding)
        if not query_embedding:
            return []

        # Prepare search request for Zilliz API
        search_url = f"{MILVUS_URI}/v2/vectordb/entities/search"
        headers = {
            "Authorization": f"Bearer {MILVUS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Search for more documents initially to allow reranking to select the best ones
        initial_limit = min(limit * INITIAL_SEARCH_MULTIPLIER, 20)  # Get 3x more results for reranking
        
        search_data = {
            "collectionName": COLLECTION_NAME,
            "data": [query_embedding],
            "limit": initial_limit,
            "outputFields": ["text", "metadata"]
        }

        response = requests.post(search_url, json=search_data, headers=headers)
        if response.status_code != 200:
            print(f"Zilliz API error: {response.status_code}")
            return []
        
        result = response.json()
        pretty_json_string = json.dumps(result, indent=4)
        print('milvus sources', pretty_json_string)

        sources = []
        if 'data' in result:
            for hit in result['data']:
                try:
                    # Parse metadata if it's a JSON string
                    metadata = hit.get('metadata', {})
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    
                    sources.append({
                        "text": hit.get('text', ''),
                        "metadata": metadata
                    })
                except Exception as e:
                    print(f"Error parsing metadata: {e}")
                    # Fallback if metadata parsing fails
                    sources.append({
                        "text": hit.get('text', ''),
                        "metadata": hit.get('metadata', {})
                    })
        
        # Apply reranking to improve result relevance
        reranked_sources = await rerank_results(query, sources, limit)
        
        pretty_json_string = json.dumps(reranked_sources, indent=4)
        print('reranked sources', pretty_json_string)
    

        return reranked_sources
        
    except Exception as e:
        print(f"Error searching documents: {e}")
        return []

async def chat_with_gpt_personalized(message: str, conversation_history: List[ChatMessage], sources: Optional[List[Dict[str, Any]]] = None, user_profile: Optional[UserProfile] = None) -> str:
    """Chat with GPT using conversation history, RAG sources, and personalized user profile."""
    if not client:
        return "OpenAI API key not configured."
    try:
        # Prepare personalized system message based on user profile
        system_message = "You are a helpful AI study assistant. Provide accurate and helpful responses."
        
        # Add personalization based on user profile
        if user_profile:
            personalization = f"""
You are helping {user_profile.username}, a {user_profile.study_level} level student currently in {user_profile.current_stage}.
Their interests include: {', '.join(user_profile.topics_of_interest)}
Their current goals are: {', '.join(user_profile.current_goals)}
"""
            if user_profile.preferred_learning_style:
                personalization += f"\nThey prefer {user_profile.preferred_learning_style} learning style."
            
            system_message += personalization + "\n\nPlease tailor your responses to their level and interests."
        
        # Add RAG sources context
        if sources:
            context_parts = []
            for source in sources:
                try:
                    metadata = json.loads(source['metadata'][0]) if source['metadata'][0] else {}
                    channel_name = metadata.get('channel_name', 'Unknown Channel')
                    video_title = metadata.get('video_title', 'Unknown Video')
                    youtube_id = metadata.get('youtube_id', '')
                    timestamp = metadata.get('start_time', '')
                    
                    print(channel_name, metadata)
                    # Format timestamp if available
                    if timestamp:
                        minutes = int(timestamp // 60)
                        seconds = int(timestamp % 60)
                        time_str = f"[{minutes:02d}:{seconds:02d}]"
                    else:
                        time_str = ""
                    
                    # Include YouTube ID if available
                    youtube_info = f" (ID: https://www.youtube.com/watch?v={youtube_id}&t={str(round(timestamp))}s )" if youtube_id else ""
                    context_parts.append(f"Source ({channel_name} - {video_title}{youtube_info} : {source['text']}")
                except Exception as e:
                    print(e)
                    # Fallback if metadata parsing fails
                    context_parts.append(f"Source: {source['text']}")
            
            context = "\n\n".join(context_parts)
            system_message += f"\n\n<Sources>:\n{context}"
        
        print(system_message)
        # Prepare messages
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Limit to last 10 messages
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error chatting with GPT: {e}")
        return "I apologize, but I'm having trouble processing your request right now."

async def chat_with_gpt(message: str, conversation_history: List[ChatMessage], sources: Optional[List[Dict[str, Any]]] = None) -> str:
    """Legacy chat function for backward compatibility."""
    return await chat_with_gpt_personalized(message, conversation_history, sources, None)

# Routes
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: UserProfile = Depends(get_current_user)):
    """Chat endpoint with RAG integration - requires authentication."""
    try:
        # Search for relevant documents
        sources = await search_similar_documents(request.message)
        
        print(sources)

        # Convert conversation history to ChatMessage objects
        history = [ChatMessage(role=msg.role, content=msg.content) 
                  for msg in request.conversation_history]
        
        # Get AI response - personalize based on user profile
        response = await chat_with_gpt_personalized(request.message, history, sources, current_user)
        
        # Prepare reranking information
        reranking_info = {
            "enabled": ENABLE_RERANKING,
            "model": RERANKING_MODEL,
            "initial_search_multiplier": INITIAL_SEARCH_MULTIPLIER,
            "total_sources_found": len(sources),
            "rerank_scores": [source.get('rerank_score', None) for source in sources if 'rerank_score' in source]
        }
        
        return ChatResponse(
            response=response,
            sources=sources,
            reranking_info=reranking_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reranking-config", response_model=RerankingConfig)
async def get_reranking_config():
    """Get current reranking configuration."""
    return RerankingConfig(
        enabled=ENABLE_RERANKING,
        model=RERANKING_MODEL,
        initial_search_multiplier=INITIAL_SEARCH_MULTIPLIER
    )

@app.post("/api/add-document")
async def add_document(request: AddDocumentRequest):
    """Add a document to the RAG system using Zilliz dedicated API."""
    try:
        # Generate Murmur3 hash of the text as primary key
        text_hash = mmh3.hash(request.text)
        
        print(text_hash)
        
        # Check if document already exists using Zilliz API
        query_url = f"{MILVUS_URI}/v2/vectordb/entities/search"
        headers = {
            "Authorization": f"Bearer {MILVUS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        query_data = {
            "collectionName": COLLECTION_NAME,
            "filter": f"primary_key == {text_hash}",
            "outputFields": ["primary_key"]
        }

        response = requests.post(query_url, json=query_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('data') and len(result['data']) > 0:
                return {"message": "Document already exists", "id": text_hash}
        
        # Get embedding
        embedding = await get_embedding(request.text)
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        json_metadata = json.loads(request.metadata)
        print(json_metadata)
        print(text_hash)

        # Insert into Zilliz using HTTP API
        insert_url = f"{MILVUS_URI}/v2/vectordb/entities/upsert"
        insert_data = {
            "collectionName": COLLECTION_NAME,
            "data": {
                "id": text_hash,
                "channel_name": json_metadata['channel_name'],
                "text": request.text,
                "vector": embedding,
                "metadata": request.metadata
            }
        }

        response = requests.post(insert_url, json=insert_data, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to insert document: {response.status_code}")
        
        return {"message": "Document added successfully", "id": text_hash}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Zilliz API connection
        headers = {
            "Authorization": f"Bearer {MILVUS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Simple health check using list collections endpoint
        health_url = f"{MILVUS_URI}/v2/vectordb/collections/list"
        response = requests.post(health_url, headers=headers)
        zilliz_connected = response.status_code == 200
        print(zilliz_connected)
        return {"status": "healthy", "zilliz_connected": zilliz_connected}
    except Exception as e:
        return {"status": "unhealthy", "zilliz_connected": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
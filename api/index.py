import os
import asyncio
import mmh3
import json
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import openai
from pymilvus import MilvusClient, Collection, CollectionSchema, FieldSchema, DataType, utility
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MILVUS_URI = os.getenv("MILVUS_URI", "https://in03-4efcec782ae2f4c.serverless.gcp-us-west1.cloud.zilliz.com")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN", "dca9ee30dd6accca68a63953d96a07cf3295cb68d1df55d93823135499762886d4ea0c5cb68b7307f72afce73a991ebc16447360")
COLLECTION_NAME = "youtube_creator_videos"

# Initialize OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

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

class AddDocumentRequest(BaseModel):
    text: str = Field(..., description="Document text to add")
    metadata: str = Field(default="", description="Optional metadata for the document")

# Milvus client
milvus_client = None

def connect_to_milvus():
    """Connect to Milvus database using MilvusClient."""
    global milvus_client
    try:
        milvus_client = MilvusClient(
            uri=MILVUS_URI,
            token=MILVUS_TOKEN
        )
        print("Connected to Milvus successfully")
        return True
    except Exception as e:
        print(f"Failed to connect to Milvus: {e}")
        return False

def setup_milvus_collection():
    """Setup Milvus collection for storing embeddings."""
    global milvus_client
    if not milvus_client:
        return
        
    try:
        # Check if collection exists
        collections = milvus_client.list_collections()
        if COLLECTION_NAME in collections:
            print(f"Collection {COLLECTION_NAME} already exists")
            return
        
        # Create collection with schema
        schema = {
            "fields": [
                {"name": "id", "dtype": "INT64", "is_primary": True},
                {"name": "text", "dtype": "VARCHAR", "max_length": 65535},
                {"name": "embedding", "dtype": "FLOAT_VECTOR", "dim": 3072},
                {"name": "channel_name", "dtype": "VARCHAR", "max_length": 128},
                {"name": "metadata", "dtype": "VARCHAR", "max_length": 65535},
            ],
            "description": "Chat embeddings collection"
        }
        
        milvus_client.create_collection(
            collection_name=COLLECTION_NAME,
            schema=schema
        )
        
        # Create index
        milvus_client.create_index(
            collection_name=COLLECTION_NAME,
            field_name="embedding",
            index_params={
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
        )
        
        print(f"Collection {COLLECTION_NAME} created successfully")
        
    except Exception as e:
        print(f"Failed to setup Milvus collection: {e}")

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    if connect_to_milvus():
        setup_milvus_collection()
    yield
    # Shutdown
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="ChatGPT RAG API",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="../static"), name="static")

# Templates
templates = Jinja2Templates(directory="../templates")

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

async def search_similar_documents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for similar documents in Milvus."""
    global milvus_client
    if not milvus_client:
        return []
        
    try:
        # Get query embedding
        query_embedding = await get_embedding(query)
        if not query_embedding:
            return []

        
        # Search in Milvus using MilvusClient
        results = milvus_client.search(
            collection_name=COLLECTION_NAME,
            data=[query_embedding],
            limit=limit,
            filter=f"channel_name == 'Eczachly_'",
            output_fields=["text", "metadata"]
        )
        
        sources = []
        for hits in results:
            for hit in hits:
                try:
                    # Parse metadata if it's a JSON string
                    metadata = hit['entity']['metadata']
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    
                    sources.append({
                        "text": hit['entity']['text'],
                        "metadata": metadata
                    })
                except:
                    # Fallback if metadata parsing fails
                    sources.append({
                        "text": hit['entity']['text'],
                        "metadata": hit['entity']['metadata']
                    })
        
        return sources
        
    except Exception as e:
        print(f"Error searching documents: {e}")
        return []

async def chat_with_gpt(message: str, conversation_history: List[ChatMessage], sources: Optional[List[Dict[str, Any]]] = None) -> str:
    """Chat with GPT using conversation history and optional RAG sources."""
    if not client:
        return "OpenAI API key not configured."
    try:
        # Prepare system message
        system_message = "You are a helpful AI assistant. Provide accurate and helpful responses. If a youtube link in the source, provide that as well with the proper timestamped youtube url with this format: https://youtube.com/watch?v=<id>&t=<time>s"
        if sources:
            # Enhanced context with channel information
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
                    youtube_info = f" (ID: https://www.youtube.com/watch?v={youtube_id})&t={str(round(timestamp))}s)" if youtube_id else ""
                    context_parts.append(f"Source ({channel_name} - {video_title}{youtube_info} : {source['text']}")
                except Exception as e :
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

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with RAG integration."""
    try:
        # Search for relevant documents
        sources = await search_similar_documents(request.message)
        
        print(sources)

        # Convert conversation history to ChatMessage objects
        history = [ChatMessage(role=msg.role, content=msg.content) 
                  for msg in request.conversation_history]
        
        # Get AI response
        response = await chat_with_gpt(request.message, history, sources)
        
        return ChatResponse(
            response=response,
            sources=sources
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-document")
async def add_document(request: AddDocumentRequest):
    """Add a document to the RAG system."""
    global milvus_client
    if not milvus_client:
        raise HTTPException(status_code=500, detail="Milvus not connected")
        
    try:
        # Generate Murmur3 hash of the text as primary key
        text_hash = mmh3.hash(request.text)
        

        print(text_hash)
        # Check if document already exists
        existing_docs = milvus_client.query(
            collection_name=COLLECTION_NAME,
            filter=f"id == {text_hash}",
            output_fields=["id"]
        )
        
        if existing_docs:
            return {"message": "Document already exists", "id": text_hash}
        
        # Get embedding
        embedding = await get_embedding(request.text)
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        

        json_metadata = json.loads(request.metadata)
        print(json_metadata)
        print(text_hash)

        # Insert into Milvus using MilvusClient
        milvus_client.insert(
            collection_name=COLLECTION_NAME,
            data={
                "primary_key": text_hash,
                "channel_name": json_metadata['channel_name'],
                "text": [request.text],
                "vector": embedding,
                "metadata": [request.metadata]
            }
        )
        
        return {"message": "Document added successfully", "id": text_hash}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    global milvus_client
    return {"status": "healthy", "milvus_connected": milvus_client is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
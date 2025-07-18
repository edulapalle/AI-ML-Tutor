import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Import the FastAPI app
from index import app

async def test_rag_query():
    """Test the RAG system with a specific query."""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test query that should return specific YouTube video
    test_query = "How do I become a senior data engineer?"
    expected_video_id = "CoDwI-gLSnI"
    expected_timestamp = "70"
    
    print(f"Testing RAG system with query: '{test_query}'")
    print(f"Expected video ID: {expected_video_id}")
    print(f"Expected timestamp: {expected_timestamp}s")
    
    # Make request to chat endpoint
    response = client.post("/api/chat", json={
        "message": test_query,
        "conversation_history": []
    })
    
    if response.status_code != 200:
        print(f"❌ Chat endpoint failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False
        
    result = response.json()
    print(f"✅ Chat endpoint successful")
    
    # Check if response contains the expected video
    response_text = result.get("response", "")
    sources = result.get("sources", [])
    reranking_info = result.get("reranking_info", {})
    
    print(f"Response length: {len(response_text)} characters")
    print(f"Number of sources: {len(sources)}")
    print(f"Reranking enabled: {reranking_info.get('enabled', False)}")
    
    # Check if the expected video ID is in the response
    if expected_video_id in response_text:
        print(f"✅ Found expected video ID '{expected_video_id}' in response")
    else:
        print(f"❌ Expected video ID '{expected_video_id}' not found in response")
        print(f"Response preview: {response_text[:500]}...")
        
    # Check if the expected timestamp is in the response
    if expected_timestamp in response_text:
        print(f"✅ Found expected timestamp '{expected_timestamp}s' in response")
    else:
        print(f"❌ Expected timestamp '{expected_timestamp}s' not found in response")
        
    # Check if the full expected URL is in the response
    expected_url = f"https://www.youtube.com/watch?v={expected_video_id}&t={expected_timestamp}s"
    if expected_url in response_text:
        print(f"✅ Found expected full URL in response")
    else:
        print(f"❌ Expected full URL not found in response")
        
    # Check sources for the expected video
    found_in_sources = False
    for i, source in enumerate(sources):
        source_text = source.get("text", "")
        metadata = source.get("metadata", {})
        
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
                
        youtube_id = json.loads(metadata[0]).get('youtube_id', '') if metadata and isinstance(metadata, list) and len(metadata) > 0 else ''
        if youtube_id == expected_video_id:
            print(f"✅ Found expected video in source {i+1}")
            found_in_sources = True
            break
            
    if not found_in_sources:
        print(f"❌ Expected video not found in any source")
        print("Available sources:")
        for i, source in enumerate(sources):
            metadata = source.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            youtube_id = json.loads(metadata[0]).get('youtube_id', '') if metadata and isinstance(metadata, list) and len(metadata) > 0 else 'N/A'
            print(f"  Source {i+1}: youtube_id={youtube_id}")
    
    # Check reranking scores if enabled
    if reranking_info.get("enabled", False):
        scores = reranking_info.get("rerank_scores", [])
        if scores:
            print(f"Reranking scores: {scores}")
            max_score = max(scores) if scores else 0
            print(f"Highest reranking score: {max_score:.3f}")
            
            if max_score > 0.7:
                print(f"✅ High reranking score indicates good relevance")
            else:
                print(f"⚠️  Low reranking score may indicate poor relevance")
    
    # Overall success criteria
    success = (
        expected_video_id in response_text and 
        expected_timestamp in response_text and
        expected_url in response_text
    )
    
    if success:
        print("🎉 RAG system test PASSED!")
        return True
    else:
        print("💥 RAG system test FAILED!")
        return False
        
async def test_health_endpoint():
    """Test the health endpoint."""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    print("Testing health endpoint...")
    response = client.get("/api/health")
    
    if response.status_code == 200:
        health_data = response.json()
        print(f"✅ Health endpoint successful")
        print(f"Status: {health_data.get('status')}")
        print(f"Zilliz connected: {health_data.get('zilliz_connected')}")
        return health_data.get('status') == 'healthy'
    else:
        print(f"❌ Health endpoint failed with status {response.status_code}")
        return False

async def test_reranking_config():
    """Test the reranking configuration endpoint."""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    print("Testing reranking config endpoint...")
    response = client.get("/api/reranking-config")
    
    if response.status_code == 200:
        config = response.json()
        print(f"✅ Reranking config endpoint successful")
        print(f"Reranking enabled: {config.get('enabled')}")
        print(f"Reranking model: {config.get('model')}")
        print(f"Initial search multiplier: {config.get('initial_search_multiplier')}")
        return True
    else:
        print(f"❌ Reranking config endpoint failed with status {response.status_code}")
        return False

async def test_with_custom_query(query: str, expected_video_id: Optional[str] = None, expected_timestamp: Optional[str] = None):
    """Test the RAG system with a custom query."""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    print(f"Testing RAG system with custom query: '{query}'")
    if expected_video_id:
        print(f"Expected video ID: {expected_video_id}")
    if expected_timestamp:
        print(f"Expected timestamp: {expected_timestamp}s")
    
    # Make request to chat endpoint
    response = client.post("/api/chat", json={
        "message": query,
        "conversation_history": []
    })
    
    if response.status_code != 200:
        print(f"❌ Chat endpoint failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False
        
    result = response.json()
    print(f"✅ Chat endpoint successful")
    
    # Check if response contains the expected video
    response_text = result.get("response", "")
    sources = result.get("sources", [])
    reranking_info = result.get("reranking_info", {})
    
    print(f"Response length: {len(response_text)} characters")
    print(f"Number of sources: {len(sources)}")
    print(f"Reranking enabled: {reranking_info.get('enabled', False)}")
    
    # Check for expected video if specified
    if expected_video_id:
        if expected_video_id in response_text:
            print(f"✅ Found expected video ID '{expected_video_id}' in response")
        else:
            print(f"❌ Expected video ID '{expected_video_id}' not found in response")
            print(f"Response preview: {response_text[:500]}...")
    
    # Check for expected timestamp if specified
    if expected_timestamp:
        if expected_timestamp in response_text:
            print(f"✅ Found expected timestamp '{expected_timestamp}s' in response")
        else:
            print(f"❌ Expected timestamp '{expected_timestamp}s' not found in response")
    
    # Check reranking scores if enabled
    if reranking_info.get("enabled", False):
        scores = reranking_info.get("rerank_scores", [])
        if scores:
            print(f"Reranking scores: {scores}")
            max_score = max(scores) if scores else 0
            print(f"Highest reranking score: {max_score:.3f}")
    
    return True

async def main():
    """Run all tests."""
    print("🚀 Starting RAG system tests...")
    
    # Test health endpoint first
    health_ok = await test_health_endpoint()
    if not health_ok:
        print("❌ Health check failed, skipping RAG test")
        sys.exit(1)
    
    # Test reranking config
    config_ok = await test_reranking_config()
    if not config_ok:
        print("⚠️  Reranking config test failed, but continuing...")
    
    # Test RAG query
    rag_ok = await test_rag_query()
    
    if not rag_ok:
        sys.exit(1)
    
    print("✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 
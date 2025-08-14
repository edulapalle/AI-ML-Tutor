#!/usr/bin/env python3
"""
Test script for RAG Backend API
Tests all endpoints and their functionality
"""

import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"

def test_query_endpoint():
    """Test the main /query endpoint"""
    print("🧪 Testing /query endpoint...")
    
    test_queries = [
        {
            "question": "What is machine learning?",
            "audience": "kid",
            "top_k": 5,
            "use_graph": True,
            "expected_intent": "explain"
        },
        {
            "question": "Compare supervised vs unsupervised learning",
            "audience": "teen", 
            "top_k": 8,
            "use_graph": True,
            "expected_intent": "compare"
        },
        {
            "question": "What should I learn after neural networks?",
            "audience": "kid",
            "top_k": 6,
            "use_graph": True,
            "expected_intent": "next"
        }
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query['question'][:50]}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json=query,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Intent: {data['intent']}, Citations: {len(data['citations'])}")
                print(f"   Next concepts: {len(data['next_concepts'])}")
                print(f"   Latency: {data['latency_ms']}ms")
                
                # Verify requirements
                assert data['intent'] == query['expected_intent'], f"Intent mismatch: {data['intent']}"
                assert len(data['citations']) >= 2, f"Need at least 2 citations, got {len(data['citations'])}"
                
                if query['expected_intent'] in ['compare', 'related', 'next']:
                    print(f"   Next concepts: {data['next_concepts']}")
                
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_star_endpoints():
    """Test the star endpoints"""
    print("\n🧪 Testing star endpoints...")
    
    test_user = "test-user-123"
    test_doc = "test-doc-456"
    
    try:
        # Test inserting a star
        star_data = {
            "user_id": test_user,
            "doc_id": test_doc,
            "note": "Great explanation of neural networks!"
        }
        
        response = requests.post(f"{BASE_URL}/star", json=star_data)
        if response.status_code == 200:
            print("✅ Star insertion successful")
        else:
            print(f"⚠️ Star insertion: {response.status_code} - {response.text}")
        
        # Test retrieving stars
        response = requests.get(f"{BASE_URL}/stars", params={"user_id": test_user})
        if response.status_code == 200:
            stars = response.json()
            print(f"✅ Star retrieval successful: {len(stars)} stars found")
        else:
            print(f"⚠️ Star retrieval: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Star endpoints error: {e}")

def test_next_endpoint():
    """Test the /next endpoint"""
    print("\n🧪 Testing /next endpoint...")
    
    test_concepts = [
        "neural networks",
        "machine learning", 
        "deep learning"
    ]
    
    for concept in test_concepts:
        print(f"\n📝 Testing concept: {concept}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/next",
                params={"concept": concept, "limit": 3}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Next concepts: {len(data['next_concepts'])}")
                print(f"   Learning path steps: {len(data.get('learning_path', []))}")
                
                if data.get('relationships'):
                    rels = data['relationships']
                    print(f"   Relationships found: {len(rels)} types")
                
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_guardrails():
    """Test content guardrails"""
    print("\n🧪 Testing guardrails...")
    
    out_of_scope_queries = [
        "How do I cook pasta?",
        "What's the weather today?",
        "Who won the football game?"
    ]
    
    for query in out_of_scope_queries:
        print(f"\n📝 Testing out-of-scope: {query}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json={
                    "question": query,
                    "audience": "kid",
                    "top_k": 5,
                    "use_graph": True
                }
            )
            
            if response.status_code == 400:
                print("✅ Correctly blocked out-of-scope query")
            else:
                print(f"⚠️ Should have been blocked: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting RAG Backend API Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print("✅ Server is running!")
    except Exception:
        print("❌ Server not running. Start with: uvicorn rag_backend:app --reload")
        return
    
    # Run tests
    test_query_endpoint()
    test_star_endpoints() 
    test_next_endpoint()
    test_guardrails()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main()

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

def get_auth_token():
    """Get authentication token for testing"""
    try:
        # Try to login with test credentials
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "test_integration@example.com",
                "password": "TestPassword123!"
            }
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception:
        pass
    
    # Try to register and login
    try:
        test_user = {
            "username": "testuser_rag",
            "email": "test_integration@example.com",
            "password": "TestPassword123!",
            "date_of_birth": "1995-01-01",
            "current_stage": "college",
            "study_level": "beginner",
            "topics_of_interest": ["machine_learning", "deep_learning"],
            "current_goals": ["Learn ML basics"],
            "preferred_learning_style": "study_and_test"
        }
        
        requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception:
        pass
    
    return None

def test_query_endpoint():
    """Test the main /api/chat endpoint"""
    print("🧪 Testing /api/chat endpoint...")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    test_queries = [
        {
            "question": "What is overfitting?",
            "audience": "kid",
            "top_k": 5,
            "use_graph": True,
            "expected_intent": "explain"
        },
        {
            "question": "Compare CNN vs RNN",
            "audience": "teen", 
            "top_k": 8,
            "use_graph": True,
            "expected_intent": "compare"
        },
        {
            "question": "Next after logistic regression?",
            "audience": "kid",
            "top_k": 6,
            "use_graph": True,
            "expected_intent": "next"
        },
        {
            "question": "Explain PCA",
            "audience": "kid",
            "top_k": 5,
            "use_graph": True,
            "expected_intent": "explain"
        },
        {
            "question": "Common DT mistakes",
            "audience": "teen",
            "top_k": 6,
            "use_graph": True,
            "expected_intent": "explain"
        }
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query['question'][:50]}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                headers=headers,
                json={
                    "message": query["question"],
                    "conversation_history": []
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Answer length: {len(data.get('answer', ''))} chars")
                
                # Check if answer exists
                if 'answer' in data and data['answer']:
                    print(f"   Answer preview: {data['answer'][:100]}...")
                else:
                    print("   ❌ No answer content")
                
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_star_endpoints():
    """Test the star endpoints"""
    print("\n🧪 Testing star endpoints...")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token for star tests")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test inserting a star
        star_data = {
            "doc_id": "test-doc-456",
            "note": "Great explanation of neural networks!"
        }
        
        response = requests.post(f"{BASE_URL}/api/star", headers=headers, json=star_data)
        if response.status_code == 200:
            print("✅ Star insertion successful")
        else:
            print(f"⚠️ Star insertion: {response.status_code} - {response.text}")
        
        # Test retrieving stars
        response = requests.get(f"{BASE_URL}/api/stars", headers=headers)
        if response.status_code == 200:
            stars = response.json()
            print(f"✅ Star retrieval successful: {len(stars)} stars found")
        else:
            print(f"⚠️ Star retrieval: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Star endpoints error: {e}")

def test_next_endpoint():
    """Test the /api/next endpoint"""
    print("\n🧪 Testing /api/next endpoint...")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token for next tests")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    test_concepts = [
        "neural networks",
        "machine learning", 
        "deep learning"
    ]
    
    for concept in test_concepts:
        print(f"\n📝 Testing concept: {concept}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/next",
                headers=headers,
                params={"concept": concept, "limit": 3}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response received")
                if 'next_concepts' in data:
                    print(f"   Next concepts: {len(data['next_concepts'])}")
                
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_guardrails():
    """Test content guardrails"""
    print("\n🧪 Testing guardrails...")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token for guardrail tests")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    out_of_scope_queries = [
        "How do I cook pasta?",
        "What's the weather today?",
        "Who won the football game?"
    ]
    
    for query in out_of_scope_queries:
        print(f"\n📝 Testing out-of-scope: {query}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                headers=headers,
                json={
                    "message": query,
                    "conversation_history": []
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

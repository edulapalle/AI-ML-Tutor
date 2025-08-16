#!/usr/bin/env python3
"""
Test script to demonstrate learning level adaptations
Tests the same questions across kid, teen, and adult levels
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token for testing"""
    try:
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
    return None

def test_learning_level_responses():
    """Test responses across different learning levels"""
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test questions
    questions = [
        "What is machine learning?",
        "What is the math behind it?"
    ]
    
    # Learning levels to test (these correspond to user age groups)
    levels = [
        ("kid", "Child-Friendly Level"),
        ("teen", "Teen Level"), 
        ("adult", "Adult Level")
    ]
    
    print("🧪 TESTING LEARNING LEVEL ADAPTATIONS")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Questions: {len(questions)}")
    print(f"📊 Learning Levels: {len(levels)}")
    print("=" * 60)
    
    for i, question in enumerate(questions, 1):
        print(f"\n🔍 QUESTION {i}: \"{question}\"")
        print("-" * 50)
        
        for level_code, level_name in levels:
            print(f"\n📚 {level_name.upper()}")
            print("." * 30)
            
            try:
                # Make request with specific audience level
                response = requests.post(
                    f"{BASE_URL}/api/chat",
                    headers=headers,
                    json={
                        "message": question,
                        "conversation_history": [],
                        "audience": level_code  # This should set the learning level
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', 'No answer received')
                    
                    # Extract key metrics
                    answer_length = len(answer)
                    word_count = len(answer.split())
                    citations = len(data.get('citations', []))
                    next_concepts = len(data.get('next_concepts', []))
                    
                    print(f"✅ Response received:")
                    print(f"   📏 Length: {answer_length} characters")
                    print(f"   📝 Words: {word_count}")
                    print(f"   📚 Citations: {citations}")
                    print(f"   🔗 Next concepts: {next_concepts}")
                    print(f"   📖 Preview: {answer[:150]}...")
                    
                    # Show full response if it's short enough
                    if answer_length < 500:
                        print(f"   📄 Full response: {answer}")
                    
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    print(f"   Error: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Small delay between requests
            time.sleep(1)
        
        print("\n" + "="*60)
    
    print("\n🎯 TEST COMPLETED!")
    print("💡 Key observations to look for:")
    print("   • Kid level: Simple language, short sentences, analogies")
    print("   • Teen level: More detail, moderate complexity")  
    print("   • Adult level: Technical depth, comprehensive explanations")

if __name__ == "__main__":
    test_learning_level_responses()

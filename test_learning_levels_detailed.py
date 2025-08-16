#!/usr/bin/env python3
"""
Detailed test to show actual response differences across learning levels
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

def test_detailed_responses():
    """Test and show full responses for each learning level"""
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    questions = [
        "What is machine learning?",
        "What is the math behind it?"
    ]
    
    levels = [
        ("kid", "CHILD-FRIENDLY"),
        ("teen", "TEEN LEVEL"),
        ("adult", "ADULT LEVEL")
    ]
    
    print("🔍 DETAILED LEARNING LEVEL COMPARISON")
    print("=" * 80)
    
    for q_num, question in enumerate(questions, 1):
        title = f"🎯 QUESTION {q_num}"
        question_formatted = f'"{question}"'
        print(f"\n{title:^80}")
        print(f"{question_formatted:^80}")
        print("=" * 80)
        
        responses = {}
        
        # Collect all responses first
        for level_code, level_name in levels:
            try:
                response = requests.post(
                    f"{BASE_URL}/api/chat",
                    headers=headers,
                    json={
                        "message": question,
                        "conversation_history": [],
                        "audience": level_code
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    responses[level_name] = {
                        'answer': data.get('answer', 'No answer'),
                        'citations': data.get('citations', []),
                        'next_concepts': data.get('next_concepts', [])
                    }
                else:
                    responses[level_name] = {'error': f"HTTP {response.status_code}"}
                    
                time.sleep(1)  # Small delay
                
            except Exception as e:
                responses[level_name] = {'error': str(e)}
        
        # Display responses
        for level_name in [name for _, name in levels]:
            if level_name not in responses:
                continue
                
            print(f"\n📚 {level_name}")
            print("-" * 60)
            
            if 'error' in responses[level_name]:
                print(f"❌ Error: {responses[level_name]['error']}")
                continue
            
            answer = responses[level_name]['answer']
            citations = responses[level_name]['citations']
            next_concepts = responses[level_name]['next_concepts']
            
            print(f"📏 Length: {len(answer)} chars | Words: {len(answer.split())}")
            print(f"📚 Citations: {len(citations)} | 🔗 Next: {len(next_concepts)}")
            print("\n📖 FULL RESPONSE:")
            print(answer)
            
            if citations:
                print(f"\n📚 CITATIONS ({len(citations)}):")
                for i, citation in enumerate(citations, 1):
                    source = citation.get('source', 'Unknown')
                    title = citation.get('title', 'No title')[:50]
                    print(f"   {i}. [{source}] {title}...")
            
            if next_concepts:
                print(f"\n🔗 NEXT CONCEPTS: {', '.join(next_concepts)}")
            
        print("\n" + "=" * 80)
    
    print("\n🎯 ANALYSIS COMPLETE!")

if __name__ == "__main__":
    test_detailed_responses()

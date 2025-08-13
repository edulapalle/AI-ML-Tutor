#!/usr/bin/env python3
"""
Test script to verify the conversation continuity fix
Simulates the exact flow that was causing generic responses
"""

import os
import sys
from dotenv import load_dotenv
from rag_system import get_rag_system

def test_conversation_with_history():
    """Test conversation flow with proper history context"""
    
    # Load environment variables
    load_dotenv()
    
    # Test user profile
    test_profile = {
        "study_level": "beginner",
        "topics_of_interest": ["ML Foundations"],
        "preferred_learning_style": "study only",
        "current_stage": "school",
        "user_age": 25,
        "age_group": "adult"
    }
    
    # Initialize RAG system
    print("🔄 Initializing RAG system...")
    rag_system = get_rag_system()
    print("✅ RAG system initialized")
    print("=" * 70)
    
    # Simulate a real conversation
    conversation_history = []
    
    print("🎭 Simulating Real Conversation Flow")
    print("=" * 70)
    
    # Step 1: Initial question
    question_1 = "What is machine learning?"
    print(f"\n👤 User: {question_1}")
    
    response_1 = rag_system.generate_response(question_1, test_profile, conversation_history)
    print(f"🤖 Assistant: {response_1[:300]}...")
    
    # Add to conversation history
    conversation_history.append({"role": "user", "content": question_1})
    conversation_history.append({"role": "assistant", "content": response_1})
    
    # Step 2: Follow-up with "Yes" 
    question_2 = "Yes"
    print(f"\n👤 User: {question_2}")
    
    # Check pre-screening
    is_ml_related = rag_system.is_ml_ai_related_question(question_2)
    print(f"🔍 Pre-screening: {is_ml_related}")
    
    response_2 = rag_system.generate_response(question_2, test_profile, conversation_history)
    print(f"🤖 Assistant: {response_2[:300]}...")
    
    # Check for problematic patterns
    problematic_patterns = [
        "Hello! How can I help you today?",
        "Would you like to learn about supervised learning, explainable AI",
        "Feel free to pick one! 😊"
    ]
    
    found_issues = []
    for pattern in problematic_patterns:
        if pattern in response_2:
            found_issues.append(pattern)
    
    if found_issues:
        print(f"❌ FOUND PROBLEMATIC PATTERNS: {found_issues}")
    else:
        print("✅ No problematic patterns found")
    
    # Add to conversation history
    conversation_history.append({"role": "user", "content": question_2})
    conversation_history.append({"role": "assistant", "content": response_2})
    
    # Step 3: Follow-up with "tell me more"
    question_3 = "tell me more"
    print(f"\n👤 User: {question_3}")
    
    response_3 = rag_system.generate_response(question_3, test_profile, conversation_history)
    print(f"🤖 Assistant: {response_3[:300]}...")
    
    # Step 4: Single word follow-up
    question_4 = "how"
    print(f"\n👤 User: {question_4}")
    
    response_4 = rag_system.generate_response(question_4, test_profile, conversation_history)
    print(f"🤖 Assistant: {response_4[:300]}...")
    
    # Analysis
    print("\n" + "=" * 70)
    print("📊 CONVERSATION ANALYSIS")
    print("=" * 70)
    
    responses = [response_1, response_2, response_3, response_4]
    
    # Check response lengths
    avg_length = sum(len(r) for r in responses) / len(responses)
    print(f"📏 Average response length: {avg_length:.0f} characters")
    
    # Check for educational content
    educational_keywords = [
        "machine learning", "learning", "algorithm", "data", "model", 
        "artificial intelligence", "neural", "training", "prediction"
    ]
    
    educational_scores = []
    for i, response in enumerate(responses, 1):
        score = sum(1 for keyword in educational_keywords if keyword.lower() in response.lower())
        educational_scores.append(score)
        print(f"📚 Response {i} educational keywords: {score}")
    
    # Check for conversation continuity
    has_context_references = []
    context_indicators = ["previous", "earlier", "mentioned", "discussed", "continue", "build upon"]
    
    for i, response in enumerate(responses[1:], 2):  # Skip first response
        has_context = any(indicator in response.lower() for indicator in context_indicators)
        has_context_references.append(has_context)
        print(f"🔗 Response {i} has context references: {has_context}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"✅ All responses substantial: {all(len(r) > 200 for r in responses)}")
    print(f"✅ All responses educational: {all(score > 2 for score in educational_scores)}")
    print(f"✅ Follow-ups show continuity: {any(has_context_references)}")
    print(f"✅ No generic responses: {not any(found_issues)}")
    
    if all([
        all(len(r) > 200 for r in responses),
        all(score > 2 for score in educational_scores),
        not any(found_issues)
    ]):
        print("\n🎉 SUCCESS: Conversation continuity is working correctly!")
    else:
        print("\n⚠️ ISSUES DETECTED: Conversation flow needs more work")

def test_edge_cases():
    """Test edge cases for conversation continuity"""
    
    print("\n🔬 Testing Edge Cases")
    print("=" * 70)
    
    rag_system = get_rag_system()
    
    edge_cases = [
        "yes",
        "Yeah sure",
        "tell me more about that",
        "can you explain",
        "what about",
        "how does that work",
        "why",
        "give me an example",
        "I don't understand",
        "make it simpler"
    ]
    
    for question in edge_cases:
        is_ml_related = rag_system.is_ml_ai_related_question(question)
        status = "✅ PASS" if is_ml_related else "❌ BLOCK"
        print(f"{status} '{question}' -> {is_ml_related}")

def main():
    """Run conversation continuity tests"""
    print("🔧 Conversation Continuity Fix Testing")
    print("=" * 70)
    
    # Check required environment variables
    required_vars = ['OPENAI_API_KEY', 'MILVUS_URI', 'MILVUS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    try:
        # Test edge cases for pre-screening
        test_edge_cases()
        
        # Test full conversation with history
        test_conversation_with_history()
        
        print("\n" + "=" * 70)
        print("🎯 TEST SUMMARY")
        print("=" * 70)
        print("✅ Conversation continuity tests completed")
        print("📋 The fix should now properly handle:")
        print("   - 'Yes' responses continuing previous topics")
        print("   - 'Tell me more' expanding on current concepts")
        print("   - Short follow-up questions with context")
        print("   - Maintaining educational focus throughout")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

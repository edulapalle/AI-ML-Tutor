#!/usr/bin/env python3
"""
Debug script to test conversation flow and identify the source of generic responses
"""

import os
import sys
from dotenv import load_dotenv
from rag_system import get_rag_system

def test_conversation_flow():
    """Test the exact conversation flow that causes the issue"""
    
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
    print("=" * 60)
    
    # Test sequence that reproduces the issue
    test_sequence = [
        {
            "step": 1,
            "question": "What is machine learning?",
            "description": "Initial ML question"
        },
        {
            "step": 2, 
            "question": "Yes",
            "description": "Follow-up response that should continue the topic"
        },
        {
            "step": 3,
            "question": "tell me more",
            "description": "Explicit request for more information"
        },
        {
            "step": 4,
            "question": "how",
            "description": "Single word follow-up"
        }
    ]
    
    print("🧪 Testing Conversation Flow")
    print("=" * 60)
    
    for test in test_sequence:
        print(f"\n📝 Step {test['step']}: {test['description']}")
        print(f"❓ Question: '{test['question']}'")
        
        # Test pre-screening first
        is_ml_related = rag_system.is_ml_ai_related_question(test['question'])
        print(f"🔍 Pre-screening result: {is_ml_related}")
        
        # Get full response
        response = rag_system.generate_response(test['question'], test_profile)
        print(f"🤖 Response length: {len(response)} characters")
        print(f"🤖 Response preview: {response[:200]}...")
        
        # Check for problematic patterns
        problematic_patterns = [
            "Hello! How can I help you today?",
            "Would you like to learn about supervised learning, explainable AI",
            "Feel free to pick one! 😊"
        ]
        
        for pattern in problematic_patterns:
            if pattern in response:
                print(f"⚠️ FOUND PROBLEMATIC PATTERN: '{pattern}'")
        
        print("-" * 40)

def test_pre_screening_only():
    """Test just the pre-screening function with various inputs"""
    
    print("\n🔍 Testing Pre-Screening Function")
    print("=" * 60)
    
    # Initialize RAG system
    rag_system = get_rag_system()
    
    test_inputs = [
        "What is machine learning?",
        "Yes",
        "yes", 
        "tell me more",
        "how",
        "why",
        "continue",
        "more",
        "please explain",
        "What's the weather?",
        "How do I cook pasta?"
    ]
    
    for question in test_inputs:
        result = rag_system.is_ml_ai_related_question(question)
        status = "✅ PASS" if result else "❌ BLOCK"
        print(f"{status} '{question}' -> {result}")

def main():
    """Run debugging tests"""
    print("🐛 Conversation Flow Debug Script")
    print("=" * 70)
    
    # Check required environment variables
    required_vars = ['OPENAI_API_KEY', 'MILVUS_URI', 'MILVUS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    try:
        # Test pre-screening function
        test_pre_screening_only()
        
        # Test full conversation flow
        test_conversation_flow()
        
        print("\n" + "=" * 70)
        print("🎯 DEBUG SUMMARY")
        print("=" * 70)
        print("✅ Debug tests completed")
        print("📊 Check the output above for:")
        print("   - Pre-screening accuracy for conversation continuations")
        print("   - Generic response patterns")
        print("   - Response length and content quality")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

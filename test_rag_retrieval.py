#!/usr/bin/env python3
"""
Test script to verify RAG system retrieval and child-friendly responses
This script tests if ML concepts are being retrieved correctly and responses are appropriate for children
"""

import os
import sys
from dotenv import load_dotenv
from rag_system import get_rag_system

# Sample child-like questions to test
TEST_QUESTIONS = [
    {
        "question": "What is machine learning?",
        "expected_concepts": ["Machine Learning", "Algorithm"],
        "difficulty": "beginner"
    },
    {
        "question": "How do neural networks work?",
        "expected_concepts": ["Neural Network", "Deep Learning"],
        "difficulty": "intermediate"
    },
    {
        "question": "What's the difference between supervised and unsupervised learning?",
        "expected_concepts": ["Supervised Learning", "Unsupervised Learning"],
        "difficulty": "beginner"
    },
    {
        "question": "Explain overfitting like I'm 10 years old",
        "expected_concepts": ["Overfitting"],
        "difficulty": "intermediate"
    },
    {
        "question": "What is classification in machine learning?",
        "expected_concepts": ["Classification"],
        "difficulty": "beginner"
    },
    {
        "question": "How does a computer learn to recognize pictures?",
        "expected_concepts": ["Neural Network", "Deep Learning", "Supervised Learning"],
        "difficulty": "intermediate"
    },
    {
        "question": "What are algorithms?",
        "expected_concepts": ["Algorithm"],
        "difficulty": "beginner"
    },
    {
        "question": "What is ChatGPT and how does it work?",
        "expected_concepts": ["Large Language Model (LLM)", "Generative AI"],
        "difficulty": "intermediate"
    }
]

# Sample user profiles to test personalization
TEST_USER_PROFILES = [
    {
        "name": "Elementary Student",
        "study_level": "beginner",
        "topics_of_interest": ["ML Foundations"],
        "preferred_learning_style": "study only",
        "current_stage": "school"
    },
    {
        "name": "High School Student",
        "study_level": "intermediate", 
        "topics_of_interest": ["Deep Learning Basics", "LLM & Generative AI"],
        "preferred_learning_style": "study and test",
        "current_stage": "school"
    },
    {
        "name": "College Student",
        "study_level": "advanced",
        "topics_of_interest": ["Practical ML Production", "Model Evaluation"],
        "preferred_learning_style": "study and live example demo build",
        "current_stage": "college"
    }
]

def test_concept_retrieval(rag_system):
    """Test if concepts are being retrieved correctly"""
    print("🔍 Testing Concept Retrieval")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in TEST_QUESTIONS:
        total_tests += 1
        question = test_case["question"]
        expected_concepts = test_case["expected_concepts"]
        
        print(f"\n📝 Question: {question}")
        
        # Search for relevant concepts
        concepts = rag_system.search_concepts(question, top_k=3)
        
        if not concepts:
            print("❌ No concepts retrieved")
            continue
        
        print(f"📊 Retrieved {len(concepts)} concepts:")
        retrieved_concept_names = []
        
        for i, concept in enumerate(concepts, 1):
            concept_name = concept.get('concept', 'Unknown')
            similarity = concept.get('similarity_score', 0)
            category = concept.get('category', 'Unknown')
            
            retrieved_concept_names.append(concept_name)
            print(f"   {i}. {concept_name} (Category: {category}, Similarity: {similarity:.3f})")
        
        # Check if any expected concepts were found
        found_expected = any(expected in retrieved_concept_names for expected in expected_concepts)
        
        if found_expected:
            print("✅ Expected concepts found!")
            passed_tests += 1
        else:
            print(f"❌ Expected concepts not found. Expected: {expected_concepts}")
            print(f"   Got: {retrieved_concept_names}")
    
    print(f"\n📊 Retrieval Test Results: {passed_tests}/{total_tests} passed")
    return passed_tests, total_tests

def test_child_friendly_responses(rag_system):
    """Test if responses are child-friendly and contain analogies"""
    print("\n🧒 Testing Child-Friendly Responses")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for profile in TEST_USER_PROFILES:
        for test_case in TEST_QUESTIONS[:3]:  # Test first 3 questions for each profile
            total_tests += 1
            question = test_case["question"]
            
            print(f"\n👤 User Profile: {profile['name']} ({profile['study_level']})")
            print(f"📝 Question: {question}")
            
            # Generate response using RAG system
            response = rag_system.generate_response(question, profile)
            
            if not response:
                print("❌ No response generated")
                continue
            
            print(f"🤖 Response: {response[:200]}..." if len(response) > 200 else f"🤖 Response: {response}")
            
            # Check for child-friendly indicators
            child_friendly_indicators = [
                "like" in response.lower(),  # Analogies often use "like"
                "imagine" in response.lower(),  # Good for children
                "think of" in response.lower(),  # Analogies
                "for example" in response.lower(),  # Examples
                "it's like when" in response.lower(),  # Analogies
                len(response.split()) < 150,  # Not too long
                "!" in response  # Enthusiastic tone
            ]
            
            score = sum(child_friendly_indicators)
            
            if score >= 2:  # At least 2 child-friendly indicators
                print(f"✅ Child-friendly response (Score: {score}/7)")
                passed_tests += 1
            else:
                print(f"❌ Not child-friendly enough (Score: {score}/7)")
    
    print(f"\n📊 Child-Friendly Test Results: {passed_tests}/{total_tests} passed")
    return passed_tests, total_tests

def test_analogy_presence(rag_system):
    """Test if responses contain the child analogies from our database"""
    print("\n🎭 Testing Analogy Presence")
    print("=" * 50)
    
    analogy_questions = [
        "What is machine learning?",
        "What is overfitting?", 
        "How do neural networks work?"
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for question in analogy_questions:
        total_tests += 1
        print(f"\n📝 Question: {question}")
        
        # Get concepts first
        concepts = rag_system.search_concepts(question, top_k=1)
        if concepts:
            analogy = concepts[0].get('child_analogy', '')
            print(f"📚 Original Analogy: {analogy[:100]}...")
            
            # Generate response
            response = rag_system.generate_response(question)
            print(f"🤖 Generated Response: {response[:150]}...")
            
            # Check if response incorporates analogy concepts
            analogy_words = analogy.lower().split()
            response_words = response.lower().split()
            
            # Look for key analogy concepts
            analogy_concepts = []
            for word in analogy_words:
                if len(word) > 4 and word in response_words:
                    analogy_concepts.append(word)
            
            if analogy_concepts or any(keyword in response.lower() for keyword in ['like', 'imagine', 'think of']):
                print(f"✅ Analogy concepts found: {analogy_concepts}")
                passed_tests += 1
            else:
                print("❌ No analogy concepts found in response")
        else:
            print("❌ No concepts retrieved")
    
    print(f"\n📊 Analogy Test Results: {passed_tests}/{total_tests} passed")
    return passed_tests, total_tests

def main():
    """Run all RAG system tests"""
    print("🧪 RAG System Child-Friendly Retrieval Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables exist
    required_vars = ['OPENAI_API_KEY', 'MILVUS_URI', 'MILVUS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    try:
        # Initialize RAG system
        print("🔄 Initializing RAG system...")
        rag_system = get_rag_system()
        
        # Check system status
        status = rag_system.get_system_status()
        
        print(f"📊 System Status:")
        print(f"   - Milvus Connected: {status['milvus_connected']}")
        print(f"   - OpenAI Available: {status['openai_available']}")
        print(f"   - Collection Exists: {status['collection_exists']}")
        print(f"   - Concepts Count: {status['concepts_count']}")
        
        if not status['milvus_connected']:
            print("❌ Milvus not connected")
            sys.exit(1)
        
        if not status['openai_available']:
            print("❌ OpenAI not available")
            sys.exit(1)
        
        if status['concepts_count'] == 0:
            print("❌ No concepts in database - run populate_ml_concepts.py first")
            sys.exit(1)
        
        # Run all tests
        retrieval_passed, retrieval_total = test_concept_retrieval(rag_system)
        friendly_passed, friendly_total = test_child_friendly_responses(rag_system)
        analogy_passed, analogy_total = test_analogy_presence(rag_system)
        
        # Final results
        total_passed = retrieval_passed + friendly_passed + analogy_passed
        total_tests = retrieval_total + friendly_total + analogy_total
        
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 60)
        print(f"🔍 Concept Retrieval: {retrieval_passed}/{retrieval_total}")
        print(f"🧒 Child-Friendly: {friendly_passed}/{friendly_total}")
        print(f"🎭 Analogy Presence: {analogy_passed}/{analogy_total}")
        print(f"📊 Overall Score: {total_passed}/{total_tests} ({(total_passed/total_tests)*100:.1f}%)")
        
        if (total_passed/total_tests) >= 0.7:
            print("🎉 RAG system is working well for child-friendly ML education!")
        elif (total_passed/total_tests) >= 0.5:
            print("⚠️ RAG system is working but could be improved")
        else:
            print("❌ RAG system needs significant improvements")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

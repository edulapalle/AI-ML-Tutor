#!/usr/bin/env python3
"""Comprehensive RAG System Tests

Tests all RAG functionality:
- Chat endpoint with different query types
- Intent classification (explain, define, compare, examples, quiz)
- Multi-source retrieval (Milvus collections)
- Response quality and structure
- Conversation context handling
- Age-appropriate responses
"""

import asyncio
import json
from fastapi.testclient import TestClient

# Import the app
try:
    from app import app
    print("✅ Successfully imported app")
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    exit(1)

# Test client
client = TestClient(app)

class TestRAGSystem:
    """Comprehensive RAG system test suite"""
    
    def __init__(self):
        self.auth_token = None
        self.conversation_history = []
        
        # Test queries for different intents
        self.test_queries = {
            "explain": [
                "What is machine learning?",
                "How does a neural network work?",
                "Explain overfitting in simple terms"
            ],
            "define": [
                "Define gradient descent",
                "What is a convolutional neural network?",
                "Define bias-variance tradeoff"
            ],
            "compare": [
                "Compare supervised vs unsupervised learning",
                "CNN vs RNN - what's the difference?",
                "Random Forest vs Decision Tree"
            ],
            "examples": [
                "Give me examples of classification algorithms",
                "Show me real-world applications of deep learning",
                "Examples of feature engineering techniques"
            ],
            "quiz": [
                "Quiz me on machine learning basics",
                "Test my knowledge of neural networks",
                "Ask me questions about data preprocessing"
            ]
        }
    
    def setup_auth(self):
        """Set up authentication for testing"""
        print("\n🔐 Setting up authentication...")
        
        # Try to register and login a test user
        test_user = {
            "username": "ragtest123",
            "email": "ragtest@example.com",
            "password": "TestPassword123!",
            "date_of_birth": "1995-05-15",
            "topics_of_interest": ["Machine Learning", "Deep Learning"],
            "current_stage": "college",
            "current_goals": ["Learn AI"],
            "study_level": "intermediate"
        }
        
        # Register (might already exist)
        client.post("/api/auth/register", json=test_user)
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        
        if login_response.status_code == 200:
            self.auth_token = login_response.json().get('access_token')
            print("✅ Authentication setup successful")
            return True
        else:
            print(f"⚠️ Authentication setup failed: {login_response.status_code}")
            return False
    
    def test_chat_basic_functionality(self):
        """Test basic chat functionality"""
        print("\n🧪 Testing Basic Chat Functionality...")
        
        test_message = "What is machine learning?"
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        response = client.post(
            "/api/chat",
            json={"message": test_message, "conversation_history": []},
            headers=headers
        )
        
        print(f"Chat response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            required_fields = ["response", "sources", "intent", "topics"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print(f"✅ Chat response has all required fields")
                print(f"   Intent detected: {data.get('intent')}")
                print(f"   Topics identified: {data.get('topics', [])}")
                print(f"   Sources count: {len(data.get('sources', []))}")
                print(f"   Response length: {len(data.get('response', ''))}")
                return True, data
            else:
                print(f"❌ Missing fields in response: {missing_fields}")
                return False, None
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"❌ Chat request failed: {error_detail}")
            return False, None
    
    def test_intent_classification(self):
        """Test intent classification for different query types"""
        print("\n🧪 Testing Intent Classification...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        results = {}
        
        for intent_type, queries in self.test_queries.items():
            print(f"\n  Testing {intent_type.upper()} intent...")
            intent_results = []
            
            for query in queries:
                response = client.post(
                    "/api/chat",
                    json={"message": query, "conversation_history": []},
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    detected_intent = data.get('intent', 'unknown')
                    intent_results.append({
                        "query": query,
                        "detected_intent": detected_intent,
                        "correct": detected_intent == intent_type
                    })
                    print(f"    '{query[:30]}...' → {detected_intent}")
                else:
                    intent_results.append({
                        "query": query,
                        "detected_intent": "error",
                        "correct": False
                    })
                    print(f"    '{query[:30]}...' → ERROR")
            
            # Calculate accuracy for this intent
            correct = sum(1 for r in intent_results if r["correct"])
            total = len(intent_results)
            accuracy = correct / total if total > 0 else 0
            
            results[intent_type] = {
                "accuracy": accuracy,
                "correct": correct,
                "total": total,
                "results": intent_results
            }
            
            print(f"  {intent_type.upper()} accuracy: {accuracy:.1%} ({correct}/{total})")
        
        # Overall accuracy
        total_correct = sum(r["correct"] for r in results.values())
        total_queries = sum(r["total"] for r in results.values())
        overall_accuracy = total_correct / total_queries if total_queries > 0 else 0
        
        print(f"\n📊 Overall intent classification accuracy: {overall_accuracy:.1%} ({total_correct}/{total_queries})")
        
        return overall_accuracy >= 0.7  # 70% accuracy threshold
    
    def test_response_quality(self):
        """Test response quality and structure"""
        print("\n🧪 Testing Response Quality...")
        
        test_query = "Explain the bias-variance tradeoff in machine learning"
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        response = client.post(
            "/api/chat",
            json={"message": test_query, "conversation_history": []},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get response: {response.status_code}")
            return False
        
        data = response.json()
        response_text = data.get('response', '')
        sources = data.get('sources', [])
        
        quality_checks = {
            "Response length": len(response_text) >= 100,  # At least 100 characters
            "Contains sources": len(sources) > 0,  # Has sources
            "Educational content": any(word in response_text.lower() for word in 
                                    ['bias', 'variance', 'overfitting', 'underfitting', 'model']),
            "Child-friendly": not any(word in response_text.lower() for word in 
                                    ['complex', 'sophisticated', 'advanced calculus']),
            "Has examples": any(word in response_text.lower() for word in 
                              ['example', 'imagine', 'like', 'similar']),
        }
        
        passed_checks = sum(quality_checks.values())
        total_checks = len(quality_checks)
        
        print(f"Quality checks passed: {passed_checks}/{total_checks}")
        for check, passed in quality_checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
        
        return passed_checks >= total_checks * 0.8  # 80% of checks should pass
    
    def test_conversation_context(self):
        """Test conversation context handling"""
        print("\n🧪 Testing Conversation Context...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # First message
        first_message = "What is a neural network?"
        response1 = client.post(
            "/api/chat",
            json={"message": first_message, "conversation_history": []},
            headers=headers
        )
        
        if response1.status_code != 200:
            print(f"❌ First message failed: {response1.status_code}")
            return False
        
        data1 = response1.json()
        
        # Build conversation history
        conversation_history = [
            {"role": "user", "content": first_message},
            {"role": "assistant", "content": data1.get('response', '')}
        ]
        
        # Follow-up message that requires context
        followup_message = "How many layers does it typically have?"
        response2 = client.post(
            "/api/chat",
            json={"message": followup_message, "conversation_history": conversation_history},
            headers=headers
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            response_text = data2.get('response', '').lower()
            
            # Check if response shows understanding of context
            context_indicators = [
                'layer' in response_text,
                'neural' in response_text or 'network' in response_text,
                len(response_text) > 50  # Meaningful response
            ]
            
            context_score = sum(context_indicators)
            print(f"Context understanding score: {context_score}/{len(context_indicators)}")
            
            if context_score >= 2:
                print("✅ Context handling working correctly")
                return True
            else:
                print("❌ Context not properly understood")
                return False
        else:
            print(f"❌ Follow-up message failed: {response2.status_code}")
            return False
    
    def test_age_appropriate_responses(self):
        """Test age-appropriate response generation"""
        print("\n🧪 Testing Age-Appropriate Responses...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Test with a complex topic
        test_query = "Explain backpropagation algorithm"
        response = client.post(
            "/api/chat",
            json={"message": test_query, "conversation_history": []},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get response: {response.status_code}")
            return False
        
        data = response.json()
        response_text = data.get('response', '').lower()
        
        # Check for child-friendly language
        child_friendly_indicators = [
            any(word in response_text for word in ['simple', 'imagine', 'like', 'similar to']),
            not any(word in response_text for word in ['calculus', 'derivative', 'gradient descent']),
            any(word in response_text for word in ['learning', 'practice', 'improve']),
            len([word for word in response_text.split() if len(word) > 12]) < 5  # Not too many long words
        ]
        
        friendly_score = sum(child_friendly_indicators)
        print(f"Child-friendly score: {friendly_score}/{len(child_friendly_indicators)}")
        
        if friendly_score >= 2:
            print("✅ Response is appropriately child-friendly")
            return True
        else:
            print("❌ Response may be too complex for children")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        print("\n🧪 Testing Error Handling...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        error_test_cases = [
            # Empty message
            {"message": "", "conversation_history": []},
            # Very long message
            {"message": "x" * 2000, "conversation_history": []},
            # Invalid conversation history format
            {"message": "test", "conversation_history": "invalid"},
        ]
        
        passed_tests = 0
        
        for i, test_case in enumerate(error_test_cases):
            response = client.post("/api/chat", json=test_case, headers=headers)
            
            if response.status_code in [400, 422]:  # Expected error codes
                print(f"✅ Error test {i+1}: Correctly handled invalid input")
                passed_tests += 1
            elif response.status_code == 200:
                # Some invalid inputs might still get responses
                print(f"⚠️ Error test {i+1}: Got response instead of error (might be okay)")
                passed_tests += 0.5
            else:
                print(f"❌ Error test {i+1}: Unexpected response code {response.status_code}")
        
        success_rate = passed_tests / len(error_test_cases)
        print(f"Error handling success rate: {success_rate:.1%}")
        
        return success_rate >= 0.7
    
    def run_all_tests(self):
        """Run complete RAG system test suite"""
        print("🎯 Starting Comprehensive RAG System Tests")
        print("=" * 60)
        
        # Setup authentication
        auth_success = self.setup_auth()
        if not auth_success:
            print("⚠️ Continuing without authentication (some features may not work)")
        
        tests = [
            ("Basic Chat Functionality", self.test_chat_basic_functionality),
            ("Intent Classification", self.test_intent_classification),
            ("Response Quality", self.test_response_quality),
            ("Conversation Context", self.test_conversation_context),
            ("Age-Appropriate Responses", self.test_age_appropriate_responses),
            ("Error Handling", self.test_error_handling),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                if test_name == "Basic Chat Functionality":
                    result, _ = test_func()  # This returns a tuple
                else:
                    result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print("\n" + "=" * 60)
        print("📊 RAG SYSTEM TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All RAG system tests passed!")
            return True
        else:
            print(f"⚠️ {total - passed} tests failed")
            return False

def main():
    """Run RAG system tests"""
    test_suite = TestRAGSystem()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ RAG system is working correctly!")
        exit(0)
    else:
        print("\n❌ RAG system has issues!")
        exit(1)

if __name__ == "__main__":
    main()

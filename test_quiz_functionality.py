#!/usr/bin/env python3
"""
Quiz Functionality Test Script
Tests all quiz endpoints and functionality
"""

import asyncio
import json
import sys
from datetime import datetime
import httpx

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "quiz_tester",
    "email": "quiz_test@example.com", 
    "password": "TestPass123!",
    "date_of_birth": "1995-01-01",
    "topics_of_interest": ["machine learning", "neural networks"],
    "current_stage": "beginner",
    "current_goals": ["learn basics"],
    "study_level": "beginner",
    "preferred_learning_style": "visual"
}

class QuizTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.session_id = None
        
    async def setup(self):
        """Setup test user and authentication"""
        print("🔧 Setting up test environment...")
        
        # Try to register test user (may fail if already exists)
        try:
            register_response = await self.client.post(
                f"{BASE_URL}/api/auth/register",
                json=TEST_USER
            )
            if register_response.status_code == 201:
                print("✅ Test user registered successfully")
            else:
                print(f"⚠️ User registration response: {register_response.status_code}")
        except Exception as e:
            print(f"⚠️ Registration attempt: {e}")
        
        # Login to get token
        try:
            login_response = await self.client.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                self.token = login_data.get("access_token")
                print("✅ Login successful, token acquired")
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                print(f"Response: {login_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
            
        return True
    
    async def test_health_check(self):
        """Test basic health check"""
        print("\n🏥 Testing health check...")
        try:
            response = await self.client.get(f"{BASE_URL}/api/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_start_quiz(self):
        """Test starting a quiz"""
        print("\n🎯 Testing quiz start...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        quiz_request = {
            "topic": "machine learning",
            "difficulty": "beginner",
            "num_questions": 3
        }
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/quiz/start",
                json=quiz_request,
                headers=headers
            )
            
            if response.status_code == 200:
                quiz_data = response.json()
                self.session_id = quiz_data.get("session_id")
                print(f"✅ Quiz started successfully!")
                print(f"   📝 Session ID: {self.session_id}")
                print(f"   ❓ First question: {quiz_data.get('question', {}).get('question', 'N/A')}")
                print(f"   📊 Progress: {quiz_data.get('progress', 'N/A')}")
                
                # Print options
                options = quiz_data.get('question', {}).get('options', [])
                for i, option in enumerate(options):
                    print(f"      {chr(65+i)}) {option}")
                    
                return True
            else:
                print(f"❌ Quiz start failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Quiz start error: {e}")
            return False
    
    async def test_answer_quiz(self):
        """Test answering quiz questions"""
        print("\n📝 Testing quiz answers...")
        
        if not self.session_id:
            print("❌ No active quiz session")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Answer 3 questions (assuming 3 questions in quiz)
        for question_num in range(1, 4):
            print(f"\n   Answering question {question_num}...")
            
            answer_request = {
                "session_id": self.session_id,
                "answer": 0  # Always choose first option for testing
            }
            
            try:
                response = await self.client.post(
                    f"{BASE_URL}/api/quiz/answer",
                    json=answer_request,
                    headers=headers
                )
                
                if response.status_code == 200:
                    answer_data = response.json()
                    is_correct = answer_data.get("is_correct")
                    feedback = answer_data.get("feedback", "No feedback")
                    score = answer_data.get("score", 0)
                    progress = answer_data.get("progress", "N/A")
                    completed = answer_data.get("completed", False)
                    
                    print(f"   ✅ Answer submitted successfully!")
                    print(f"   🎯 Correct: {is_correct}")
                    print(f"   📊 Score: {score}")
                    print(f"   📈 Progress: {progress}")
                    print(f"   💭 Feedback: {feedback[:100]}...")
                    
                    if completed:
                        print(f"   🎉 Quiz completed!")
                        return True
                    
                    # Show next question if not completed
                    next_question = answer_data.get("question", {})
                    if next_question:
                        print(f"   ❓ Next question: {next_question.get('question', 'N/A')}")
                        options = next_question.get('options', [])
                        for i, option in enumerate(options):
                            print(f"      {chr(65+i)}) {option}")
                    
                else:
                    print(f"   ❌ Answer submission failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Answer submission error: {e}")
                return False
        
        return True
    
    async def test_quiz_results(self):
        """Test getting quiz results"""
        print("\n📊 Testing quiz results...")
        
        if not self.session_id:
            print("❌ No active quiz session")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/quiz/result/{self.session_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                result_data = response.json()
                print(f"✅ Quiz results retrieved successfully!")
                print(f"   📚 Topic: {result_data.get('topic', 'N/A')}")
                print(f"   🎯 Final Score: {result_data.get('final_score', 0)}/{result_data.get('total_questions', 0)}")
                print(f"   📊 Percentage: {result_data.get('percentage', 0):.1f}%")
                print(f"   💭 Feedback: {result_data.get('feedback', 'N/A')}")
                
                recommendations = result_data.get('recommendations', [])
                if recommendations:
                    print(f"   📋 Recommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"      {i}. {rec}")
                        
                return True
            else:
                print(f"❌ Quiz results failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Quiz results error: {e}")
            return False
    
    async def test_quiz_generation(self):
        """Test quiz generation with different topics"""
        print("\n🎲 Testing quiz generation with different topics...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        test_topics = [
            {"topic": "neural networks", "difficulty": "beginner"},
            {"topic": "deep learning", "difficulty": "intermediate"},
            {"topic": "machine learning", "difficulty": "advanced"}
        ]
        
        for test_topic in test_topics:
            print(f"\n   Testing topic: {test_topic['topic']} ({test_topic['difficulty']})")
            
            quiz_request = {
                "topic": test_topic["topic"],
                "difficulty": test_topic["difficulty"],
                "num_questions": 2  # Smaller number for faster testing
            }
            
            try:
                response = await self.client.post(
                    f"{BASE_URL}/api/quiz/start",
                    json=quiz_request,
                    headers=headers
                )
                
                if response.status_code == 200:
                    quiz_data = response.json()
                    question = quiz_data.get('question', {})
                    print(f"   ✅ Generated successfully!")
                    print(f"   ❓ Question: {question.get('question', 'N/A')[:80]}...")
                    print(f"   🎚️ Options: {len(question.get('options', []))}")
                else:
                    print(f"   ❌ Generation failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Generation error: {e}")
                
        return True
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()
        print("\n🧹 Cleanup completed")
    
    async def run_all_tests(self):
        """Run all quiz tests"""
        print("🚀 Starting Quiz Functionality Tests")
        print("=" * 50)
        
        # Setup
        if not await self.setup():
            print("❌ Setup failed, aborting tests")
            return False
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Quiz Generation (Multiple Topics)", self.test_quiz_generation),
            ("Start Quiz", self.test_start_quiz),
            ("Answer Quiz", self.test_answer_quiz),
            ("Quiz Results", self.test_quiz_results),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All quiz functionality tests PASSED!")
        else:
            print(f"⚠️ {total - passed} tests FAILED")
            
        await self.cleanup()
        return passed == total

async def main():
    """Main test runner"""
    tester = QuizTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())

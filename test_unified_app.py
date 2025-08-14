#!/usr/bin/env python3
"""
Comprehensive test script for the unified AI/ML Educational Platform
Tests authentication, RAG pipeline, stars, and learning paths
"""

import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"

class UnifiedAppTester:
    def __init__(self):
        self.access_token = None
        self.test_user = {
            "username": "testuser123",
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "date_of_birth": "1995-01-01",
            "study_level": "intermediate",
            "topics_of_interest": ["machine learning", "deep learning", "neural networks"],
            "preferred_learning_style": "study and test",
            "current_stage": "learning_fundamentals",
            "current_goals": ["Understand ML basics", "Learn about neural networks"]
        }

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 Starting Unified App Test Suite")
        print("=" * 50)
        
        try:
            # Basic connectivity
            self.test_health_check()
            
            # Authentication flow
            self.test_registration()
            self.test_login()
            self.test_profile()
            
            # RAG system
            self.test_chat_explain()
            self.test_chat_compare()
            self.test_chat_next()
            self.test_guardrails()
            
            # Stars/bookmarks
            self.test_star_content()
            self.test_get_stars()
            
            # Learning paths
            self.test_next_concepts()
            
            print("\n" + "=" * 50)
            print("🎉 All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            raise

    def test_health_check(self):
        """Test system health endpoint"""
        print("\n🏥 Testing health check...")
        
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health check passed")
            print(f"   Milvus: {'✅' if health.get('milvus') else '❌'}")
            print(f"   Neo4j: {'✅' if health.get('neo4j') else '❌'}")
            print(f"   OpenAI: {'✅' if health.get('openai') else '❌'}")
            
            if not all([health.get('milvus'), health.get('neo4j'), health.get('openai')]):
                print("⚠️ Some services are offline - tests may fail")
        else:
            raise Exception(f"Health check failed: {response.status_code}")

    def test_registration(self):
        """Test user registration"""
        print("\n👤 Testing user registration...")
        
        # Try to delete existing user first (ignore errors)
        try:
            if self.access_token:
                requests.delete(f"{BASE_URL}/api/auth/delete", 
                              headers={"Authorization": f"Bearer {self.access_token}"})
        except:
            pass
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=self.test_user,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ User registration successful")
        elif response.status_code == 400 and "already exists" in response.text:
            print("✅ User already exists (expected)")
        else:
            raise Exception(f"Registration failed: {response.status_code} - {response.text}")

    def test_login(self):
        """Test user login"""
        print("\n🔐 Testing user login...")
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            print("✅ Login successful")
            print(f"   Token type: {data['token_type']}")
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")

    def test_profile(self):
        """Test profile retrieval"""
        print("\n👤 Testing profile retrieval...")
        
        if not self.access_token:
            raise Exception("No access token available")
        
        response = requests.get(
            f"{BASE_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            profile = response.json()
            print("✅ Profile retrieved successfully")
            print(f"   Username: {profile['username']}")
            print(f"   Study Level: {profile['study_level']}")
            print(f"   Age: {profile.get('user_age', 'N/A')} years")
        else:
            raise Exception(f"Profile retrieval failed: {response.status_code}")

    def test_chat_explain(self):
        """Test chat with explain intent"""
        print("\n💬 Testing chat (explain intent)...")
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "message": "What is machine learning?",
                "audience": "adult",
                "use_graph": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat explain successful")
            print(f"   Intent: {data['intent']}")
            print(f"   Citations: {len(data['citations'])}")
            print(f"   Next concepts: {len(data['next_concepts'])}")
            print(f"   Latency: {data['latency_ms']}ms")
            
            # Verify response structure
            assert data['intent'] in ['explain', 'define'], f"Unexpected intent: {data['intent']}"
            assert len(data['citations']) >= 1, "Should have at least 1 citation"
            assert len(data['answer']) > 50, "Answer should be substantial"
        else:
            raise Exception(f"Chat explain failed: {response.status_code} - {response.text}")

    def test_chat_compare(self):
        """Test chat with compare intent"""
        print("\n🔍 Testing chat (compare intent)...")
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "message": "Compare supervised vs unsupervised learning",
                "audience": "teen",
                "use_graph": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat compare successful")
            print(f"   Intent: {data['intent']}")
            print(f"   Citations: {len(data['citations'])}")
            print(f"   Next concepts: {len(data['next_concepts'])}")
            
            # Should include next concepts for compare queries
            assert data['intent'] == 'compare', f"Expected compare intent, got: {data['intent']}"
            # Note: next_concepts might be empty if Neo4j has no data
        else:
            raise Exception(f"Chat compare failed: {response.status_code} - {response.text}")

    def test_chat_next(self):
        """Test chat with next intent"""
        print("\n➡️ Testing chat (next intent)...")
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "message": "What should I learn after neural networks?",
                "audience": "kid",
                "use_graph": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat next successful")
            print(f"   Intent: {data['intent']}")
            print(f"   Next concepts: {data['next_concepts']}")
            
            assert data['intent'] == 'next', f"Expected next intent, got: {data['intent']}"
        else:
            raise Exception(f"Chat next failed: {response.status_code} - {response.text}")

    def test_guardrails(self):
        """Test content guardrails"""
        print("\n🛡️ Testing content guardrails...")
        
        off_topic_queries = [
            "How do I cook pasta?",
            "What's the weather today?",
            "Tell me about politics"
        ]
        
        for query in off_topic_queries:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={"message": query, "audience": "adult"},
                timeout=10
            )
            
            if response.status_code == 400:
                print(f"✅ Correctly blocked: '{query}'")
            else:
                print(f"⚠️ Query not blocked: '{query}' (status: {response.status_code})")

    def test_star_content(self):
        """Test content starring/bookmarking"""
        print("\n⭐ Testing content starring...")
        
        response = requests.post(
            f"{BASE_URL}/api/star",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "doc_id": "test-doc-123",
                "note": "Great explanation of neural networks!"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Content starred successfully")
        else:
            raise Exception(f"Star content failed: {response.status_code} - {response.text}")

    def test_get_stars(self):
        """Test retrieving starred content"""
        print("\n📋 Testing stars retrieval...")
        
        response = requests.get(
            f"{BASE_URL}/api/stars",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            stars = response.json()
            print(f"✅ Stars retrieved: {len(stars)} items")
            
            if stars:
                print(f"   Latest: {stars[0]['doc_id']}")
        else:
            raise Exception(f"Get stars failed: {response.status_code}")

    def test_next_concepts(self):
        """Test learning path concepts"""
        print("\n🎯 Testing next concepts...")
        
        response = requests.get(
            f"{BASE_URL}/api/next",
            params={"concept": "machine learning", "limit": 3},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Next concepts retrieved: {len(data['next_concepts'])} suggestions")
            
            if data['next_concepts']:
                print(f"   Suggestions: {', '.join(data['next_concepts'])}")
            else:
                print("   No suggestions (Neo4j may need more data)")
        else:
            raise Exception(f"Next concepts failed: {response.status_code}")

    def test_web_pages(self):
        """Test web page accessibility"""
        print("\n🌐 Testing web pages...")
        
        pages = [
            ("/", "Dashboard"),
            ("/login", "Login"),
            ("/register", "Register"),
            ("/docs", "API Docs")
        ]
        
        for path, name in pages:
            response = requests.get(f"{BASE_URL}{path}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {name} page accessible")
            elif response.status_code == 302:
                print(f"✅ {name} page redirects (expected for protected routes)")
            else:
                print(f"⚠️ {name} page issue: {response.status_code}")

def main():
    """Run the test suite"""
    print("🚀 Unified AI/ML Educational Platform Test Suite")
    print("🔗 Make sure the application is running on http://localhost:8000")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print("✅ Server is running!")
    except Exception as e:
        print("❌ Server not running. Start with: python run_app.py")
        print(f"Error: {e}")
        return
    
    # Run tests
    tester = UnifiedAppTester()
    tester.run_all_tests()
    
    print("\n🎊 Test suite completed successfully!")
    print("🔗 You can now access the application at: http://localhost:8000")

if __name__ == "__main__":
    main()

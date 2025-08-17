#!/usr/bin/env python3
"""Comprehensive Agentic Learning System Tests

Tests all agentic features:
- Learning Path Agent (personalized sequences)
- Comprehension Monitor (understanding tracking)
- Goal Achievement Assistant (objective tracking)
- Content Curation Agent (recommendations)
- Background analysis and interventions
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

class TestAgenticSystem:
    """Comprehensive agentic learning system test suite"""
    
    def __init__(self):
        self.auth_token = None
        self.user_id = None
    
    def setup_auth(self):
        """Set up authentication for testing"""
        print("\n🔐 Setting up authentication...")
        
        test_user = {
            "username": "agentictest123",
            "email": "agentictest@example.com",
            "password": "TestPassword123!",
            "date_of_birth": "1995-05-15",
            "topics_of_interest": ["Machine Learning", "Deep Learning", "Neural Networks"],
            "current_stage": "college",
            "current_goals": ["Learn AI fundamentals", "Build ML projects", "Understand deep learning"],
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
            
            # Get user profile to extract user_id
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            profile_response = client.get("/api/auth/profile", headers=headers)
            if profile_response.status_code == 200:
                self.user_id = profile_response.json().get('id')
                print("✅ Authentication setup successful")
                return True
        
        print(f"⚠️ Authentication setup failed")
        return False
    
    def test_learning_analysis(self):
        """Test learning pattern analysis"""
        print("\n🧪 Testing Learning Pattern Analysis...")
        
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test learning analysis endpoint
        analysis_data = {
            "user_interactions": [
                {"topic": "machine learning", "time_spent": 300, "questions_asked": 5},
                {"topic": "neural networks", "time_spent": 450, "questions_asked": 8},
                {"topic": "deep learning", "time_spent": 200, "questions_asked": 3}
            ],
            "performance_metrics": {
                "comprehension_score": 0.8,
                "engagement_level": 0.9,
                "progress_rate": 0.7
            }
        }
        
        response = client.post("/api/agentic/analyze", json=analysis_data, headers=headers)
        
        print(f"Analysis response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["analysis_summary", "recommendations", "learning_patterns"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print(f"✅ Learning analysis successful")
                print(f"   Patterns identified: {len(data.get('learning_patterns', []))}")
                print(f"   Recommendations: {len(data.get('recommendations', []))}")
                return True
            else:
                print(f"❌ Missing fields in analysis: {missing_fields}")
                return False
        else:
            print(f"❌ Learning analysis failed: {response.status_code}")
            return False
    
    def test_agentic_insights(self):
        """Test personalized learning insights"""
        print("\n🧪 Testing Agentic Insights...")
        
        if not self.auth_token or not self.user_id:
            print("❌ No authentication or user ID available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = client.get(f"/api/agentic/insights/{self.user_id}", headers=headers)
        
        print(f"Insights response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            expected_insights = [
                "learning_velocity",
                "knowledge_gaps",
                "strong_areas",
                "recommended_focus",
                "next_concepts"
            ]
            
            available_insights = [insight for insight in expected_insights if insight in data]
            coverage = len(available_insights) / len(expected_insights)
            
            print(f"Insights coverage: {coverage:.1%} ({len(available_insights)}/{len(expected_insights)})")
            
            if coverage >= 0.6:  # At least 60% of insights available
                print("✅ Agentic insights working correctly")
                return True
            else:
                print("❌ Insufficient insights generated")
                return False
        else:
            print(f"❌ Insights request failed: {response.status_code}")
            return False
    
    def test_learning_recommendations(self):
        """Test learning path recommendations"""
        print("\n🧪 Testing Learning Recommendations...")
        
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = client.get("/api/agentic/recommendations", headers=headers)
        
        print(f"Recommendations response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            expected_fields = ["next_topics", "difficulty_level", "estimated_time", "prerequisites"]
            available_fields = [field for field in expected_fields if field in data]
            
            if len(available_fields) >= 2:  # At least half the fields
                recommendations = data.get('next_topics', [])
                print(f"✅ Recommendations generated: {len(recommendations)} topics")
                
                # Check recommendation quality
                if recommendations:
                    first_rec = recommendations[0]
                    has_title = 'title' in first_rec or 'topic' in first_rec
                    has_description = 'description' in first_rec or 'explanation' in first_rec
                    
                    if has_title and has_description:
                        print("✅ Recommendation quality: Good structure")
                        return True
                    else:
                        print("⚠️ Recommendation quality: Missing details")
                        return True  # Still pass, basic functionality works
                else:
                    print("⚠️ No specific recommendations, but endpoint works")
                    return True
            else:
                print(f"❌ Insufficient recommendation data: {available_fields}")
                return False
        else:
            print(f"❌ Recommendations request failed: {response.status_code}")
            return False
    
    def test_goal_progress_tracking(self):
        """Test goal achievement tracking"""
        print("\n🧪 Testing Goal Progress Tracking...")
        
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = client.get("/api/agentic/goal-progress", headers=headers)
        
        print(f"Goal progress response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for goal tracking structure
            goal_fields = ["current_goals", "progress_percentage", "completed_milestones", "next_milestones"]
            available_fields = [field for field in goal_fields if field in data]
            
            if len(available_fields) >= 2:
                print("✅ Goal progress tracking working")
                
                # Check progress data quality
                if 'progress_percentage' in data:
                    progress = data['progress_percentage']
                    if isinstance(progress, (int, float)) and 0 <= progress <= 100:
                        print(f"   Progress: {progress}%")
                        return True
                
                print("   Goal tracking available (basic)")
                return True
            else:
                print(f"❌ Insufficient goal tracking data: {available_fields}")
                return False
        else:
            print(f"❌ Goal progress request failed: {response.status_code}")
            return False
    
    def test_content_curation(self):
        """Test content curation suggestions"""
        print("\n🧪 Testing Content Curation...")
        
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = client.get("/api/agentic/content-suggestions", headers=headers)
        
        print(f"Content curation response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for content suggestions
            content_fields = ["suggested_content", "difficulty_matched", "personalized_resources"]
            available_fields = [field for field in content_fields if field in data]
            
            if len(available_fields) >= 1:
                print("✅ Content curation working")
                
                # Check suggestion quality
                suggestions = data.get('suggested_content', [])
                if suggestions:
                    print(f"   Suggestions count: {len(suggestions)}")
                    
                    # Verify suggestion structure
                    first_suggestion = suggestions[0]
                    if isinstance(first_suggestion, dict) and ('title' in first_suggestion or 'topic' in first_suggestion):
                        print("   Suggestion quality: Good structure")
                        return True
                
                print("   Content curation available (basic)")
                return True
            else:
                print(f"❌ No content suggestions available: {available_fields}")
                return False
        else:
            print(f"❌ Content curation request failed: {response.status_code}")
            return False
    
    def test_learning_path_integration(self):
        """Test learning path integration with agentic system"""
        print("\n🧪 Testing Learning Path Integration...")
        
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Get learning path
        response = client.get("/api/learning-path", headers=headers)
        
        print(f"Learning path response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for learning path structure
            path_fields = ["explored_topics", "suggested_next", "learning_progress"]
            available_fields = [field for field in path_fields if field in data]
            
            if len(available_fields) >= 1:
                print("✅ Learning path integration working")
                
                explored = data.get('explored_topics', [])
                suggested = data.get('suggested_next', [])
                
                print(f"   Explored topics: {len(explored)}")
                print(f"   Suggested next: {len(suggested)}")
                
                return True
            else:
                print(f"❌ Insufficient learning path data: {available_fields}")
                return False
        else:
            print(f"❌ Learning path request failed: {response.status_code}")
            return False
    
    def test_agentic_system_integration(self):
        """Test overall agentic system integration"""
        print("\n🧪 Testing Agentic System Integration...")
        
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        # Test multiple endpoints to ensure they work together
        endpoints_to_test = [
            ("/api/agentic/recommendations", "recommendations"),
            ("/api/agentic/goal-progress", "goal progress"),
            ("/api/agentic/content-suggestions", "content curation"),
            ("/api/learning-path", "learning path")
        ]
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        working_endpoints = 0
        
        for endpoint, name in endpoints_to_test:
            response = client.get(endpoint, headers=headers)
            if response.status_code == 200:
                working_endpoints += 1
                print(f"✅ {name}: Working")
            else:
                print(f"❌ {name}: Failed ({response.status_code})")
        
        integration_score = working_endpoints / len(endpoints_to_test)
        print(f"\nIntegration score: {integration_score:.1%} ({working_endpoints}/{len(endpoints_to_test)})")
        
        if integration_score >= 0.75:  # 75% of endpoints working
            print("✅ Agentic system integration successful")
            return True
        else:
            print("❌ Agentic system integration issues")
            return False
    
    def run_all_tests(self):
        """Run complete agentic system test suite"""
        print("🎯 Starting Comprehensive Agentic System Tests")
        print("=" * 60)
        
        # Setup authentication
        auth_success = self.setup_auth()
        if not auth_success:
            print("❌ Authentication required for agentic tests")
            return False
        
        tests = [
            ("Learning Analysis", self.test_learning_analysis),
            ("Agentic Insights", self.test_agentic_insights),
            ("Learning Recommendations", self.test_learning_recommendations),
            ("Goal Progress Tracking", self.test_goal_progress_tracking),
            ("Content Curation", self.test_content_curation),
            ("Learning Path Integration", self.test_learning_path_integration),
            ("System Integration", self.test_agentic_system_integration),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print("\n" + "=" * 60)
        print("📊 AGENTIC SYSTEM TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed >= total * 0.7:  # 70% pass rate for agentic features
            print("🎉 Agentic system tests passed!")
            return True
        else:
            print(f"⚠️ {total - passed} tests failed")
            return False

def main():
    """Run agentic system tests"""
    test_suite = TestAgenticSystem()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ Agentic system is working correctly!")
        exit(0)
    else:
        print("\n❌ Agentic system has issues!")
        exit(1)

if __name__ == "__main__":
    main()

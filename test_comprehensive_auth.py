#!/usr/bin/env python3
"""Comprehensive Authentication System Tests

Tests all authentication features:
- User registration with validation
- User login with JWT tokens
- Profile management
- Password security
- Session handling
- Error scenarios
"""

import asyncio
import json
import jwt
from datetime import datetime, date
from fastapi.testclient import TestClient
from auth_models import UserRegistration, UserLogin

# Import the app
try:
    from app import app
    print("✅ Successfully imported app")
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    exit(1)

# Test client
client = TestClient(app)

class TestAuthentication:
    """Comprehensive authentication test suite"""
    
    def __init__(self):
        self.test_user_data = {
            "username": "testuser123",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "date_of_birth": "1995-05-15",
            "topics_of_interest": ["Machine Learning", "Deep Learning"],
            "current_stage": "college",
            "current_goals": ["Learn Python", "Build ML projects"],
            "study_level": "intermediate",
            "preferred_learning_style": "visual"
        }
        self.auth_token = None
        self.user_id = None
    
    def test_user_registration(self):
        """Test user registration with comprehensive validation"""
        print("\n🧪 Testing User Registration...")
        
        # Test successful registration
        response = client.post("/api/auth/register", json=self.test_user_data)
        print(f"Registration response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Registration successful: {data.get('message')}")
            self.user_id = data.get('user_id')
            return True
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            if "already exists" in error_detail:
                print(f"⚠️ User already exists (expected in testing): {error_detail}")
                return True
            else:
                print(f"❌ Registration failed: {error_detail}")
                return False
        else:
            print(f"❌ Unexpected registration response: {response.status_code}")
            return False
    
    def test_registration_validation(self):
        """Test registration validation rules"""
        print("\n🧪 Testing Registration Validation...")
        
        test_cases = [
            # Missing required fields
            {
                "data": {"username": "test", "email": "test@example.com"},
                "expected": 422,
                "description": "Missing required fields"
            },
            # Invalid email format
            {
                "data": {**self.test_user_data, "email": "invalid-email"},
                "expected": 422,
                "description": "Invalid email format"
            },
            # Short password
            {
                "data": {**self.test_user_data, "password": "123"},
                "expected": 422,
                "description": "Password too short"
            },
            # Future birth date
            {
                "data": {**self.test_user_data, "date_of_birth": "2030-01-01"},
                "expected": 422,
                "description": "Future birth date"
            }
        ]
        
        passed = 0
        for test_case in test_cases:
            response = client.post("/api/auth/register", json=test_case["data"])
            if response.status_code == test_case["expected"]:
                print(f"✅ {test_case['description']}: Correctly rejected")
                passed += 1
            else:
                print(f"❌ {test_case['description']}: Expected {test_case['expected']}, got {response.status_code}")
        
        print(f"📊 Validation tests: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)
    
    def test_user_login(self):
        """Test user login and JWT token generation"""
        print("\n🧪 Testing User Login...")
        
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        
        response = client.post("/api/auth/login", json=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access_token')
            print(f"✅ Login successful, token received")
            
            # Validate JWT token structure
            if self.auth_token:
                try:
                    # Decode without verification (just to check structure)
                    decoded = jwt.decode(self.auth_token, options={"verify_signature": False})
                    print(f"✅ JWT token structure valid: {decoded.keys()}")
                    return True
                except jwt.InvalidTokenError:
                    print(f"❌ Invalid JWT token structure")
                    return False
            else:
                print(f"❌ No token in response")
                return False
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"❌ Login failed: {error_detail}")
            return False
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        print("\n🧪 Testing Invalid Login Scenarios...")
        
        test_cases = [
            {
                "email": "nonexistent@example.com",
                "password": "password123",
                "description": "Non-existent email"
            },
            {
                "email": self.test_user_data["email"],
                "password": "wrongpassword",
                "description": "Wrong password"
            },
            {
                "email": "invalid-email",
                "password": "password123",
                "description": "Invalid email format"
            }
        ]
        
        passed = 0
        for test_case in test_cases:
            response = client.post("/api/auth/login", json={
                "email": test_case["email"],
                "password": test_case["password"]
            })
            
            if response.status_code in [400, 401, 422]:
                print(f"✅ {test_case['description']}: Correctly rejected ({response.status_code})")
                passed += 1
            else:
                print(f"❌ {test_case['description']}: Should be rejected, got {response.status_code}")
        
        print(f"📊 Invalid login tests: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)
    
    def test_profile_access(self):
        """Test authenticated profile access"""
        print("\n🧪 Testing Profile Access...")
        
        if not self.auth_token:
            print("❌ No auth token available for profile test")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = client.get("/api/auth/profile", headers=headers)
        
        if response.status_code == 200:
            profile_data = response.json()
            expected_fields = ["id", "username", "email", "study_level", "user_age"]
            
            missing_fields = [field for field in expected_fields if field not in profile_data]
            if not missing_fields:
                print(f"✅ Profile access successful with all expected fields")
                print(f"   Username: {profile_data.get('username')}")
                print(f"   Study Level: {profile_data.get('study_level')}")
                print(f"   Age: {profile_data.get('user_age')}")
                return True
            else:
                print(f"❌ Profile missing fields: {missing_fields}")
                return False
        else:
            print(f"❌ Profile access failed: {response.status_code}")
            return False
    
    def test_unauthorized_access(self):
        """Test access without authentication"""
        print("\n🧪 Testing Unauthorized Access...")
        
        # Test profile access without token
        response = client.get("/api/auth/profile")
        if response.status_code == 401:
            print("✅ Unauthorized access correctly blocked")
            return True
        else:
            print(f"❌ Should require authentication, got {response.status_code}")
            return False
    
    def test_invalid_token(self):
        """Test access with invalid token"""
        print("\n🧪 Testing Invalid Token Access...")
        
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/auth/profile", headers=invalid_headers)
        
        if response.status_code == 401:
            print("✅ Invalid token correctly rejected")
            return True
        else:
            print(f"❌ Invalid token should be rejected, got {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run complete authentication test suite"""
        print("🎯 Starting Comprehensive Authentication Tests")
        print("=" * 60)
        
        tests = [
            ("User Registration", self.test_user_registration),
            ("Registration Validation", self.test_registration_validation),
            ("User Login", self.test_user_login),
            ("Invalid Login", self.test_invalid_login),
            ("Profile Access", self.test_profile_access),
            ("Unauthorized Access", self.test_unauthorized_access),
            ("Invalid Token", self.test_invalid_token),
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
        print("📊 AUTHENTICATION TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All authentication tests passed!")
            return True
        else:
            print(f"⚠️ {total - passed} tests failed")
            return False

def main():
    """Run authentication tests"""
    test_suite = TestAuthentication()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ Authentication system is working correctly!")
        exit(0)
    else:
        print("\n❌ Authentication system has issues!")
        exit(1)

if __name__ == "__main__":
    main()

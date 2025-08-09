#!/usr/bin/env python3
"""
Test script to create sample user registrations and verify authentication
This will test the complete authentication flow and verify data in Supabase
"""

import requests
import json
from datetime import date

# Test server configuration
BASE_URL = "http://localhost:8000"

# Sample test users data
TEST_USERS = [
    {
        "username": "john_student",
        "email": "john.student@example.com",
        "password": "securepass123",
        "date_of_birth": "2000-01-15",
        "topics_of_interest": ["ML Foundations", "Supervised Learning", "Data Prep & Features (EDA)"],
        "current_stage": "college",
        "current_goals": ["Learn Python basics", "Build a web application", "Master data analysis"],
        "study_level": "beginner",
        "preferred_learning_style": "study_and_test"
    },
    {
        "username": "sarah_dev",
        "email": "sarah.dev@example.com", 
        "password": "mypassword456",
        "date_of_birth": "1995-03-22",
        "topics_of_interest": ["Deep Learning Basics", "LLM & Generative AI", "Practical ML"],
        "current_stage": "work",
        "current_goals": ["Become a full-stack developer", "Learn advanced React patterns"],
        "study_level": "intermediate",
        "preferred_learning_style": "study_and_demo"
    },
    {
        "username": "mike_researcher",
        "email": "mike.research@example.com",
        "password": "research789",
        "date_of_birth": "1988-07-10",
        "topics_of_interest": ["Model Evaluation", "Optimization", "Production ML", "Interpretability & Ethics"],
        "current_stage": "work",
        "current_goals": ["Publish AI research papers", "Build computer vision models"],
        "study_level": "advanced",
        "preferred_learning_style": "study_only"
    }
]

def test_user_registration(user_data):
    """Test user registration with sample data"""
    print(f"\n🧪 Testing registration for user: {user_data['username']}")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=user_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration successful!")
            print(f"   User ID: {data.get('user', {}).get('user_id', 'N/A')}")
            print(f"   Access Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   Token Type: {data.get('token_type', 'N/A')}")
            return data
        else:
            print("❌ Registration failed!")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure the server is running on port 8000")
        return None
    except requests.exceptions.Timeout:
        print("❌ Request timed out!")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_user_login(email, password):
    """Test user login with credentials"""
    print(f"\n🔐 Testing login for: {email}")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"   Access Token: {data.get('access_token', 'N/A')[:20]}...")
            return data
        else:
            print("❌ Login failed!")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_user_profile(access_token):
    """Test fetching user profile with token"""
    print(f"\n👤 Testing profile fetch...")
    print("-" * 50)
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BASE_URL}/api/auth/profile",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Profile fetch successful!")
            print(f"   Username: {data.get('username', 'N/A')}")
            print(f"   Email: {data.get('email', 'N/A')}")
            print(f"   Study Level: {data.get('study_level', 'N/A')}")
            print(f"   Current Stage: {data.get('current_stage', 'N/A')}")
            print(f"   Topics: {', '.join(data.get('topics_of_interest', [])[:3])}...")
            return data
        else:
            print("❌ Profile fetch failed!")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Profile fetch error: {e}")
        return None

def test_dashboard_access():
    """Test dashboard page access"""
    print(f"\n🏠 Testing dashboard access...")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/dashboard", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard accessible!")
            print(f"   Page size: {len(response.text)} bytes")
            return True
        else:
            print("❌ Dashboard access failed!")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard access error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 AI Study Assistant - Authentication Test")
    print("=" * 60)
    
    # Test server connectivity
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except:
        print(f"❌ Server is not running at {BASE_URL}")
        print("Please start the server with: python index.py")
        return
    
    successful_registrations = []
    
    # Test user registrations
    for user_data in TEST_USERS:
        result = test_user_registration(user_data)
        if result:
            successful_registrations.append((user_data, result))
    
    print(f"\n📊 Registration Summary:")
    print(f"   Successful: {len(successful_registrations)}/{len(TEST_USERS)}")
    
    # Test login and profile for the first successful user
    if successful_registrations:
        user_data, reg_result = successful_registrations[0]
        
        # Test login
        login_result = test_user_login(user_data['email'], user_data['password'])
        
        if login_result:
            # Test profile fetch
            test_user_profile(login_result['access_token'])
    
    # Test dashboard access
    test_dashboard_access()
    
    print("\n" + "=" * 60)
    print("🎯 Test Instructions:")
    print("1. Check your Supabase dashboard -> Table Editor -> users table")
    print("2. You should see the registered users with their data")
    print("3. Try logging in at: http://localhost:8000/login")
    print("4. Use any of these test credentials:")
    
    for user in TEST_USERS:
        print(f"   📧 {user['email']} / 🔑 {user['password']}")
    
    print("\n✨ If tests pass, your authentication system is working correctly!")

if __name__ == "__main__":
    main()

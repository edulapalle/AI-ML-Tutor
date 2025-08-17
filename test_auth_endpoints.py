#!/usr/bin/env python3
"""
Test authentication endpoints on Railway
Debug registration and login issues
"""

import json
import httpx
import asyncio
from datetime import datetime

# Railway app URL
BASE_URL = "https://web-production-ff950.up.railway.app"

async def test_auth_endpoints():
    """Test authentication endpoints"""
    print("🔐 Testing Authentication Endpoints")
    print("=" * 50)
    
    # Test data
    test_user = {
        "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "date_of_birth": "1990-01-01",
        "topics_of_interest": ["Machine Learning", "Deep Learning"],
        "study_method": "Study Only",
        "current_goals": ["Learn Python", "Build AI projects"]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Registration endpoint
        print("\n🧪 Testing Registration")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/register",
                json=test_user,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                print("✅ Registration successful!")
                reg_data = response.json()
                print(f"User ID: {reg_data.get('user_id', 'Not provided')}")
            else:
                print("❌ Registration failed")
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
        
        # Test 2: Login endpoint
        print("\n🧪 Testing Login")
        try:
            login_data = {
                "email": test_user["email"],
                "password": test_user["password"]
            }
            
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                print("✅ Login successful!")
                login_data = response.json()
                token = login_data.get('access_token')
                if token:
                    print(f"Token received: {token[:20]}...")
                    return token
            else:
                print("❌ Login failed")
                
        except Exception as e:
            print(f"❌ Login error: {e}")
        
        # Test 3: Check pages that were 404
        print("\n🧪 Testing Missing Pages")
        for page in ["/terms", "/privacy"]:
            try:
                response = await client.get(f"{BASE_URL}{page}")
                print(f"{page}: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ {page} working")
                else:
                    print(f"❌ {page} still failing")
            except Exception as e:
                print(f"❌ {page} error: {e}")
    
    return None

async def test_environment_debug():
    """Test environment and database connectivity"""
    print("\n🔍 Testing Environment Debug")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/detailed-health")
            if response.status_code == 200:
                data = response.json()
                print("Environment Status:")
                env = data.get("environment", {})
                for key, value in env.items():
                    status = "✅" if value else "❌"
                    print(f"  {status} {key}: {value}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")

def main():
    """Main test function"""
    print("🚂 Railway Authentication Testing")
    print(f"🎯 Target: {BASE_URL}")
    
    # Run async tests
    asyncio.run(test_auth_endpoints())
    asyncio.run(test_environment_debug())
    
    print("\n" + "=" * 50)
    print("📋 Common Issues & Solutions:")
    print("1. 'No such file or directory' → Missing import (json)")
    print("2. '400 Bad Request' → Check Supabase configuration")
    print("3. '404 Not Found' → Missing route handlers")
    print("4. 'Authentication error' → Database connection issues")

if __name__ == "__main__":
    main()

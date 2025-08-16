#!/usr/bin/env python3
"""
Quick API test for Agentic Learning System
Run this while your app is running to test the endpoints
"""

import asyncio
import httpx
import json

async def test_agentic_endpoints():
    """Test all agentic API endpoints"""
    print("🧪 Testing Agentic API Endpoints")
    print("=" * 40)
    
    # You'll need to replace this with a real auth token from your browser
    # Instructions: 
    # 1. Login to your app
    # 2. Open browser dev tools (F12)
    # 3. Go to Application/Storage -> Local Storage
    # 4. Copy the 'auth_token' value
    AUTH_TOKEN = "your-auth-token-here"  # Replace this!
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health check (should show agentic system status)
        print("1. 🔍 Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/api/health")
            if response.status_code == 200:
                health = response.json()
                print(f"   ✅ Health: {health.get('status')}")
                print(f"   🤖 Agentic System: {'✅ Active' if health.get('agentic_system') else '❌ Inactive'}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        if AUTH_TOKEN == "your-auth-token-here":
            print("\n⚠️  To test authenticated endpoints:")
            print("   1. Login to your app at http://localhost:8000")
            print("   2. Open browser dev tools (F12)")
            print("   3. Go to Application -> Local Storage")
            print("   4. Copy the 'auth_token' value")
            print("   5. Replace AUTH_TOKEN in this script")
            print("   6. Run this script again")
            return
        
        # Test 2: Get learning insights
        print("\n2. 🧠 Testing insights endpoint...")
        try:
            # Get current user first
            user_response = await client.get(f"{base_url}/api/user", headers=headers)
            if user_response.status_code == 200:
                user = user_response.json()
                user_id = user.get('id')
                print(f"   👤 Testing for user: {user.get('username')} ({user_id})")
                
                insights_response = await client.get(f"{base_url}/api/agentic/insights/{user_id}", headers=headers)
                if insights_response.status_code == 200:
                    insights = insights_response.json()
                    print(f"   ✅ Generated {len(insights.get('insights', []))} insights")
                    for insight in insights.get('insights', [])[:2]:
                        print(f"      💡 {insight.get('type')}: {insight.get('action_suggestion')[:50]}...")
                else:
                    print(f"   ❌ Insights failed: {insights_response.status_code}")
            else:
                print(f"   ❌ User info failed: {user_response.status_code}")
        except Exception as e:
            print(f"   ❌ Insights error: {e}")
        
        # Test 3: Get recommendations
        print("\n3. 📚 Testing recommendations endpoint...")
        try:
            response = await client.get(f"{base_url}/api/agentic/recommendations", headers=headers)
            if response.status_code == 200:
                data = response.json()
                recs = data.get('recommendations', [])
                print(f"   ✅ Generated {len(recs)} recommendations")
                for rec in recs[:2]:
                    print(f"      🎯 {rec.get('current_topic')} → {rec.get('next_topics')}")
            else:
                print(f"   ❌ Recommendations failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Recommendations error: {e}")
        
        # Test 4: Full analysis
        print("\n4. 🔬 Testing full analysis endpoint...")
        try:
            response = await client.post(f"{base_url}/api/agentic/analyze", headers=headers)
            if response.status_code == 200:
                analysis = response.json()
                print(f"   ✅ Analysis completed!")
                print(f"      📊 Learning paths: {len(analysis.get('learning_path_recommendations', []))}")
                print(f"      🧠 Insights: {len(analysis.get('comprehension_insights', []))}")
                print(f"      📖 Content gaps: {len(analysis.get('content_gaps', []))}")
                
                # Show autonomous actions taken
                actions = analysis.get('synthesis', {}).get('actions_taken', [])
                if actions:
                    print(f"      🤖 Autonomous actions taken: {len(actions)}")
                    for action in actions[:2]:
                        print(f"         • {action.get('description', 'Action taken')}")
            else:
                print(f"   ❌ Analysis failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
    
    print("\n🎉 API Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_agentic_endpoints())

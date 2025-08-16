#!/usr/bin/env python3
"""
YouTube API Setup Guide and Tester
==================================

This script helps you:
1. Get instructions for YouTube Data API v3 setup
2. Test your API key
3. Test the real-time monitoring system

Run: python setup_youtube_api.py
"""

import os
import sys
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()

# Configure SSL certificates for all HTTPS requests (your SSL fix)
ssl_cert = os.getenv("SSL_CERT_FILE")
requests_ca = os.getenv("REQUESTS_CA_BUNDLE")

if ssl_cert and requests_ca:
    os.environ['REQUESTS_CA_BUNDLE'] = requests_ca
    os.environ['SSL_CERT_FILE'] = ssl_cert
    print(f"🔒 SSL certificates configured: {ssl_cert}")
else:
    print("⚠️ SSL certificates not configured, disabling SSL verification")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def print_setup_instructions():
    """Print step-by-step YouTube API setup instructions"""
    print("🎬 YouTube Data API v3 Setup Instructions")
    print("=" * 60)
    print()
    print("📋 Step 1: Go to Google Cloud Console")
    print("   🌐 Visit: https://console.cloud.google.com/")
    print()
    print("📋 Step 2: Create or Select Project")
    print("   • Click on project dropdown (top-left)")
    print("   • Create a new project or select existing one")
    print("   • Project name: 'YouTube ML Monitor' (or similar)")
    print()
    print("📋 Step 3: Enable YouTube Data API v3")
    print("   • Go to: APIs & Services > Library")
    print("   • Search for: 'YouTube Data API v3'")
    print("   • Click on it and press 'Enable'")
    print()
    print("📋 Step 4: Create API Credentials")
    print("   • Go to: APIs & Services > Credentials")
    print("   • Click: '+ CREATE CREDENTIALS'")
    print("   • Choose: 'API Key'")
    print("   • Copy the generated API key")
    print()
    print("📋 Step 5: Restrict API Key (Optional but Recommended)")
    print("   • Click on your API key to edit")
    print("   • Under 'API restrictions':")
    print("     - Select 'Restrict key'")
    print("     - Choose 'YouTube Data API v3'")
    print("   • Save changes")
    print()
    print("📋 Step 6: Add to Environment")
    print("   • Add to your .env file:")
    print("     YOUTUBE_API_KEY=your_api_key_here")
    print()
    print("💡 Quota Information:")
    print("   • Free tier: 10,000 units/day")
    print("   • Video search: ~5 units")
    print("   • Video details: ~1 unit")
    print("   • This allows ~1,000 video checks/day")
    print()

def test_youtube_api():
    """Test YouTube API key"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        print("❌ YOUTUBE_API_KEY not found in environment")
        print("   Please add it to your .env file and try again")
        return False
    
    print("🔍 Testing YouTube API key...")
    print(f"   Key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test with StatQuest channel
    channel_id = "UCtYLUTtgS3k1Fg4y5tAhLbw"  # StatQuest
    
    try:
        # Test API with a simple channel info request
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'key': api_key,
            'id': channel_id,
            'part': 'snippet,statistics'
        }
        
        # Create session with SSL handling (your SSL fix)
        session = requests.Session()
        session.verify = False  # Disable SSL verification for API testing
        
        response = session.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data and data['items']:
                channel_info = data['items'][0]
                snippet = channel_info['snippet']
                stats = channel_info['statistics']
                
                print("✅ YouTube API test successful!")
                print(f"   📺 Channel: {snippet['title']}")
                print(f"   📊 Subscribers: {int(stats.get('subscriberCount', 0)):,}")
                print(f"   🎥 Total Videos: {int(stats.get('videoCount', 0)):,}")
                print(f"   👀 Total Views: {int(stats.get('viewCount', 0)):,}")
                return True
            else:
                print("❌ API returned empty results")
                return False
        else:
            print(f"❌ API request failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"   Error: {error_data['error'].get('message', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_recent_videos():
    """Test getting recent videos from StatQuest"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        print("❌ YOUTUBE_API_KEY not found")
        return False
    
    print("\n🔍 Testing recent video detection...")
    
    try:
        from datetime import datetime, timedelta
        
        # Get videos from last 30 days
        published_after = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
        channel_id = "UCtYLUTtgS3k1Fg4y5tAhLbw"  # StatQuest
        
        # Search for recent videos
        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            'key': api_key,
            'channelId': channel_id,
            'part': 'id,snippet',
            'order': 'date',
            'type': 'video',
            'publishedAfter': published_after,
            'maxResults': 5
        }
        
        # Create session with SSL handling (your SSL fix)
        session = requests.Session()
        session.verify = False  # Disable SSL verification for API testing
        
        response = session.get(search_url, params=search_params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            videos = data.get('items', [])
            
            print(f"✅ Found {len(videos)} recent videos (last 30 days):")
            
            for i, video in enumerate(videos, 1):
                snippet = video['snippet']
                video_id = video['id']['videoId']
                title = snippet['title']
                published = snippet['publishedAt']
                
                print(f"   {i}. {title[:60]}...")
                print(f"      📅 Published: {published}")
                print(f"      🔗 https://www.youtube.com/watch?v={video_id}")
                print()
            
            return len(videos) > 0
        else:
            print(f"❌ Recent video search failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Recent video test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 YouTube API Setup and Testing Tool")
    print("=" * 50)
    
    # Check if API key exists
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        print("\n📋 YouTube API Key Setup Required")
        print_setup_instructions()
        print("\n💡 After setting up your API key:")
        print("   1. Add YOUTUBE_API_KEY=your_key to .env file")
        print("   2. Run this script again to test")
        print("   3. Then run: python youtube_realtime_monitor.py --test")
        return
    
    # Test API key
    print("\n🧪 Testing API Configuration...")
    api_success = test_youtube_api()
    
    if api_success:
        video_success = test_recent_videos()
        
        if video_success:
            print("\n🎉 All tests passed! Your YouTube API setup is working.")
            print("\n🚀 Next Steps:")
            print("   1. Install additional dependencies:")
            print("      pip install -r requirements_realtime.txt")
            print("   2. Test the real-time monitor:")
            print("      python youtube_realtime_monitor.py --test")
            print("   3. Start continuous monitoring:")
            print("      python youtube_realtime_monitor.py")
        else:
            print("\n⚠️ API key works but video detection failed")
            print("   This might be due to no recent StatQuest videos")
            print("   You can still proceed with the setup")
    else:
        print("\n❌ API setup incomplete or invalid")
        print("   Please check your YOUTUBE_API_KEY in .env file")

if __name__ == "__main__":
    main()

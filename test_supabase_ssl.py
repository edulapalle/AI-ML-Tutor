#!/usr/bin/env python3
"""Test Supabase SSL connection for Railway debugging"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_ssl():
    """Test Supabase connection with SSL diagnostics"""
    
    print("🔍 Testing Supabase SSL Connection")
    print("=" * 50)
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"📍 Supabase URL: {supabase_url[:30] + '...' if supabase_url else 'Not set'}")
    print(f"🔑 Supabase Key: {'Set' if supabase_key else 'Not set'}")
    print()
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    try:
        print("🔧 Testing basic imports...")
        from supabase import create_client, Client
        print("✅ Supabase import successful")
        
        print("\n🔐 Testing SSL certificate access...")
        import ssl
        import certifi
        
        # Check if certificates are accessible
        cert_path = certifi.where()
        print(f"📜 Certificate path: {cert_path}")
        print(f"📜 Certificate exists: {os.path.exists(cert_path)}")
        
        if os.path.exists(cert_path):
            print(f"📜 Certificate size: {os.path.getsize(cert_path)} bytes")
        
        print("\n🚀 Testing Supabase client creation...")
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        print("\n🧪 Testing simple database query...")
        # Try a simple query that should work with any Supabase setup
        result = client.table("users").select("count").execute()
        print("✅ Database query successful")
        print(f"📊 Query result: {result}")
        
        print("\n✨ All tests passed!")
        
    except FileNotFoundError as e:
        print(f"❌ File not found error: {e}")
        print("   This is likely the cause of the Railway issue")
        print("   Missing: SSL certificates or system files")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Missing dependency")
        
    except Exception as e:
        print(f"❌ General error: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Additional SSL diagnostics
        if "ssl" in str(e).lower() or "certificate" in str(e).lower():
            print("\n🔍 SSL-related error detected!")
            print("   Possible solutions:")
            print("   1. Install ca-certificates in Railway container")
            print("   2. Use REQUESTS_CA_BUNDLE environment variable")
            print("   3. Configure SSL_CERT_FILE")

if __name__ == "__main__":
    test_supabase_ssl()

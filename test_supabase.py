#!/usr/bin/env python3
"""
Test script to verify Supabase configuration
Run this script to check if your Supabase setup is working correctly.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_config():
    """Test Supabase configuration"""
    print("🔍 Testing Supabase Configuration...")
    print("=" * 50)
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Not set'}")
    print(f"SUPABASE_ANON_KEY: {'✅ Set' if supabase_key else '❌ Not set'}")
    
    if not supabase_url or not supabase_key:
        print("\n❌ Supabase configuration is incomplete!")
        print("Please set the following environment variables in your .env file:")
        print("   SUPABASE_URL=https://your-project-id.supabase.co")
        print("   SUPABASE_ANON_KEY=your_supabase_anon_key_here")
        return False
    
    # Test Supabase client creation
    try:
        from supabase import create_client, Client
        
        print("\n🔧 Testing Supabase client creation...")
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully!")
        
        # Test basic connection
        print("\n🔗 Testing Supabase connection...")
        try:
            # Try to access the users table (this will fail if table doesn't exist, but connection should work)
            result = supabase.table("users").select("count", count="exact").execute()
            print("✅ Supabase connection successful!")
            print(f"   Users table accessible: {result.count if hasattr(result, 'count') else 'Unknown'}")
        except Exception as e:
            if "relation \"users\" does not exist" in str(e):
                print("⚠️  Supabase connection successful, but users table doesn't exist yet.")
                print("   Please run the database_schema.sql script in your Supabase project.")
            else:
                print(f"❌ Supabase connection failed: {e}")
                return False
        
        return True
        
    except ImportError:
        print("❌ Supabase package not installed!")
        print("Please install it with: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Error creating Supabase client: {e}")
        return False

def test_environment_variables():
    """Test all required environment variables"""
    print("\n🔍 Testing Environment Variables...")
    print("=" * 50)
    
    required_vars = [
        "OPENAI_API_KEY",
        "SUPABASE_URL", 
        "SUPABASE_ANON_KEY",
        "JWT_SECRET_KEY"
    ]
    
    optional_vars = [
        "MILVUS_URI",
        "MILVUS_TOKEN",
        "COLLECTION_NAME",
        "ENABLE_RERANKING",
        "RERANKING_MODEL",
        "HOST",
        "PORT"
    ]
    
    print("Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ Set" if value else "❌ Not set"
        print(f"   {var}: {status}")
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        status = "✅ Set" if value else "⚠️  Not set (using default)"
        print(f"   {var}: {status}")

if __name__ == "__main__":
    print("🚀 AI Study Assistant - Configuration Test")
    print("=" * 50)
    
    # Test environment variables
    test_environment_variables()
    
    # Test Supabase configuration
    supabase_ok = test_supabase_config()
    
    print("\n" + "=" * 50)
    if supabase_ok:
        print("✅ All tests passed! Your configuration looks good.")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        print("\n📝 Next steps:")
        print("1. Create a .env file: cp env.example .env")
        print("2. Add your Supabase credentials to .env")
        print("3. Run the database_schema.sql in your Supabase project")
        print("4. Try running this test again")


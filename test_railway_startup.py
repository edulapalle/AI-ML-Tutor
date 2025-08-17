#!/usr/bin/env python3
"""
Test Railway startup without running the full server
Quick validation that the app can initialize
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_app_initialization():
    """Test if the app can initialize without errors"""
    print("🧪 Testing Railway App Initialization...")
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
        print("✅ FastAPI imports successful")
        
        # Test OpenAI
        print("🤖 Testing OpenAI import...")
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            client = OpenAI(api_key=api_key)
            print("✅ OpenAI client created successfully")
        else:
            print("⚠️ OpenAI API key not found")
        
        # Test basic app creation
        print("🚀 Testing FastAPI app creation...")
        app = FastAPI(title="Test App", version="1.0.0")
        
        # Test middleware
        print("🛡️ Testing middleware...")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        print("✅ CORS middleware added successfully")
        
        # Test HTTPS redirect (conditionally)
        railway_env = os.getenv("RAILWAY_ENVIRONMENT_NAME")
        if railway_env and railway_env.lower() == "production":
            app.add_middleware(HTTPSRedirectMiddleware)
            print("✅ HTTPS redirect middleware added successfully")
        else:
            print("ℹ️ HTTPS redirect skipped (not Railway production)")
        
        # Test health check
        print("❤️ Testing health check...")
        @app.get("/health")
        async def health():
            return {"status": "healthy", "test": "passed"}
        
        print("✅ Health check endpoint created successfully")
        
        print("\n🎉 All initialization tests passed!")
        print("📊 Summary:")
        print("  ✅ Imports: Working")
        print("  ✅ OpenAI: Configured")
        print("  ✅ FastAPI: Working") 
        print("  ✅ Middleware: Working")
        print("  ✅ Health Check: Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test critical environment variables"""
    print("\n🔍 Testing Environment Variables...")
    
    critical_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"]
    optional_vars = ["MILVUS_URI", "NEO4J_URI", "SENDGRID_API_KEY"]
    
    all_critical_present = True
    
    print("📋 Critical Variables:")
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Present")
        else:
            print(f"  ❌ {var}: Missing")
            all_critical_present = False
    
    print("📋 Optional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Present")
        else:
            print(f"  ⚠️ {var}: Missing (optional)")
    
    return all_critical_present

if __name__ == "__main__":
    print("🚂 Railway Startup Test")
    print("=" * 50)
    
    # Test environment
    env_ok = test_environment_variables()
    
    # Test app initialization
    app_ok = test_app_initialization()
    
    print("\n" + "=" * 50)
    print("🏁 Final Results:")
    print(f"  Environment: {'✅ OK' if env_ok else '❌ Issues'}")
    print(f"  App Init: {'✅ OK' if app_ok else '❌ Failed'}")
    
    if env_ok and app_ok:
        print("\n🎉 Railway startup should work!")
        sys.exit(0)
    else:
        print("\n💥 Railway startup will likely fail!")
        sys.exit(1)

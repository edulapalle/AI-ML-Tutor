#!/usr/bin/env python3
"""
Railway debugging script - helps diagnose deployment issues
Run this to check if all services are working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API access",
        "PORT": "Railway port configuration"
    }
    
    optional_vars = {
        "SUPABASE_URL": "Database connection",
        "MILVUS_URI": "Vector database",
        "NEO4J_URI": "Knowledge graph",
        "SENDGRID_API_KEY": "Email service"
    }
    
    print("\n📋 Required Variables:")
    all_required_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Present ({description})")
        else:
            print(f"❌ {var}: Missing ({description})")
            all_required_present = False
    
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Present ({description})")
        else:
            print(f"⚠️ {var}: Missing ({description}) - feature will be disabled")
    
    return all_required_present

def test_openai():
    """Test OpenAI connection"""
    print("\n🤖 Testing OpenAI Connection...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'OpenAI connection test successful'"}],
            max_tokens=10
        )
        
        print("✅ OpenAI connection successful!")
        print(f"📝 Test response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

def test_imports():
    """Test if all required packages can be imported"""
    print("\n📦 Testing Package Imports...")
    
    packages = {
        "fastapi": "Web framework",
        "openai": "OpenAI API client",
        "jinja2": "Template engine",
        "httpx": "HTTP client",
        "python-dotenv": "Environment variables"
    }
    
    failed_imports = []
    
    for package, description in packages.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}: Available ({description})")
        except ImportError as e:
            print(f"❌ {package}: Failed to import ({description}) - {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def create_simple_health_check():
    """Create a simple health check server for testing"""
    print("\n🚑 Creating Simple Health Check...")
    
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        import uvicorn
        
        app = FastAPI(title="Railway Health Check")
        
        @app.get("/")
        @app.get("/health")
        async def health():
            return JSONResponse({
                "status": "healthy",
                "message": "Railway deployment is working!",
                "environment_check": check_environment(),
                "openai_available": os.getenv("OPENAI_API_KEY") is not None
            })
        
        print("✅ Health check server created")
        port = int(os.getenv("PORT", 8000))
        print(f"🌐 Starting server on port {port}")
        
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        print(f"❌ Failed to create health check server: {e}")

def main():
    """Main debugging function"""
    print("🚂 Railway Deployment Debugging")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    # Test imports
    imports_ok = test_imports()
    
    # Test OpenAI if available
    openai_ok = test_openai() if os.getenv("OPENAI_API_KEY") else False
    
    print("\n📊 Summary:")
    print(f"Environment Variables: {'✅ OK' if env_ok else '❌ Missing required vars'}")
    print(f"Package Imports: {'✅ OK' if imports_ok else '❌ Missing packages'}")
    print(f"OpenAI Connection: {'✅ OK' if openai_ok else '❌ Failed or missing key'}")
    
    if not env_ok:
        print("\n🔧 Fix: Add missing environment variables in Railway dashboard")
    
    if not imports_ok:
        print("\n🔧 Fix: Check requirements.txt and Railway build logs")
    
    if not openai_ok and os.getenv("OPENAI_API_KEY"):
        print("\n🔧 Fix: Verify OPENAI_API_KEY is valid and has credits")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        print("\n🚀 Starting simple health check server...")
        create_simple_health_check()

if __name__ == "__main__":
    main()

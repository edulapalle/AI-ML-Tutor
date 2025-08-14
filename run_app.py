#!/usr/bin/env python3
"""
Startup script for the unified AI/ML Educational Platform
"""

import os
import uvicorn
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        "OPENAI_API_KEY",
        "MILVUS_URI", 
        "MILVUS_TOKEN",
        "NEO4J_URI",
        "NEO4J_PASSWORD",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "JWT_SECRET_KEY"
    ]
    
    missing = []
    configured = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
        else:
            configured.append(var)
    
    print("🔧 Environment Configuration Check:")
    print("=" * 40)
    
    for var in configured:
        print(f"✅ {var}")
    
    if missing:
        print("\n❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease check your .env file!")
        return False
    
    print(f"\n✅ All {len(required_vars)} environment variables configured")
    return True

def print_system_info():
    """Print system information and endpoints"""
    print("\n🚀 AI/ML Educational Platform")
    print("=" * 50)
    print("🎓 Advanced RAG-powered AI tutoring with authentication")
    print("🔗 Integrates: OpenAI + Milvus + Neo4j + Supabase")
    print("\n📍 Available Endpoints:")
    print("   🌐 Dashboard: http://localhost:8000/")
    print("   🔐 Login: http://localhost:8000/login")
    print("   📝 Register: http://localhost:8000/register")
    print("   📚 API Docs: http://localhost:8000/docs")
    print("   ❤️ Health: http://localhost:8000/api/health")
    print("\n💬 Main Features:")
    print("   • 🤖 Intelligent ML/AI Chat with Guardrails")
    print("   • 🎯 Learning Path Suggestions (Neo4j)")
    print("   • ⭐ Content Bookmarking (Supabase)")
    print("   • 👤 User Authentication & Profiles")
    print("   • 📊 Real-time System Status")
    print("   • 🔍 Advanced RAG with Reranking")
    print("\n" + "=" * 50)

def main():
    """Start the unified application"""
    # Set SSL certificates for the environment
    os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
    os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'
    
    print_system_info()
    
    if not check_environment():
        print("\n🛑 Cannot start application due to missing configuration.")
        print("📋 Please ensure your .env file contains all required variables.")
        return
    
    print("\n🌟 Starting unified application server...")
    print("⏳ This may take a moment to initialize all connections...")
    
    # Start the server
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start application: {e}")

if __name__ == "__main__":
    main()

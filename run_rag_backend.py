#!/usr/bin/env python3
"""
Startup script for RAG Backend API
Checks connections and starts the server
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
        "SUPABASE_ANON_KEY"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease check your .env file!")
        return False
    
    print("✅ All environment variables configured")
    return True

def main():
    """Start the RAG Backend API server"""
    print("🚀 Starting RAG Backend API")
    print("=" * 40)
    
    # Set SSL certificates for the environment
    os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
    os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'
    
    if not check_environment():
        return
    
    print("\n🌐 Starting FastAPI server...")
    print("📍 API docs: http://localhost:8000/docs")
    print("🧪 Test script: python test_rag_backend.py")
    print("\n" + "=" * 40)
    
    # Start the server
    uvicorn.run(
        "rag_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()

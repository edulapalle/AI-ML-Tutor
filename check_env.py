#!/usr/bin/env python3
"""
Quick environment configuration checker
"""

import os
from dotenv import load_dotenv

def check_environment():
    """Check environment configuration"""
    load_dotenv()
    
    print("🔧 Environment Configuration Check")
    print("=" * 40)
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API access",
        "MILVUS_URI": "Milvus/Zilliz Cloud endpoint", 
        "MILVUS_TOKEN": "Milvus/Zilliz Cloud token",
        "NEO4J_URI": "Neo4j Aura connection",
        "NEO4J_PASSWORD": "Neo4j Aura password",
        "SUPABASE_URL": "Supabase project URL",
        "SUPABASE_ANON_KEY": "Supabase anonymous key",
        "JWT_SECRET_KEY": "JWT token signing"
    }
    
    configured = []
    missing = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            configured.append((var, description, value[:20] + "..." if len(value) > 20 else value))
        else:
            missing.append((var, description))
    
    # Show configured
    print("\n✅ Configured variables:")
    for var, desc, val in configured:
        print(f"   {var}: {val}")
    
    # Show missing
    if missing:
        print("\n❌ Missing variables:")
        for var, desc in missing:
            print(f"   {var}: {desc}")
    else:
        print("\n🎉 All environment variables are configured!")
    
    # Test Milvus specifically
    if os.getenv("MILVUS_URI") and os.getenv("MILVUS_TOKEN"):
        print(f"\n🔍 Milvus Configuration:")
        milvus_uri = os.getenv("MILVUS_URI")
        print(f"   URI: {milvus_uri}")
        print(f"   URI Type: {'Zilliz Cloud' if 'zilliz.com' in milvus_uri else 'Local/Other'}")
        
        # Test connection
        try:
            from pymilvus import connections
            print("   Testing connection...")
            connections.connect(
                alias="test_connection",
                uri=milvus_uri,
                token=os.getenv("MILVUS_TOKEN")
            )
            
            from pymilvus import utility
            collections = utility.list_collections(using="test_connection")
            print(f"   ✅ Connection successful! Collections: {collections}")
            connections.disconnect("test_connection")
            
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    
    return len(missing) == 0

if __name__ == "__main__":
    check_environment()

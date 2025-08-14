#!/usr/bin/env python3
"""
Debug Milvus connection issues
"""

import os
from dotenv import load_dotenv

def debug_milvus_connection():
    """Debug Milvus connection step by step"""
    load_dotenv()
    
    print("🔍 Debugging Milvus Connection")
    print("=" * 40)
    
    milvus_uri = os.getenv('MILVUS_URI')
    milvus_token = os.getenv('MILVUS_TOKEN')
    
    print(f"URI: {milvus_uri}")
    print(f"Token: {milvus_token[:20]}..." if milvus_token else "Token: None")
    
    # Set SSL certificates like other scripts
    os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
    os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'
    
    # Try basic network connectivity
    import socket
    import urllib.parse
    
    parsed = urllib.parse.urlparse(milvus_uri)
    host = parsed.hostname
    port = parsed.port or 443
    
    print(f"\n🌐 Testing network connectivity to {host}:{port}...")
    
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        print("✅ Network connectivity OK")
    except Exception as e:
        print(f"❌ Network connectivity failed: {e}")
        return False
    
    # Try importing pymilvus
    print("\n📦 Testing pymilvus import...")
    try:
        from pymilvus import connections, Collection, utility
        print("✅ pymilvus imported successfully")
    except Exception as e:
        print(f"❌ pymilvus import failed: {e}")
        return False
    
    # Try different connection methods
    print("\n🔗 Testing Milvus connection methods...")
    
    # Method 1: Standard connection
    print("Method 1: Standard connection")
    try:
        connections.connect(
            alias="test1",
            uri=milvus_uri,
            token=milvus_token
        )
        
        # Test listing collections
        collections_list = utility.list_collections(using="test1")
        print(f"✅ Method 1 successful! Collections: {collections_list}")
        connections.disconnect("test1")
        return True
        
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Method 2: With explicit timeout
    print("\nMethod 2: With explicit timeout")
    try:
        connections.connect(
            alias="test2",
            uri=milvus_uri,
            token=milvus_token,
            timeout=30
        )
        
        collections_list = utility.list_collections(using="test2")
        print(f"✅ Method 2 successful! Collections: {collections_list}")
        connections.disconnect("test2")
        return True
        
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Method 3: Check if it's a token/auth issue
    print("\nMethod 3: Testing basic connection without operations")
    try:
        connections.connect(
            alias="test3",
            uri=milvus_uri,
            token=milvus_token
        )
        print("✅ Method 3: Basic connection successful")
        connections.disconnect("test3")
        return True
        
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    return False

if __name__ == "__main__":
    debug_milvus_connection()

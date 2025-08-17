#!/usr/bin/env python3
"""
Test OpenAI client initialization on Railway
Debug the "No such file or directory" error
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_openai_client():
    """Test OpenAI client initialization with detailed debugging"""
    print("🤖 Testing OpenAI Client Initialization")
    print("=" * 50)
    
    # Check environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"📋 Environment Check:")
    print(f"   API Key Present: {bool(api_key)}")
    if api_key:
        print(f"   API Key Format: {api_key[:10]}... (length: {len(api_key)})")
        print(f"   Starts with 'sk-': {api_key.startswith('sk-') if api_key else False}")
    else:
        print("   ❌ OPENAI_API_KEY not found in environment")
        return False
    
    # Test import
    print(f"\n📦 Testing OpenAI Import:")
    try:
        from openai import OpenAI
        print("   ✅ OpenAI module imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import OpenAI: {e}")
        return False
    
    # Test client creation
    print(f"\n🔧 Testing Client Creation:")
    try:
        client = OpenAI(api_key=api_key)
        print("   ✅ OpenAI client created successfully")
    except FileNotFoundError as e:
        print(f"   ❌ File error during client creation: {e}")
        print("   💡 This might be SSL certificate or temp file issues")
        return False
    except Exception as e:
        print(f"   ❌ Error creating client: {e}")
        print(f"   📝 Error type: {type(e).__name__}")
        return False
    
    # Test simple API call (optional)
    print(f"\n🌐 Testing API Connection:")
    try:
        # Simple test that doesn't use much quota
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=5
        )
        print("   ✅ API call successful!")
        print(f"   📝 Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"   ⚠️ API call failed: {e}")
        print("   💡 Client created but API call failed - check credits/connectivity")
        return False

def test_ssl_certificates():
    """Test SSL certificate access"""
    print(f"\n🔒 Testing SSL Configuration:")
    
    import ssl
    import certifi
    
    try:
        # Check certifi certificates
        cert_path = certifi.where()
        print(f"   📄 Certifi path: {cert_path}")
        print(f"   📄 Cert file exists: {os.path.exists(cert_path)}")
        
        # Test SSL context
        context = ssl.create_default_context()
        print("   ✅ SSL context created successfully")
        
    except Exception as e:
        print(f"   ❌ SSL configuration error: {e}")

def test_temp_directory():
    """Test temporary directory access"""
    print(f"\n📁 Testing Temporary Directory Access:")
    
    import tempfile
    
    try:
        # Test temp directory
        temp_dir = tempfile.gettempdir()
        print(f"   📂 Temp directory: {temp_dir}")
        print(f"   📂 Temp dir exists: {os.path.exists(temp_dir)}")
        print(f"   📂 Temp dir writable: {os.access(temp_dir, os.W_OK)}")
        
        # Test creating temp file
        with tempfile.NamedTemporaryFile() as tmp:
            print(f"   ✅ Temp file created: {tmp.name}")
            
    except Exception as e:
        print(f"   ❌ Temp directory error: {e}")

def main():
    """Main test function"""
    print("🚂 Railway OpenAI Debugging")
    print("Investigating: 'OpenAI client failed to initialize: [Errno 2] No such file or directory'")
    
    # Run all tests
    success = test_openai_client()
    test_ssl_certificates()
    test_temp_directory()
    
    print("\n" + "=" * 50)
    print("📊 DIAGNOSIS:")
    
    if success:
        print("✅ OpenAI client working correctly!")
        print("💡 The error might be environment-specific or intermittent")
    else:
        print("❌ OpenAI client has issues")
        print("🔧 Possible fixes:")
        print("   1. Check OPENAI_API_KEY in Railway environment variables")
        print("   2. Verify API key format (should start with 'sk-')")
        print("   3. Check Railway SSL/certificate configuration")
        print("   4. Try updating OpenAI client version")

if __name__ == "__main__":
    main()

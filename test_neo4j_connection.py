#!/usr/bin/env python3
"""
Simple Neo4j Aura Connection Test
Just one functionality: connect to Neo4j Aura instance
Uses SSL certificate solution for corporate environments
"""

import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_neo4j_connection():
    """Test connection to Neo4j Aura instance using SSL certificate solution"""
    
    # Get Neo4j connection details from .env
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    # Check if environment variables are set
    if not uri:
        print("❌ NEO4J_URI not found in .env file")
        return False
    
    if not username:
        print("❌ NEO4J_USERNAME not found in .env file")
        return False
    
    if not password:
        print("❌ NEO4J_PASSWORD not found in .env file")
        return False
    
    print("🔍 Testing Neo4j Aura Connection (SSL Certificate Solution)")
    print("=" * 60)
    print(f"Original URI: {uri}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    # Check if SSL certificate environment variables are set
    ssl_cert = os.getenv("SSL_CERT_FILE")
    requests_ca = os.getenv("REQUESTS_CA_BUNDLE")
    
    if ssl_cert:
        print(f"SSL_CERT_FILE: {ssl_cert}")
    else:
        print("⚠️  SSL_CERT_FILE not set - may cause connection issues")
        
    if requests_ca:
        print(f"REQUESTS_CA_BUNDLE: {requests_ca}")
    else:
        print("⚠️  REQUESTS_CA_BUNDLE not set - may cause connection issues")
    
    print("=" * 60)
    
    try:
        # Convert neo4j+s:// to bolt+s:// for direct connection (no routing)
        if uri.startswith("neo4j+s://"):
            direct_uri = uri.replace("neo4j+s://", "bolt+s://")
            print(f"🔄 Converting to direct connection: {direct_uri}")
        else:
            direct_uri = uri
            print(f"🔄 Using URI as-is: {direct_uri}")
        
        # Create driver with direct connection
        print("📡 Creating Neo4j driver with direct connection...")
        driver = GraphDatabase.driver(direct_uri, auth=(username, password))
        
        # Test connectivity
        print("🔌 Testing connectivity...")
        driver.verify_connectivity()
        print("✅ Connectivity verified!")
        
        # Test connection with a simple query
        print("🔌 Testing connection with simple query...")
        with driver.session(database="neo4j") as session:
            result = session.run("RETURN 'Hello from Neo4j!' as message")
            message = result.single()["message"]
            print(f"✅ Connection successful!")
            print(f"   Response: {message}")
            
            # Get database info
            print("\n📊 Getting database information...")
            try:
                result = session.run("CALL dbms.components() YIELD name, versions, edition")
                components = list(result)
                print("   Database components:")
                for comp in components:
                    name = comp["name"]
                    version = comp["versions"][0] if comp["versions"] else "unknown"
                    edition = comp["edition"]
                    print(f"     - {name}: {version} ({edition})")
            except Exception as e:
                print(f"   ⚠️ Could not get component info: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
        
    finally:
        if 'driver' in locals():
            driver.close()
            print("🔌 Driver connection closed")

if __name__ == "__main__":
    success = test_neo4j_connection()
    
    if success:
        print("\n🎉 Neo4j Aura connection test PASSED!")
        print("\n💡 SSL Certificate Solution Working:")
        print("   - Using bolt+s:// for direct connection")
        print("   - SSL certificates properly configured")
        print("   - No routing issues encountered")
    else:
        print("\n💥 Neo4j Aura connection test FAILED!")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check if your Neo4j Aura instance is running")
        print("   2. Verify your .env file has correct credentials")
        print("   3. Set SSL certificate environment variables:")
        print("      export SSL_CERT_FILE=/path/to/corp_root_ca.pem")
        print("      export REQUESTS_CA_BUNDLE=/path/to/corp_root_ca.pem")
        print("   4. Try accessing Neo4j Browser in your Aura console")
        print("   5. Check if you need to use bolt+s:// instead of neo4j+s://")

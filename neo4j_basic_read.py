#!/usr/bin/env python3
"""
Basic Neo4j Aura Connection and Read Script
Connects to Neo4j Aura instance and reads basic database contents
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

def connect_to_neo4j():
    """Connect to Neo4j Aura instance using SSL certificate solution"""
    
    # Get Neo4j connection details from .env
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    # Check if environment variables are set
    if not uri:
        print("❌ NEO4J_URI not found in .env file")
        return None
    
    if not username:
        print("❌ NEO4J_USERNAME not found in .env file")
        return None
    
    if not password:
        print("❌ NEO4J_PASSWORD not found in .env file")
        return None
    
    print("🔍 Connecting to Neo4j Aura Instance")
    print("=" * 60)
    print(f"Original URI: {uri}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    # Check SSL certificate environment variables
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
        # Convert neo4j+s:// to bolt+s:// for direct connection
        if uri.startswith("neo4j+s://"):
            direct_uri = uri.replace("neo4j+s://", "bolt+s://")
            print(f"🔄 Converting to direct connection: {direct_uri}")
        else:
            direct_uri = uri
            print(f"🔄 Using URI as-is: {direct_uri}")
        
        # Create driver with direct connection
        print("📡 Creating Neo4j driver...")
        driver = GraphDatabase.driver(direct_uri, auth=(username, password))
        
        # Test connectivity
        print("🔌 Testing connectivity...")
        driver.verify_connectivity()
        print("✅ Connectivity verified!")
        
        return driver
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def read_database_contents(driver):
    """Read basic contents from the Neo4j database"""
    
    print("\n📖 Reading Database Contents")
    print("=" * 60)
    
    try:
        with driver.session(database="neo4j") as session:
            
            # 1. Get database information
            print("📊 Database Information:")
            try:
                result = session.run("CALL dbms.components() YIELD name, versions, edition")
                components = list(result)
                for comp in components:
                    name = comp["name"]
                    version = comp["versions"][0] if comp["versions"] else "unknown"
                    edition = comp["edition"]
                    print(f"   - {name}: {version} ({edition})")
            except Exception as e:
                print(f"   ⚠️ Could not get component info: {e}")
            
            print()
            
            # 2. Count all nodes by type
            print("🔢 Node Counts by Type:")
            try:
                result = session.run("""
                    MATCH (n)
                    RETURN labels(n) as labels, count(n) as count
                    ORDER BY count DESC
                """)
                node_counts = list(result)
                
                if node_counts:
                    for record in node_counts:
                        labels = record["labels"]
                        count = record["count"]
                        label_str = ":".join(labels) if labels else "unlabeled"
                        print(f"   - {label_str}: {count} nodes")
                else:
                    print("   - No nodes found in database")
                    
            except Exception as e:
                print(f"   ⚠️ Could not count nodes: {e}")
            
            print()
            
            # 3. Count all relationships by type
            print("🔗 Relationship Counts by Type:")
            try:
                result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as type, count(r) as count
                    ORDER BY count DESC
                """)
                rel_counts = list(result)
                
                if rel_counts:
                    for record in rel_counts:
                        rel_type = record["type"]
                        count = record["count"]
                        print(f"   - {rel_type}: {count} relationships")
                else:
                    print("   - No relationships found in database")
                    
            except Exception as e:
                print(f"   ⚠️ Could not count relationships: {e}")
            
            print()
            
            # 4. Show sample nodes (first 5 of each type)
            print("📋 Sample Nodes (First 5 of each type):")
            try:
                result = session.run("""
                    MATCH (n)
                    RETURN labels(n) as labels, n.name as name, n.title as title, n.concept as concept
                    LIMIT 20
                """)
                sample_nodes = list(result)
                
                if sample_nodes:
                    for record in sample_nodes:
                        labels = record["labels"]
                        name = record["name"] or record["title"] or record["concept"] or "unnamed"
                        label_str = ":".join(labels) if labels else "unlabeled"
                        print(f"   - [{label_str}] {name}")
                else:
                    print("   - No nodes found to display")
                    
            except Exception as e:
                print(f"   ⚠️ Could not get sample nodes: {e}")
            
            print()
            
            # 5. Show sample relationships
            print("🔗 Sample Relationships (First 10):")
            try:
                result = session.run("""
                    MATCH (a)-[r]->(b)
                    RETURN labels(a) as from_labels, a.name as from_name, 
                           type(r) as relationship, 
                           labels(b) as to_labels, b.name as to_name
                    LIMIT 10
                """)
                sample_rels = list(result)
                
                if sample_rels:
                    for record in sample_rels:
                        from_labels = ":".join(record["from_labels"]) if record["from_labels"] else "unlabeled"
                        from_name = record["from_name"] or "unnamed"
                        rel_type = record["relationship"]
                        to_labels = ":".join(record["to_labels"]) if record["to_labels"] else "unlabeled"
                        to_name = record["to_name"] or "unnamed"
                        
                        print(f"   - [{from_labels}] {from_name} --{rel_type}--> [{to_labels}] {to_name}")
                else:
                    print("   - No relationships found to display")
                    
            except Exception as e:
                print(f"   ⚠️ Could not get sample relationships: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return False

def main():
    """Main function to connect and read Neo4j database"""
    
    print("🚀 Neo4j Aura Basic Read Script")
    print("=" * 60)
    
    # Connect to Neo4j
    driver = connect_to_neo4j()
    if not driver:
        print("❌ Failed to connect to Neo4j. Exiting.")
        return
    
    try:
        # Read database contents
        success = read_database_contents(driver)
        
        if success:
            print("\n🎉 Database read completed successfully!")
            print("\n💡 Next Steps:")
            print("   1. If database is empty, we can create some test data")
            print("   2. If data exists, we can analyze the structure")
            print("   3. We can build ML concept relationships")
        else:
            print("\n⚠️ Database read completed with some issues")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
    finally:
        # Always close the driver
        if driver:
            driver.close()
            print("🔌 Driver connection closed")

if __name__ == "__main__":
    main()

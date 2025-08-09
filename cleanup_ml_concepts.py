#!/usr/bin/env python3
"""
Cleanup script for ML concepts collection
Use this if the collection gets into a bad state
"""

import os
import sys
from dotenv import load_dotenv
from pymilvus import connections, utility
from rag_system import get_rag_system

def main():
    """Clean up and recreate ML concepts collection"""
    print("🧹 ML Concepts Collection Cleanup Script")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['MILVUS_URI', 'MILVUS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    try:
        # Connect to Milvus
        milvus_uri = os.getenv('MILVUS_URI')
        milvus_token = os.getenv('MILVUS_TOKEN')
        
        connections.connect(
            alias="default",
            uri=milvus_uri,
            token=milvus_token
        )
        
        print("✅ Connected to Zilliz Cloud")
        
        collection_name = "ml_concepts"
        
        # Check if collection exists
        if utility.has_collection(collection_name):
            print(f"🔍 Found existing collection: {collection_name}")
            
            response = input("Do you want to delete and recreate it? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                print(f"🗑️ Dropping collection: {collection_name}")
                utility.drop_collection(collection_name)
                print("✅ Collection dropped successfully")
            else:
                print("✅ Operation cancelled")
                return
        else:
            print(f"ℹ️ Collection {collection_name} does not exist")
        
        print("\n🔄 Now run the population script:")
        print("python populate_ml_concepts.py")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

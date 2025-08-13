#!/usr/bin/env python3
"""
Create a new MilvusDB collection for rich educational content
This creates a separate collection optimized for the ml_analogies.jsonl schema
"""

import os
import json
import sys
from dotenv import load_dotenv
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

# Fix SSL certificates for Python
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'

# Load environment variables
load_dotenv()

def connect_to_milvus():
    """Connect to Zilliz Cloud"""
    try:
        # Get Milvus connection details
        milvus_uri = os.getenv('MILVUS_URI')
        milvus_token = os.getenv('MILVUS_TOKEN')
        
        if not milvus_uri or not milvus_token:
            print("❌ MILVUS_URI or MILVUS_TOKEN not found in environment")
            return False
        
        # Connect to Milvus
        connections.connect(
            alias="default",
            uri=milvus_uri,
            token=milvus_token
        )
        
        print(f"✅ Connected to Zilliz Cloud: {milvus_uri}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Milvus: {e}")
        return False

def create_rich_content_schema():
    """Create schema for rich educational content"""
    
    # Define fields for the rich content
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True, auto_id=False),
        FieldSchema(name="concept_slug", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="concept_title", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="slice", dtype=DataType.VARCHAR, max_length=50),  # definition, analogy, example, etc.
        FieldSchema(name="style", dtype=DataType.VARCHAR, max_length=50),  # classroom, sports, cooking, etc.
        FieldSchema(name="audience", dtype=DataType.VARCHAR, max_length=20),  # kid
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),  # Main educational content
        FieldSchema(name="tags", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=10, max_length=50),
        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536)  # OpenAI embeddings
    ]
    
    # Create schema
    schema = CollectionSchema(
        fields=fields,
        description="Rich Educational ML Content for Child-Friendly Tutoring"
    )
    
    return schema

def create_collection():
    """Create the new collection"""
    collection_name = "rich_ml_education"
    
    try:
        # Check if collection already exists
        if utility.has_collection(collection_name):
            print(f"⚠️ Collection '{collection_name}' already exists")
            response = input("🤔 Drop and recreate? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                utility.drop_collection(collection_name)
                print(f"🗑️ Dropped existing collection: {collection_name}")
            else:
                print("❌ Operation cancelled")
                return None
        
        # Create new collection
        schema = create_rich_content_schema()
        collection = Collection(name=collection_name, schema=schema)
        
        print(f"✅ Created new collection: {collection_name}")
        print("📋 Schema:")
        print(f"   - Fields: {len(schema.fields)}")
        print(f"   - Primary key: id")
        print(f"   - Vector dimension: 1536 (OpenAI embeddings)")
        print(f"   - Max text length: 2000 characters")
        
        return collection
        
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Creating Rich ML Education Collection in MilvusDB")
    print("=" * 60)
    
    # Connect to Milvus
    if not connect_to_milvus():
        return
    
    # Create collection
    collection = create_collection()
    
    if collection:
        print("\n🎉 Success! New collection created for rich educational content")
        print("\n💡 Next steps:")
        print("   1. Run: python load_rich_concepts_to_milvus.py")
        print("   2. This will load all 513 rich educational chunks")
        print("   3. Update your RAG system to use the new collection")
    else:
        print("\n❌ Failed to create collection")

if __name__ == "__main__":
    main()

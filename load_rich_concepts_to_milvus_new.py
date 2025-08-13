#!/usr/bin/env python3
"""
Load Rich ML Concepts from JSONL to new MilvusDB collection
This script loads the rich educational content into the new rich_ml_education collection
"""

import os
import json
import sys
from dotenv import load_dotenv
from pymilvus import connections, Collection, utility
import openai

# Fix SSL certificates for Python
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'

# Load environment variables
load_dotenv()

def connect_to_milvus():
    """Connect to Zilliz Cloud"""
    try:
        milvus_uri = os.getenv('MILVUS_URI')
        milvus_token = os.getenv('MILVUS_TOKEN')
        
        if not milvus_uri or not milvus_token:
            print("❌ MILVUS_URI or MILVUS_TOKEN not found")
            return False
        
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

def init_openai():
    """Initialize OpenAI client"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return None
        
        client = openai.OpenAI(api_key=api_key)
        
        # Test connection
        test_response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test"
        )
        
        print("✅ OpenAI client initialized successfully")
        return client
        
    except Exception as e:
        print(f"❌ Error initializing OpenAI: {e}")
        return None

def generate_embeddings_batch(client, texts, batch_size=100):
    """Generate embeddings in batches"""
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"📦 Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=batch
            )
            
            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)
            
            # Small delay to be respectful to API
            import time
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error in batch {i//batch_size + 1}: {e}")
            return None
    
    return all_embeddings

def load_jsonl_data(filepath):
    """Load rich content from JSONL file"""
    concepts = []
    
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found")
        return concepts
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    record = json.loads(line)
                    concepts.append(record)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Skipping line {line_num}: {e}")
                    continue
    
    return concepts

def load_to_new_collection(concepts, openai_client):
    """Load concepts to the new rich_ml_education collection"""
    collection_name = "rich_ml_education"
    
    # Check if collection exists
    if not utility.has_collection(collection_name):
        print(f"❌ Collection '{collection_name}' not found!")
        print("💡 Run: python create_rich_milvus_collection.py first")
        return False
    
    # Get collection
    collection = Collection(collection_name)
    
    # Check current count
    current_count = collection.num_entities
    print(f"📊 Current records in {collection_name}: {current_count}")
    
    if current_count > 0:
        print(f"\n⚠️ Collection has {current_count} existing records")
        response = input("🤔 Clear and reload? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            # Delete all data
            collection.delete(expr="id != ''")  # Delete all records
            collection.flush()
            print("🗑️ Cleared existing data")
        else:
            print("❌ Operation cancelled")
            return False
    
    print(f"\n🔄 Generating embeddings for {len(concepts)} concepts...")
    
    # Prepare texts for embedding
    texts = []
    for concept in concepts:
        # Combine title and text for better semantic search
        combined_text = f"{concept['concept_title']}: {concept['text']}"
        texts.append(combined_text)
    
    # Generate embeddings
    embeddings = generate_embeddings_batch(openai_client, texts)
    
    if not embeddings:
        print("❌ Failed to generate embeddings")
        return False
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    
    # Prepare data for insertion
    print("💾 Preparing data for insertion...")
    
    data = [
        [concept["id"] for concept in concepts],  # id
        [concept["concept_slug"] for concept in concepts],  # concept_slug
        [concept["concept_title"] for concept in concepts],  # concept_title
        [concept["slice"] for concept in concepts],  # slice
        [concept["style"] for concept in concepts],  # style
        [concept["audience"] for concept in concepts],  # audience
        [concept["text"] for concept in concepts],  # text
        [concept["tags"] for concept in concepts],  # tags
        [concept["source"] for concept in concepts],  # source
        [concept["timestamp"] for concept in concepts],  # timestamp
        embeddings  # embedding
    ]
    
    # Insert data
    print("📤 Inserting data into MilvusDB...")
    try:
        insert_result = collection.insert(data)
        print(f"✅ Inserted {len(insert_result.primary_keys)} records")
        
        # Flush data
        print("💾 Flushing data to storage...")
        collection.flush()
        
        # Build index
        print("🔍 Building search index...")
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        
        try:
            indexes = collection.indexes
            if not indexes:
                collection.create_index(
                    field_name="embedding",
                    index_params=index_params
                )
                print("✅ Search index created")
            
            # Load collection
            collection.load()
            
            import time
            time.sleep(3)
            
            final_count = collection.num_entities
            print(f"🎉 Successfully loaded {final_count} rich educational concepts!")
            
            return True
            
        except Exception as index_error:
            print(f"⚠️ Index creation warning: {index_error}")
            collection.load()
            print("✅ Collection loaded without index")
            return True
            
    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Loading Rich ML Concepts to MilvusDB")
    print("=" * 60)
    
    # Connect to Milvus
    if not connect_to_milvus():
        return
    
    # Initialize OpenAI
    openai_client = init_openai()
    if not openai_client:
        return
    
    # Load JSONL data
    jsonl_file = "ml_analogies.jsonl"
    print(f"📚 Loading content from {jsonl_file}...")
    
    concepts = load_jsonl_data(jsonl_file)
    
    if not concepts:
        print("❌ No concepts found in JSONL file")
        return
    
    print(f"✅ Loaded {len(concepts)} rich educational chunks")
    
    # Show sample content types
    slice_counts = {}
    for concept in concepts:
        slice_type = concept.get('slice', 'unknown')
        slice_counts[slice_type] = slice_counts.get(slice_type, 0) + 1
    
    print("📊 Content breakdown:")
    for slice_type, count in slice_counts.items():
        print(f"   - {slice_type}: {count} chunks")
    
    # Load to MilvusDB
    success = load_to_new_collection(concepts, openai_client)
    
    if success:
        print("\n🎉 SUCCESS! Rich educational content loaded to MilvusDB")
        print("\n💡 Next steps:")
        print("   1. Update your RAG system to use collection 'rich_ml_education'")
        print("   2. Test with your chat application")
        print("   3. Enjoy production-ready ML tutoring!")
    else:
        print("\n❌ Failed to load content")

if __name__ == "__main__":
    main()

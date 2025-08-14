#!/usr/bin/env python3
"""
Read and export data from the youtube_creator_videos Milvus collection
This script connects to Zilliz Cloud and exports all video content to JSON
"""

import os
import json
from pymilvus import connections, Collection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_milvus():
    """Connect to Zilliz Cloud"""
    try:
        milvus_uri = os.getenv('MILVUS_URI')
        milvus_token = os.getenv('MILVUS_TOKEN')
        
        if not milvus_uri or not milvus_token:
            print("❌ MILVUS_URI or MILVUS_TOKEN not found in environment")
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

def read_and_export_videos():
    """Read all videos from Milvus and export to JSON"""
    collection_name = "youtube_creator_videos"
    
    try:
        # Connect to Milvus
        if not connect_to_milvus():
            return
        
        # Get collection
        collection = Collection(collection_name)
        
        # Load collection (required for querying)
        collection.load()
        
        # Check total count
        total_entities = collection.num_entities
        print(f"📊 Total entities in collection: {total_entities}")
        
        if total_entities == 0:
            print("⚠️ Collection is empty - no data to export")
            return
        
        # Query all data
        print("🔍 Querying all video content...")
        results = collection.query(
            expr="",  # no filter - get all records
            output_fields=["doc_id", "title", "source_url", "source", "kind", "text", "tags"],
            limit=1000  # Adjust if you have more records
        )
        
        print(f"✅ Retrieved {len(results)} records")
        
        # Organize data by video
        videos_data = {}
        
        for record in results:
            doc_id = record.get("doc_id", "")
            video_id = doc_id.split("__")[0] if "__" in doc_id else doc_id
            kind = record.get("kind", "unknown")
            
            if video_id not in videos_data:
                videos_data[video_id] = {
                    "video_id": video_id,
                    "title": record.get("title", ""),
                    "source_url": record.get("source_url", ""),
                    "source": record.get("source", ""),
                    "tags": record.get("tags", ""),
                    "content": {}
                }
            
            videos_data[video_id]["content"][kind] = record.get("text", "")
        
        # Convert to list format
        from datetime import datetime
        export_data = {
            "collection": collection_name,
            "total_videos": len(videos_data),
            "total_content_pieces": len(results),
            "export_timestamp": datetime.now().isoformat(),
            "videos": list(videos_data.values())
        }
        
        # Export to JSON
        output_file = "statquest_videos_export.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"🎉 Successfully exported to: {output_file}")
        print(f"📹 Videos: {len(videos_data)}")
        print(f"📝 Content pieces: {len(results)}")
        
        # Show sample data
        print("\n📋 Sample content types:")
        content_types = {}
        for record in results:
            kind = record.get("kind", "unknown")
            content_types[kind] = content_types.get(kind, 0) + 1
        
        for content_type, count in content_types.items():
            print(f"   - {content_type}: {count} pieces")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading from Milvus: {e}")
        return False

def main():
    """Main function"""
    print("🚀 StatQuest Videos Milvus Export")
    print("=" * 50)
    
    success = read_and_export_videos()
    
    if success:
        print("\n✅ Export completed successfully!")
        print("💡 Use the JSON file for future processing or analysis")
    else:
        print("\n❌ Export failed!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Data Quality Validation Tests
Tests data quality checks for both data sources:
- Generated ML concepts dataset (rich_ml_education)
- StatQuest video transcripts (youtube_creator_videos)
"""

import requests
import json
import os
from typing import Dict, List, Any, Set
from dotenv import load_dotenv
import hashlib
import urllib3

# Load environment variables
load_dotenv()

# Disable SSL warnings for testing (since we're having cert issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")

class DataQualityValidator:
    def __init__(self):
        self.results = {}
        
    def connect_to_milvus(self):
        """Test connection to Milvus"""
        print("🔌 Testing Milvus connection...")
        
        try:
            # Test connection by listing collections
            headers = {
                'Authorization': f'Bearer {MILVUS_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{MILVUS_URI}/v1/vector/collections",
                headers=headers,
                timeout=10,
                verify=False  # Disable SSL verification for testing
            )
            
            if response.status_code == 200:
                collections = response.json()
                print(f"✅ Connected to Milvus. Found {len(collections.get('data', []))} collections")
                return True
            else:
                print(f"❌ Milvus connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Milvus connection error: {e}")
            return False

    def validate_generated_dataset(self):
        """Validate the rich_ml_education collection"""
        print("🧪 Validating Generated ML Concepts Dataset...")
        
        # Test 1: Min/Max length filter
        length_results = self.test_content_length_filter("rich_ml_education")
        
        # Test 2: Duplicate detection
        duplicate_results = self.test_duplicate_detection("rich_ml_education")
        
        return length_results and duplicate_results

    def validate_statquest_dataset(self):
        """Validate the youtube_creator_videos collection"""
        print("🧪 Validating StatQuest Video Dataset...")
        
        # Test 1: Drop empty/low-signal chunks
        empty_results = self.test_empty_content_filter("youtube_creator_videos")
        
        # Test 2: Ensure title/URL present
        metadata_results = self.test_metadata_completeness("youtube_creator_videos")
        
        return empty_results and metadata_results

    def test_content_length_filter(self, collection_name: str):
        """Test min/max length filtering for content"""
        print(f"📏 Testing content length filter for {collection_name}...")
        
        try:
            # Query some documents from the collection
            documents = self.query_collection(collection_name, limit=100)
            
            if not documents:
                print(f"❌ No documents found in {collection_name}")
                return False
            
            # Define length thresholds
            MIN_LENGTH = 50    # Minimum meaningful content
            MAX_LENGTH = 5000  # Maximum reasonable chunk size
            
            valid_count = 0
            too_short = 0
            too_long = 0
            
            for doc in documents:
                content = doc.get('text', '')
                length = len(content)
                
                if length < MIN_LENGTH:
                    too_short += 1
                elif length > MAX_LENGTH:
                    too_long += 1
                else:
                    valid_count += 1
            
            total = len(documents)
            validity_rate = valid_count / total
            
            print(f"📊 Length Analysis for {collection_name}:")
            print(f"   Valid length ({MIN_LENGTH}-{MAX_LENGTH} chars): {valid_count}/{total} ({validity_rate:.1%})")
            print(f"   Too short (<{MIN_LENGTH} chars): {too_short}")
            print(f"   Too long (>{MAX_LENGTH} chars): {too_long}")
            
            # Report specific issues
            if too_short > 0:
                print(f"⚠️ Found {too_short} chunks that are too short (may be low-signal)")
            
            if too_long > 0:
                print(f"⚠️ Found {too_long} chunks that are too long (may need splitting)")
            
            # Consider it passing if 80% of content has valid length
            success = validity_rate >= 0.8
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} - Length filter validation")
            
            return success
            
        except Exception as e:
            print(f"❌ Error testing length filter: {e}")
            return False

    def test_duplicate_detection(self, collection_name: str):
        """Test for duplicate content detection"""
        print(f"🔍 Testing duplicate detection for {collection_name}...")
        
        try:
            # Query documents from the collection
            documents = self.query_collection(collection_name, limit=200)
            
            if not documents:
                print(f"❌ No documents found in {collection_name}")
                return False
            
            # Create hashes of content for duplicate detection
            content_hashes: Dict[str, List[str]] = {}
            
            for doc in documents:
                content = doc.get('text', '').strip()
                if content:
                    # Create hash of content
                    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    
                    if content_hash not in content_hashes:
                        content_hashes[content_hash] = []
                    
                    doc_id = doc.get('id', 'unknown')
                    content_hashes[content_hash].append(doc_id)
            
            # Find duplicates
            duplicates = {h: ids for h, ids in content_hashes.items() if len(ids) > 1}
            
            total_docs = len(documents)
            duplicate_count = sum(len(ids) - 1 for ids in duplicates.values())  # Subtract 1 for original
            duplicate_rate = duplicate_count / total_docs if total_docs > 0 else 0
            
            print(f"📊 Duplicate Analysis for {collection_name}:")
            print(f"   Total documents checked: {total_docs}")
            print(f"   Duplicate documents: {duplicate_count} ({duplicate_rate:.1%})")
            print(f"   Unique content groups: {len(content_hashes)}")
            
            if duplicates:
                print(f"⚠️ Found {len(duplicates)} duplicate content groups:")
                for i, (hash_val, doc_ids) in enumerate(list(duplicates.items())[:5], 1):
                    print(f"   Group {i}: {len(doc_ids)} copies - {doc_ids}")
                if len(duplicates) > 5:
                    print(f"   ... and {len(duplicates) - 5} more groups")
            
            # Consider it passing if less than 5% duplicates
            success = duplicate_rate < 0.05
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} - Duplicate detection")
            
            return success
            
        except Exception as e:
            print(f"❌ Error testing duplicates: {e}")
            return False

    def test_empty_content_filter(self, collection_name: str):
        """Test filtering of empty or low-signal chunks"""
        print(f"🗑️ Testing empty content filter for {collection_name}...")
        
        try:
            # Query documents from the collection
            documents = self.query_collection(collection_name, limit=100)
            
            if not documents:
                print(f"❌ No documents found in {collection_name}")
                return False
            
            empty_count = 0
            low_signal_count = 0
            valid_count = 0
            
            # Define low-signal patterns
            low_signal_patterns = [
                'click here', 'subscribe', 'like and subscribe', 
                'thanks for watching', 'see you next time',
                'music playing', '[music]', '[applause]',
                'and that\'s it', 'that\'s all', 'bye bye'
            ]
            
            for doc in documents:
                content = doc.get('text', '').strip()
                
                if not content:
                    empty_count += 1
                    continue
                
                # Check for low-signal content
                content_lower = content.lower()
                is_low_signal = any(pattern in content_lower for pattern in low_signal_patterns)
                
                # Also check for very short chunks that are likely not educational
                if len(content) < 30 or is_low_signal:
                    low_signal_count += 1
                else:
                    valid_count += 1
            
            total = len(documents)
            validity_rate = valid_count / total if total > 0 else 0
            
            print(f"📊 Content Quality Analysis for {collection_name}:")
            print(f"   Valid content: {valid_count}/{total} ({validity_rate:.1%})")
            print(f"   Empty content: {empty_count}")
            print(f"   Low-signal content: {low_signal_count}")
            
            if empty_count > 0:
                print(f"⚠️ Found {empty_count} empty chunks that should be filtered")
            
            if low_signal_count > 0:
                print(f"⚠️ Found {low_signal_count} low-signal chunks that should be filtered")
            
            # Consider it passing if 85% of content is valid
            success = validity_rate >= 0.85
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} - Empty content filter")
            
            return success
            
        except Exception as e:
            print(f"❌ Error testing empty content filter: {e}")
            return False

    def test_metadata_completeness(self, collection_name: str):
        """Test that title and URL are present in metadata"""
        print(f"📋 Testing metadata completeness for {collection_name}...")
        
        try:
            # Query documents from the collection
            documents = self.query_collection(collection_name, limit=100)
            
            if not documents:
                print(f"❌ No documents found in {collection_name}")
                return False
            
            complete_metadata = 0
            missing_title = 0
            missing_url = 0
            
            for doc in documents:
                metadata = doc.get('metadata', {})
                
                # Handle different metadata formats
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                elif isinstance(metadata, list) and metadata:
                    try:
                        metadata = json.loads(metadata[0]) if metadata[0] else {}
                    except:
                        metadata = {}
                
                has_title = bool(metadata.get('video_title') or metadata.get('title'))
                has_url = bool(metadata.get('youtube_id') or metadata.get('url') or metadata.get('source_url'))
                
                if has_title and has_url:
                    complete_metadata += 1
                else:
                    if not has_title:
                        missing_title += 1
                    if not has_url:
                        missing_url += 1
            
            total = len(documents)
            completeness_rate = complete_metadata / total if total > 0 else 0
            
            print(f"📊 Metadata Completeness for {collection_name}:")
            print(f"   Complete metadata: {complete_metadata}/{total} ({completeness_rate:.1%})")
            print(f"   Missing title: {missing_title}")
            print(f"   Missing URL/ID: {missing_url}")
            
            if missing_title > 0:
                print(f"⚠️ Found {missing_title} documents missing titles")
            
            if missing_url > 0:
                print(f"⚠️ Found {missing_url} documents missing URLs/IDs")
            
            # Consider it passing if 90% have complete metadata
            success = completeness_rate >= 0.90
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} - Metadata completeness")
            
            return success
            
        except Exception as e:
            print(f"❌ Error testing metadata completeness: {e}")
            return False

    def query_collection(self, collection_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query documents from a Milvus collection"""
        try:
            headers = {
                'Authorization': f'Bearer {MILVUS_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Use a simple query to get documents
            query_data = {
                "collectionName": collection_name,
                "vector": [0.1] * 384,  # Dummy vector for search
                "limit": limit,
                "outputFields": ["text", "metadata", "id"]
            }
            
            response = requests.post(
                f"{MILVUS_URI}/v1/vector/search",
                headers=headers,
                json=query_data,
                timeout=30,
                verify=False  # Disable SSL verification for testing
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', [])
            else:
                print(f"⚠️ Query failed for {collection_name}: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error querying {collection_name}: {e}")
            return []

    def run_all_tests(self):
        """Run all data quality tests"""
        print("🚀 Starting Data Quality Validation Tests")
        print("=" * 60)
        
        # Check Milvus connection first
        if not self.connect_to_milvus():
            print("❌ Cannot proceed without Milvus connection")
            return False
        
        # Run tests for both data sources
        test_results = {
            "Generated ML Concepts Dataset": self.validate_generated_dataset(),
            "StatQuest Video Dataset": self.validate_statquest_dataset()
        }
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DATA QUALITY TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:.<40} {status}")
            if result:
                passed += 1
        
        success_rate = passed / total
        print(f"\n📈 Overall Score: {passed}/{total} ({success_rate:.1%})")
        
        if success_rate == 1.0:
            print("🎉 ALL DATA QUALITY TESTS PASSED!")
        elif success_rate >= 0.8:
            print("⚠️ Most tests passed - minor data quality issues")
        else:
            print("🚨 CRITICAL: Major data quality issues detected!")
        
        return success_rate >= 0.8

def main():
    """Main entry point"""
    validator = DataQualityValidator()
    success = validator.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if success else 1
    exit(exit_code)

if __name__ == "__main__":
    main()

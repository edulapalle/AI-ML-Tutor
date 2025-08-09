#!/usr/bin/env python3
"""
Check ML concepts collection status without modifying anything
Use this to verify your collection without risk of overwriting
"""

import os
import sys
from dotenv import load_dotenv
from rag_system import get_rag_system

def main():
    """Check ML concepts collection status"""
    print("🔍 ML Concepts Collection Status Check")
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
        # Initialize RAG system (read-only check)
        print("🔄 Connecting to RAG system...")
        rag_system = get_rag_system()
        
        # Get comprehensive status
        status = rag_system.get_system_status()
        
        print("📊 System Status:")
        print(f"   - Milvus Connected: {'✅' if status['milvus_connected'] else '❌'}")
        print(f"   - OpenAI Available: {'✅' if status['openai_available'] else '❌'}")
        print(f"   - Sentence Transformer: {'✅' if status.get('sentence_transformer_loaded', False) else '❌'}")
        print(f"   - Collection Exists: {'✅' if status['collection_exists'] else '❌'}")
        print(f"   - Concepts Count: {status['concepts_count']}")
        
        if status['concepts_count'] > 0:
            print("\n📋 Collection Contents:")
            
            # Get detailed collection summary
            concepts_summary = rag_system.get_all_concepts_summary()
            
            if concepts_summary:
                for category, concepts in concepts_summary.items():
                    print(f"   📁 {category} ({len(concepts)} concepts)")
                    for concept in concepts[:3]:  # Show first 3 concepts
                        print(f"      • {concept['name']} ({concept['difficulty']})")
                    if len(concepts) > 3:
                        print(f"      ... and {len(concepts) - 3} more")
                
                # Statistics
                total_concepts = sum(len(concepts) for concepts in concepts_summary.values())
                print(f"\n📈 Statistics:")
                print(f"   - Total Concepts: {total_concepts}")
                print(f"   - Categories: {len(concepts_summary)}")
                
                # Difficulty breakdown
                difficulty_counts = {}
                for concepts in concepts_summary.values():
                    for concept in concepts:
                        diff = concept.get('difficulty', 'unknown')
                        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
                
                print(f"   - Difficulty Levels:")
                for difficulty, count in sorted(difficulty_counts.items()):
                    percentage = (count / total_concepts) * 100
                    print(f"     * {difficulty.title()}: {count} ({percentage:.1f}%)")
            
            print(f"\n✅ Your RAG system is ready with {status['concepts_count']} ML concepts!")
            
            # Test basic retrieval
            print("\n🧪 Quick Retrieval Test:")
            test_concepts = rag_system.search_concepts("machine learning", top_k=2)
            if test_concepts:
                print("✅ Concept retrieval working!")
                for i, concept in enumerate(test_concepts, 1):
                    print(f"   {i}. {concept.get('concept', 'Unknown')} (Score: {concept.get('similarity_score', 0):.3f})")
            else:
                print("⚠️ Concept retrieval not working properly")
        
        elif status['collection_exists']:
            print("\n⚠️ Collection exists but is empty")
            print("💡 Run 'python populate_ml_concepts.py' to add ML concepts")
        
        else:
            print("\n❌ Collection does not exist")
            print("💡 Run 'python populate_ml_concepts.py' to create and populate collection")
        
        # Overall readiness
        print(f"\n🎯 RAG System Readiness:")
        if all([status['milvus_connected'], status['openai_available'], status['collection_exists'], status['concepts_count'] > 0]):
            print("✅ READY - All systems operational!")
        elif status['concepts_count'] == 0:
            print("⚠️ NOT READY - Collection empty, needs population")
        else:
            print("❌ NOT READY - System configuration issues")
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

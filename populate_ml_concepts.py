#!/usr/bin/env python3
"""
One-time script to populate ML concepts in Milvus/Zilliz Cloud
Run this script once after setting up your Zilliz Cloud cluster
"""

import os
import sys
from dotenv import load_dotenv
from rag_system import get_rag_system

def main():
    """Populate ML concepts in the vector database"""
    print("🚀 Starting ML Concepts Population Script")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['OPENAI_API_KEY', 'MILVUS_URI', 'MILVUS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Please set these in your .env file:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        sys.exit(1)
    
    try:
        # Initialize RAG system
        print("🔄 Initializing RAG system...")
        rag_system = get_rag_system()
        
        # Check system status
        status = rag_system.get_system_status()
        
        if not status['milvus_connected']:
            print("❌ Failed to connect to Milvus/Zilliz Cloud")
            print("💡 Check your MILVUS_URI and MILVUS_TOKEN in .env")
            sys.exit(1)
        
        if not status['openai_available']:
            print("❌ OpenAI client not available")
            print("💡 Check your OPENAI_API_KEY in .env")
            sys.exit(1)
        
        print("✅ All connections established successfully!")
        print(f"📊 Current collection status:")
        print(f"   - Collection exists: {status['collection_exists']}")
        print(f"   - Concepts count: {status['concepts_count']}")
        
        # Check if population is needed
        needs_population = False
        
        if status['concepts_count'] > 0:
            print(f"⚠️ Collection already has {status['concepts_count']} concepts")
            response = input("Do you want to proceed and overwrite? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("✅ Operation cancelled by user")
                print("💡 Collection already contains ML concepts and is ready to use!")
                return
            else:
                needs_population = True
                print("🔄 User confirmed overwrite...")
        else:
            needs_population = True
            print("🔄 Collection is empty, population needed...")
        
        # Only populate if needed
        if needs_population:
            print("\n🔄 Populating ML concepts...")
            print("This may take a few minutes to generate embeddings...")
            
            if status['concepts_count'] == 0:
                print("🔄 Starting fresh population...")
                success = rag_system.populate_if_empty()
            else:
                print("🔄 Overwriting existing data...")
                rag_system.force_repopulate()
                success = True
                
            if not success:
                print("❌ Failed to populate collection")
                sys.exit(1)
        else:
            print("✅ No population needed - collection already ready!")
            return
        
        # Wait a bit more for cloud synchronization
        import time
        print("⏳ Waiting for cloud synchronization...")
        time.sleep(5)
        
        # Verify final status multiple times
        final_status = None
        for attempt in range(3):
            print(f"🔍 Verification attempt {attempt + 1}/3...")
            final_status = rag_system.get_system_status()
            if final_status['concepts_count'] > 0:
                break
            time.sleep(3)
        
        if final_status and final_status['concepts_count'] > 0:
            print(f"\n🎉 Success! Populated {final_status['concepts_count']} ML concepts")
            print("✅ Your RAG system is ready to use!")
            
            # Dynamically retrieve and display actual collection data
            print("\n📋 Retrieving actual data from Milvus collection...")
            try:
                # Get all concepts and group by category
                all_concepts = rag_system.get_all_concepts_summary()
                
                if all_concepts:
                    print("📊 What's been added:")
                    for category, concepts in all_concepts.items():
                        concept_names = [concept['name'] for concept in concepts]
                        print(f"   • {category}: {', '.join(concept_names)}")
                    
                    print(f"\n📈 Collection Statistics:")
                    total_concepts = sum(len(concepts) for concepts in all_concepts.values())
                    print(f"   - Total Concepts: {total_concepts}")
                    print(f"   - Categories: {len(all_concepts)}")
                    print(f"   - Average per Category: {total_concepts/len(all_concepts):.1f}")
                    
                    # Show difficulty distribution
                    difficulty_counts = {}
                    for concepts in all_concepts.values():
                        for concept in concepts:
                            diff = concept.get('difficulty', 'unknown')
                            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
                    
                    print(f"   - Difficulty Distribution:")
                    for difficulty, count in difficulty_counts.items():
                        print(f"     * {difficulty.title()}: {count} concepts")
                        
                else:
                    print("⚠️ Could not retrieve collection details")
                    
            except Exception as e:
                print(f"⚠️ Error retrieving collection details: {e}")
                print("✅ But population appears successful based on count")
        else:
            print("⚠️ Population completed but verification shows 0 concepts")
            print("💡 This may be a cloud synchronization delay")
            print("✅ Try running the application - it might work anyway!")
            print("🔄 Or wait a few minutes and check your Zilliz dashboard")
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error during population: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

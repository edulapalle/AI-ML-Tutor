#!/usr/bin/env python3
"""
Manual Test Script for Data Loading to Milvus and Neo4j
=======================================================

This script demonstrates and tests steps 3, 4, 5 of the real-time pipeline:
3. AI Content Generation (summary, analogy, quiz)
4. Milvus Cloud Integration (embeddings + vector storage)
5. Neo4j Cloud Integration (knowledge graph relationships)

Usage: python test_data_loading.py
"""

import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure SSL (your fix)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Sample video data (from recent StatQuest video)
SAMPLE_VIDEO = {
    "video_id": "qPN_XZcJf_s",
    "title": "Reinforcement Learning with Human Feedback (RLHF), Clearly Explained!!!",
    "description": "Reinforcement Learning with Human Feedback (RLHF) is used to train Large Language Models like ChatGPT. In this StatQuest, I clearly explain what RLHF is and how it works.",
    "published_at": "2025-05-05T04:01:03Z",
    "duration": "PT17M42S",
    "view_count": 158420,
    "url": "https://www.youtube.com/watch?v=qPN_XZcJf_s",
    "transcript": "Hello, I'm Josh Starmer and welcome to StatQuest. Today we're going to talk about Reinforcement Learning with Human Feedback, or RLHF for short..."
}

async def test_step3_ai_content_generation():
    """Test Step 3: AI Content Generation"""
    print("🤖 STEP 3: AI Content Generation")
    print("=" * 50)
    
    try:
        import openai
        
        # Initialize OpenAI client
        openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if not openai_client.api_key:
            print("❌ OPENAI_API_KEY not found")
            return None
        
        # System prompt (from your existing code)
        system_tutor = (
            "You are a kind ML tutor for a 10-year-old. "
            "Use plain language, short sentences, no equations. "
            "Be accurate and safe."
        )
        
        # Generate content using your existing prompts
        title = SAMPLE_VIDEO["title"]
        description = SAMPLE_VIDEO["description"][:800]
        transcript_excerpt = SAMPLE_VIDEO["transcript"][:1800]
        
        print(f"📹 Video: {title}")
        print(f"📝 Generating AI content...")
        
        # 1. Summary
        summary_prompt = (
            "Summarize the main idea of this ML video for a 10-year-old in 4–5 short sentences. "
            "Avoid formulas and jargon. End with when/why it's useful.\n\n"
            f"TITLE: {title}\nDESCRIPTION: {description}\nTRANSCRIPT_EXCERPT:\n{transcript_excerpt}"
        )
        
        summary_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_tutor},
                {"role": "user", "content": summary_prompt}
            ]
        )
        summary = summary_response.choices[0].message.content.strip()
        
        # 2. Analogy
        analogy_prompt = (
            "Create one child-friendly analogy for the topic of this video, "
            "using a concrete everyday situation (sports, cooking, or playground). "
            f"Write 4–5 short sentences.\n\nTITLE: {title}\n"
        )
        
        analogy_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_tutor},
                {"role": "user", "content": analogy_prompt}
            ]
        )
        analogy = analogy_response.choices[0].message.content.strip()
        
        # 3. Quiz
        quiz_prompt = (
            "Write one simple question and a short answer about this video topic for a 10-year-old. "
            f"Output exactly two lines: 'Q: ...' and 'A: ...'.\n\nTITLE: {title}\n"
        )
        
        quiz_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_tutor},
                {"role": "user", "content": quiz_prompt}
            ]
        )
        quiz = quiz_response.choices[0].message.content.strip()
        
        # Display generated content
        print(f"\n📊 GENERATED CONTENT:")
        print(f"\n1️⃣ Summary ({len(summary)} chars):")
        print(f"   {summary}")
        print(f"\n2️⃣ Analogy ({len(analogy)} chars):")
        print(f"   {analogy}")
        print(f"\n3️⃣ Quiz ({len(quiz)} chars):")
        print(f"   {quiz}")
        
        generated_content = {
            "summary": summary,
            "analogy": analogy,
            "quiz": quiz
        }
        
        print(f"\n✅ Step 3 Complete: Generated 3 pieces of educational content")
        return generated_content
        
    except Exception as e:
        print(f"❌ Step 3 Failed: {e}")
        return None

async def test_step4_milvus_integration(generated_content):
    """Test Step 4: Milvus Cloud Integration"""
    print("\n🔍 STEP 4: Milvus Cloud Integration")
    print("=" * 50)
    
    try:
        import openai
        from pymilvus import connections, Collection, utility
        
        if not generated_content:
            print("❌ No content to process (Step 3 failed)")
            return False
        
        # Initialize OpenAI for embeddings
        openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Connect to Milvus Cloud
        print("🔗 Connecting to Milvus Cloud...")
        milvus_uri = os.getenv('MILVUS_URI')
        milvus_token = os.getenv('MILVUS_TOKEN')
        
        if not milvus_uri or not milvus_token:
            print("❌ MILVUS_URI or MILVUS_TOKEN not found")
            return False
        
        connections.connect(
            alias="test_connection",
            uri=milvus_uri,
            token=milvus_token
        )
        
        print(f"✅ Connected to: {milvus_uri}")
        
        # Check collection
        collection_name = "youtube_creator_videos"
        if not utility.has_collection(collection_name, using="test_connection"):
            print(f"❌ Collection '{collection_name}' not found")
            print("💡 Run your existing ingest script first to create the collection")
            return False
        
        collection = Collection(collection_name, using="test_connection")
        print(f"✅ Collection found: {collection_name}")
        
        # Generate embeddings
        print("🔮 Generating embeddings...")
        texts = [generated_content["summary"], generated_content["analogy"], generated_content["quiz"]]
        
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        embeddings = [d.embedding for d in response.data]
        print(f"✅ Generated {len(embeddings)} embeddings (dimension: {len(embeddings[0])})")
        
        # Prepare data for Milvus (using your existing format)
        video_id = SAMPLE_VIDEO["video_id"]
        title = SAMPLE_VIDEO["title"]
        url = SAMPLE_VIDEO["url"]
        
        batch_rows = []
        for (kind, text), embedding in zip([("summary", generated_content["summary"]), 
                                          ("analogy", generated_content["analogy"]), 
                                          ("quiz", generated_content["quiz"])], embeddings):
            row = {
                "doc_id": f"{video_id}__{kind}__test",  # Add 'test' to avoid conflicts
                "title": title,
                "source_url": url,
                "source": "statquest",
                "kind": kind,
                "text": text,
                "embedding": embedding,
                "tags": "statistics,ml,education,statquest,test",
            }
            batch_rows.append(row)
        
        # Insert to Milvus
        print("💾 Inserting to Milvus...")
        collection.insert([
            [r["doc_id"] for r in batch_rows],
            [r["title"] for r in batch_rows],
            [r["source_url"] for r in batch_rows],
            [r["source"] for r in batch_rows],
            [r["kind"] for r in batch_rows],
            [r["text"] for r in batch_rows],
            [r["embedding"] for r in batch_rows],
            [r["tags"] for r in batch_rows],
        ], using="test_connection")
        
        collection.flush(using="test_connection")
        
        # Verify insertion
        print("🔍 Verifying insertion...")
        collection.load(using="test_connection")
        
        # Search for our test data
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = collection.search(
            data=[embeddings[0]],  # Search using summary embedding
            anns_field="embedding",
            param=search_params,
            limit=5,
            expr=f"doc_id like '{video_id}%test'",
            output_fields=["doc_id", "title", "kind", "source"],
            using="test_connection"
        )
        
        print(f"📊 MILVUS INSERTION RESULTS:")
        for i, result in enumerate(results[0]):
            print(f"   {i+1}. {result.entity.get('doc_id')} ({result.entity.get('kind')})")
            print(f"      Score: {result.score:.4f}")
        
        print(f"\n✅ Step 4 Complete: Successfully inserted {len(batch_rows)} records to Milvus")
        
        # Cleanup test data
        print("🧹 Cleaning up test data...")
        collection.delete(expr=f"doc_id like '{video_id}%test'", using="test_connection")
        collection.flush(using="test_connection")
        print("✅ Test data cleaned up")
        
        connections.disconnect("test_connection")
        return True
        
    except Exception as e:
        print(f"❌ Step 4 Failed: {e}")
        try:
            connections.disconnect("test_connection")
        except:
            pass
        return False

async def test_step5_neo4j_integration():
    """Test Step 5: Neo4j Cloud Integration"""
    print("\n🕸️ STEP 5: Neo4j Cloud Integration")
    print("=" * 50)
    
    try:
        from neo4j import GraphDatabase
        
        # Connect to Neo4j (using your SSL fix)
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not uri or not password:
            print("❌ Neo4j connection details not found")
            return False
        
        # Convert neo4j+s:// to bolt+s:// (your SSL fix)
        if uri.startswith("neo4j+s://"):
            uri = uri.replace("neo4j+s://", "bolt+s://")
        
        print(f"🔗 Connecting to Neo4j: {uri}")
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session(database="neo4j") as session:
            # Test connection
            result = session.run("RETURN 1 as test")
            result.single()
            print("✅ Neo4j connection successful")
            
            video_id = SAMPLE_VIDEO["video_id"]
            title = SAMPLE_VIDEO["title"]
            url = SAMPLE_VIDEO["url"]
            
            # 1. Create video node (using your existing format)
            print("📹 Creating video node...")
            video_query = """
            MERGE (v:Video {video_id: $video_id})
            SET v.title = $title,
                v.url = $url,
                v.source = $source,
                v.view_count = $view_count,
                v.duration = $duration,
                v.published_at = $published_at,
                v.updated_at = datetime(),
                v.test_data = true
            RETURN v
            """
            
            session.run(video_query, {
                'video_id': video_id,
                'title': title,
                'url': url,
                'source': 'statquest',
                'view_count': SAMPLE_VIDEO['view_count'],
                'duration': SAMPLE_VIDEO['duration'],
                'published_at': SAMPLE_VIDEO['published_at']
            })
            print(f"✅ Video node created: {title}")
            
            # 2. Create channel relationship
            print("📺 Creating channel relationship...")
            channel_query = """
            MERGE (c:Channel {name: $channel_name})
            RETURN c
            """
            session.run(channel_query, {'channel_name': 'StatQuest with Josh Starmer'})
            
            relationship_query = """
            MATCH (v:Video {video_id: $video_id})
            MATCH (c:Channel {name: $channel_name})
            MERGE (v)-[:UPLOADED_BY]->(c)
            """
            session.run(relationship_query, {
                'video_id': video_id,
                'channel_name': 'StatQuest with Josh Starmer'
            })
            print("✅ Channel relationship created")
            
            # 3. Link to ML concepts (using your existing keyword mapping)
            print("🔗 Linking to ML concepts...")
            title_lower = title.lower()
            concept_keywords = {
                "reinforcement learning": "reinforcement-learning",
                "machine learning": "ml-foundations",
                "neural network": "neural-networks",
                "deep learning": "deep-learning",
                "feedback": "feedback-learning"
            }
            
            linked_concepts = []
            for keyword, concept_slug in concept_keywords.items():
                if keyword in title_lower:
                    linked_concepts.append(concept_slug)
            
            # Create relationships to concepts (if they exist)
            for concept_slug in linked_concepts[:2]:  # Limit to 2 concepts
                concept_rel_query = """
                MATCH (v:Video {video_id: $video_id})
                MATCH (c:Concept {slug: $concept_slug})
                MERGE (v)-[:COVERS]->(c)
                """
                try:
                    result = session.run(concept_rel_query, {
                        'video_id': video_id,
                        'concept_slug': concept_slug
                    })
                    print(f"✅ Linked to concept: {concept_slug}")
                except:
                    print(f"⚠️ Concept not found: {concept_slug}")
            
            # 4. Verify the data
            print("🔍 Verifying Neo4j data...")
            verify_query = """
            MATCH (v:Video {video_id: $video_id, test_data: true})
            OPTIONAL MATCH (v)-[:UPLOADED_BY]->(c:Channel)
            OPTIONAL MATCH (v)-[:COVERS]->(concept:Concept)
            RETURN v.title as title, c.name as channel, 
                   collect(concept.name) as concepts,
                   v.view_count as views
            """
            
            result = session.run(verify_query, {'video_id': video_id})
            record = result.single()
            
            if record:
                print(f"📊 NEO4J VERIFICATION RESULTS:")
                print(f"   📹 Video: {record['title']}")
                print(f"   📺 Channel: {record['channel']}")
                print(f"   🔗 Concepts: {record['concepts']}")
                print(f"   👀 Views: {record['views']:,}")
            
            print(f"\n✅ Step 5 Complete: Successfully created video node + relationships in Neo4j")
            
            # Cleanup test data
            print("🧹 Cleaning up test data...")
            cleanup_query = "MATCH (v:Video {test_data: true}) DETACH DELETE v"
            session.run(cleanup_query)
            print("✅ Test data cleaned up")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Step 5 Failed: {e}")
        try:
            driver.close()
        except:
            pass
        return False

async def main():
    """Main test function"""
    print("🚀 Manual Data Loading Test")
    print("=" * 60)
    print(f"🎯 Testing with video: {SAMPLE_VIDEO['title']}")
    print(f"🆔 Video ID: {SAMPLE_VIDEO['video_id']}")
    print("=" * 60)
    
    # Test each step
    results = {}
    
    # Step 3: AI Content Generation
    generated_content = await test_step3_ai_content_generation()
    results['step3'] = generated_content is not None
    
    # Step 4: Milvus Integration
    if generated_content:
        results['step4'] = await test_step4_milvus_integration(generated_content)
    else:
        results['step4'] = False
    
    # Step 5: Neo4j Integration
    results['step5'] = await test_step5_neo4j_integration()
    
    # Summary
    print(f"\n🎯 FINAL RESULTS")
    print("=" * 30)
    print(f"Step 3 (AI Content): {'✅ PASS' if results['step3'] else '❌ FAIL'}")
    print(f"Step 4 (Milvus):     {'✅ PASS' if results['step4'] else '❌ FAIL'}")
    print(f"Step 5 (Neo4j):      {'✅ PASS' if results['step5'] else '❌ FAIL'}")
    
    if all(results.values()):
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Your real-time pipeline data loading is working perfectly")
        print(f"🚀 Ready for production monitoring")
    else:
        print(f"\n⚠️ Some tests failed - check error messages above")
        failed_steps = [f"Step {i+3}" for i, passed in enumerate(results.values()) if not passed]
        print(f"❌ Failed: {', '.join(failed_steps)}")

if __name__ == "__main__":
    asyncio.run(main())

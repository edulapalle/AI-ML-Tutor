#!/usr/bin/env python3
"""
Ingest YouTube videos into Milvus Cloud:
- Get video metadata (yt-dlp)
- Get captions if available (youtube-transcript-api with SSL fix)
- Generate derived notes (kid summary, analogy, quiz) via OpenAI
- Embed (OpenAI text-embedding-3-small) and upsert into Milvus Cloud

ENV:
  OPENAI_API_KEY=...
  MILVUS_URI=...
  MILVUS_TOKEN=...

USAGE:
  pip install yt-dlp youtube-transcript-api openai pymilvus tiktoken
  python ingest_statquest.py --playlist "https://youtube.com/playlist?list=PLblh5JKOoLUICTaGLRoHQDuF_7q2GfuJF&si=x0CgfuMKOz6GLTfr" --limit 104
"""

import os, json, time, random, argparse
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Fix SSL certificates for Python
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'

# Load environment variables
load_dotenv()

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from openai import OpenAI
from openai import APIError, RateLimitError, APIConnectionError

from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType,
    Collection, utility
)

# ----------------------
# Config
# ----------------------
COLLECTION_NAME = "youtube_creator_videos"
EMBED_DIM = 1536  # text-embedding-3-small
TOPIC_TAG = "statquest"

SYSTEM_TUTOR = (
    "You are a kind ML tutor for a 10-year-old. "
    "Use plain language, short sentences, no equations. "
    "Be accurate and safe."
)

PROMPT_SUMMARY = (
    "Summarize the main idea of this ML video for a 10-year-old in 4–5 short sentences. "
    "Avoid formulas and jargon. End with when/why it's useful.\n\n"
    "TITLE: {title}\nDESCRIPTION: {desc}\nTRANSCRIPT_EXCERPT:\n{excerpt}"
)

PROMPT_ANALOGY = (
    "Create one child-friendly analogy for the topic of this video, "
    "using a concrete everyday situation (sports, cooking, or playground). "
    "Write 4–5 short sentences.\n\nTITLE: {title}\n"
)

PROMPT_QUIZ = (
    "Write one simple question and a short answer about this video topic for a 10-year-old. "
    "Output exactly two lines: 'Q: ...' and 'A: ...'.\n\nTITLE: {title}\n"
)

# ----------------------
# Helpers
# ----------------------
def get_video_entries(playlist_url: str) -> List[Dict]:
    ydl_opts = {'quiet': True, 'extract_flat': True, 'dump_single_json': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
    entries = [e for e in info.get("entries", []) if e and e.get("id")]
    return entries

def get_metadata(video_id: str) -> Dict:
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "video_id": video_id,
        "title": info.get("title"),
        "description": info.get("description"),
        "uploader": info.get("uploader"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "url": url
    }

def get_caption_text(video_id: str, max_chars: int = 2000) -> str:
    try:
        # Create instance of YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        tr = api.get_transcript(video_id, languages=['en'])
        text = " ".join([x["text"] for x in tr if x.get("text")])
        # keep only a slice to guide the LLM, not full storage
        return text[:max_chars]
    except (TranscriptsDisabled, NoTranscriptFound, Exception) as e:
        print(f"      ⚠️ No transcript available: {e}")
        return ""

def backoff_sleep(attempt: int):
    time.sleep(min(2 ** attempt, 32) + random.random())

def llm_call(client: OpenAI, system: str, user: str, model: str = "gpt-4o-mini", temperature: float = 0.2) -> str:
    for attempt in range(6):
        try:
            r = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[{"role":"system","content":system},{"role":"user","content":user}]
            )
            return (r.choices[0].message.content or "").strip()
        except (APIError, APIConnectionError, RateLimitError) as e:
            if attempt == 5: raise
            print(f"⚠️ API error on attempt {attempt + 1}: {e}")
            backoff_sleep(attempt)

def embed_texts(client: OpenAI, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    # batch to respect token limits
    embs = []
    for i in range(0, len(texts), 64):
        batch = texts[i:i+64]
        resp = client.embeddings.create(model=model, input=batch)
        embs.extend([d.embedding for d in resp.data])
        time.sleep(0.1)
    return embs

# ----------------------
# Milvus setup
# ----------------------
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

def ensure_collection():
    print(f"🔍 Checking collection: {COLLECTION_NAME}")
    if not utility.has_collection(COLLECTION_NAME):
        print(f"🔄 Creating new collection: {COLLECTION_NAME}")
        fields = [
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=64),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="source_url", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="kind", dtype=DataType.VARCHAR, max_length=32),  # summary|analogy|quiz
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4096),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBED_DIM),
            FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=256),
        ]
        schema = CollectionSchema(fields, description="AI/ML YouTube video notes for RAG")
        col = Collection(name=COLLECTION_NAME, schema=schema)
        
        # Create index
        print("🔍 Creating search index...")
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE", 
            "params": {"nlist": 128}
        }
        col.create_index(field_name="embedding", index_params=index_params)
        print("✅ Collection and index created")
        return col
    else:
        print(f"✅ Using existing collection: {COLLECTION_NAME}")
        return Collection(COLLECTION_NAME)

def upsert(col: Collection, rows: List[Dict]):
    if not rows: return
    col.insert([
        [r["doc_id"] for r in rows],
        [r["title"] for r in rows],
        [r["source_url"] for r in rows],
        [r["source"] for r in rows],
        [r["kind"] for r in rows],
        [r["text"] for r in rows],
        [r["embedding"] for r in rows],
        [r["tags"] for r in rows],
    ])
    col.flush()

# ----------------------
# Main
# ----------------------
def main():
    print("🚀 YouTube to Milvus Ingestion Script")
    print("=" * 60)
    
    ap = argparse.ArgumentParser()
    ap.add_argument("--playlist", required=True, help="YouTube playlist URL")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of videos (0 = all)")
    args = ap.parse_args()

    # Connect to Milvus Cloud
    if not connect_to_milvus():
        return
    
    col = ensure_collection()

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return
    
    client = OpenAI(api_key=api_key)
    print("✅ OpenAI client initialized")
    
    # Get playlist videos
    print(f"📺 Extracting videos from playlist...")
    try:
        entries = get_video_entries(args.playlist)
        if args.limit and args.limit > 0:
            entries = entries[:args.limit]
        print(f"✅ Found {len(entries)} videos to process")
    except Exception as e:
        print(f"❌ Error extracting playlist: {e}")
        return

    batch_rows = []
    successful_videos = 0
    
    for i, e in enumerate(entries, 1):
        vid = e["id"]
        print(f"\n📹 [{i}/{len(entries)}] Processing video: {vid}")
        
        try:
            # Get metadata
            meta = get_metadata(vid)
            title = meta["title"] or vid
            desc = (meta["description"] or "")[:800]
            url = meta["url"]
            
            print(f"   📝 Title: {title[:80]}...")
            
            # Try to get transcript
            excerpt = get_caption_text(vid, max_chars=1800)
            if excerpt:
                print(f"   ✅ Got transcript: {len(excerpt)} chars")
            else:
                print(f"   ⚠️ No transcript available")

            # Generate derived notes using OpenAI
            print(f"   🤖 Generating AI content...")
            summary = llm_call(client, SYSTEM_TUTOR, PROMPT_SUMMARY.format(title=title, desc=desc, excerpt=excerpt))
            analogy = llm_call(client, SYSTEM_TUTOR, PROMPT_ANALOGY.format(title=title))
            quiz = llm_call(client, SYSTEM_TUTOR, PROMPT_QUIZ.format(title=title))

            payloads = [
                ("summary", summary),
                ("analogy", analogy),
                ("quiz", quiz),
            ]
            texts = [p[1] for p in payloads]
            
            # Generate embeddings
            print(f"   🔮 Generating embeddings...")
            embs = embed_texts(client, texts)

            for (kind, text), emb in zip(payloads, embs):
                row = {
                    "doc_id": f"{vid}__{kind}",
                    "title": title,
                    "source_url": url,
                    "source": TOPIC_TAG,
                    "kind": kind,
                    "text": text,
                    "embedding": emb,
                    "tags": "statistics,ml,education,statquest",
                }
                batch_rows.append(row)

            successful_videos += 1
            print(f"   ✅ Generated 3 content pieces (summary, analogy, quiz)")

            # Upsert in batches
            if len(batch_rows) >= 15:  # Smaller batches for reliability
                print(f"💾 Upserting {len(batch_rows)} records to Milvus...")
                upsert(col, batch_rows)
                print(f"✅ Batch upserted successfully")
                batch_rows = []
                
        except Exception as e:
            print(f"   ❌ Error processing video {vid}: {e}")
            continue

    # Final batch
    if batch_rows:
        print(f"💾 Final upsert: {len(batch_rows)} records...")
        upsert(col, batch_rows)
        print(f"✅ Final batch upserted successfully")
    
    print(f"\n🎉 Ingestion complete!")
    print(f"📊 Successfully processed: {successful_videos}/{len(entries)} videos")
    print(f"📦 Total content pieces: {successful_videos * 3}")
    print(f"💡 Collection: {COLLECTION_NAME}")
    
    # Load collection
    try:
        col.load()
        total_entities = col.num_entities
        print(f"📊 Total entities in collection: {total_entities}")
    except Exception as e:
        print(f"⚠️ Warning loading collection: {e}")

if __name__ == "__main__":
    main()

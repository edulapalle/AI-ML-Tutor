#!/usr/bin/env python3
"""
Real-Time YouTube Channel Monitor for StatQuest
================================================

Monitors StatQuest channel for new videos and automatically:
1. Detects new videos using YouTube Data API
2. Downloads transcripts 
3. Processes content and extracts keywords
4. Loads to Milvus (vector embeddings)
5. Loads to Neo4j (knowledge graph relationships)

Run as: python youtube_realtime_monitor.py
"""

import os
import time
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import requests
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure SSL certificates globally (your SSL fix)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set SSL environment variables if corp_root_ca.pem exists
ssl_cert_path = os.path.join(os.getcwd(), "corp_root_ca.pem")
if os.path.exists(ssl_cert_path):
    os.environ['SSL_CERT_FILE'] = ssl_cert_path
    os.environ['REQUESTS_CA_BUNDLE'] = ssl_cert_path
    logger.info(f"🔒 SSL certificates configured: {ssl_cert_path}")
else:
    logger.warning("⚠️ corp_root_ca.pem not found, SSL verification will be disabled")

@dataclass
class VideoInfo:
    video_id: str
    title: str
    description: str
    published_at: str
    duration: str
    view_count: int
    url: str

class YouTubeMonitor:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")  # You'll need to add this
        self.channel_configs = {
            "statquest": {
                "channel_id": "UCtYLUTtgS3k1Fg4y5tAhLbw",  # StatQuest channel ID
                "name": "StatQuest with Josh Starmer"
            }
            # Can add more channels here
        }
        self.processed_videos_file = "processed_videos.json"
        self.processed_videos = self.load_processed_videos()
        
    def load_processed_videos(self) -> Set[str]:
        """Load list of already processed video IDs"""
        try:
            if os.path.exists(self.processed_videos_file):
                with open(self.processed_videos_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_video_ids', []))
        except Exception as e:
            logger.error(f"Error loading processed videos: {e}")
        return set()
    
    def save_processed_videos(self):
        """Save list of processed video IDs"""
        try:
            data = {
                'processed_video_ids': list(self.processed_videos),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.processed_videos_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed videos: {e}")
    
    def get_recent_videos(self, channel_id: str, hours_back: int = 24) -> List[VideoInfo]:
        """Get recent videos from a channel using YouTube Data API"""
        if not self.api_key:
            logger.error("YOUTUBE_API_KEY not found in environment variables")
            return []
        
        # Calculate published after timestamp
        published_after = (datetime.now() - timedelta(hours=hours_back)).isoformat() + 'Z'
        
        try:
            # Configure SSL handling
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Search for recent videos
            search_url = "https://www.googleapis.com/youtube/v3/search"
            search_params = {
                'key': self.api_key,
                'channelId': channel_id,
                'part': 'id,snippet',
                'order': 'date',
                'type': 'video',
                'publishedAfter': published_after,
                'maxResults': 10
            }
            
            response = requests.get(search_url, params=search_params, verify=False, timeout=10)
            response.raise_for_status()
            search_data = response.json()
            
            videos = []
            video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]
            
            if not video_ids:
                return videos
            
            # Get detailed video information
            videos_url = "https://www.googleapis.com/youtube/v3/videos"
            videos_params = {
                'key': self.api_key,
                'id': ','.join(video_ids),
                'part': 'snippet,contentDetails,statistics'
            }
            
            response = requests.get(videos_url, params=videos_params, verify=False, timeout=10)
            response.raise_for_status()
            videos_data = response.json()
            
            for item in videos_data.get('items', []):
                video_info = VideoInfo(
                    video_id=item['id'],
                    title=item['snippet']['title'],
                    description=item['snippet']['description'],
                    published_at=item['snippet']['publishedAt'],
                    duration=item['contentDetails']['duration'],
                    view_count=int(item['statistics'].get('viewCount', 0)),
                    url=f"https://www.youtube.com/watch?v={item['id']}"
                )
                videos.append(video_info)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error fetching recent videos: {e}")
            return []
    
    def detect_new_videos(self) -> List[VideoInfo]:
        """Detect new videos across all monitored channels"""
        new_videos = []
        
        for channel_key, config in self.channel_configs.items():
            logger.info(f"Checking channel: {config['name']}")
            recent_videos = self.get_recent_videos(config['channel_id'])
            
            for video in recent_videos:
                if video.video_id not in self.processed_videos:
                    logger.info(f"🆕 New video detected: {video.title}")
                    new_videos.append(video)
                    
        return new_videos
    
    async def process_new_video(self, video: VideoInfo) -> bool:
        """Process a new video: transcript → Milvus → Neo4j"""
        try:
            logger.info(f"📹 Processing video: {video.title}")
            
            # 1. Get transcript
            transcript_success = await self.extract_transcript(video)
            if not transcript_success:
                logger.warning(f"⚠️ Could not get transcript for {video.title}")
                return False
            
            # 2. Process and load to Milvus
            milvus_success = await self.load_to_milvus(video)
            if not milvus_success:
                logger.error(f"❌ Failed to load to Milvus: {video.title}")
                return False
            
            # 3. Load to Neo4j
            neo4j_success = await self.load_to_neo4j(video)
            if not neo4j_success:
                logger.error(f"❌ Failed to load to Neo4j: {video.title}")
                return False
            
            # 4. Mark as processed
            self.processed_videos.add(video.video_id)
            self.save_processed_videos()
            
            logger.info(f"✅ Successfully processed: {video.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing video {video.title}: {e}")
            return False
    
    async def extract_transcript(self, video: VideoInfo) -> bool:
        """Extract transcript from video using existing approach"""
        try:
            logger.info(f"📝 Extracting transcript for video: {video.video_id}")
            
            # Use yt-dlp first (your preferred method)
            transcript_text = await self.get_transcript_with_ytdlp(video.video_id)
            
            # Fallback to youtube-transcript-api if yt-dlp fails
            if not transcript_text:
                transcript_text = await self.get_transcript_with_api(video.video_id)
            
            if transcript_text:
                # Save transcript to file for Milvus processing
                transcript_file = f"transcripts/{video.video_id}_transcript.txt"
                os.makedirs("transcripts", exist_ok=True)
                
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(transcript_text)
                
                logger.info(f"📝 Transcript extracted: {len(transcript_text)} characters")
                return True
            else:
                logger.warning("⚠️ Could not extract transcript")
                return False
            
        except Exception as e:
            logger.error(f"Transcript extraction failed: {e}")
            return False
    
    async def get_transcript_with_ytdlp(self, video_id: str) -> str:
        """Get transcript using yt-dlp (your preferred method)"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writeinfojson': False,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'writesubtitlesformat': 'json3',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # Check for subtitles
                subtitle_data = video_info.get('subtitles', {}) or video_info.get('automatic_captions', {})
                
                if 'en' in subtitle_data and subtitle_data['en']:
                    subtitle_url = subtitle_data['en'][0]['url']
                    
                    # Download and parse subtitles
                    import requests
                    import urllib3
                    import json
                    
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    session = requests.Session()
                    session.verify = False
                    
                    response = session.get(subtitle_url, timeout=30)
                    if response.status_code == 200:
                        subtitle_json = json.loads(response.text)
                        
                        full_text = ""
                        if 'events' in subtitle_json:
                            for event in subtitle_json['events']:
                                if 'segs' in event and event['segs']:
                                    for seg in event['segs']:
                                        if 'utf8' in seg:
                                            full_text += seg['utf8'].strip() + " "
                        
                        return full_text.strip()
            
            return ""
            
        except Exception as e:
            logger.warning(f"yt-dlp transcript extraction failed: {e}")
            return ""
    
    async def get_transcript_with_api(self, video_id: str) -> str:
        """Fallback: Get transcript using youtube-transcript-api"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Create instance and get transcript
            api = YouTubeTranscriptApi()
            transcript = api.get_transcript(video_id, languages=['en'])
            
            # Join all text segments
            full_text = ' '.join([entry['text'] for entry in transcript])
            return full_text
            
        except Exception as e:
            logger.warning(f"youtube-transcript-api failed: {e}")
            return ""
    
    async def load_to_milvus(self, video: VideoInfo) -> bool:
        """Load video content to Milvus vector database using existing pipeline"""
        try:
            logger.info("🔍 Processing video for Milvus...")
            
            # Import OpenAI for embeddings and content generation
            import openai
            from pymilvus import connections, Collection, utility
            
            # Initialize OpenAI client
            openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Connect to Milvus
            if not self.connect_to_milvus():
                return False
            
            # Collection name from your existing code
            collection_name = "youtube_creator_videos"
            
            # Generate AI content using your existing prompts
            title = video.title
            description = video.description[:800]
            
            # Read transcript if available
            transcript_file = f"transcripts/{video.video_id}_transcript.txt"
            excerpt = ""
            if os.path.exists(transcript_file):
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    excerpt = f.read()[:1800]
            
            # System prompt from your existing code
            system_tutor = (
                "You are a kind ML tutor for a 10-year-old. "
                "Use plain language, short sentences, no equations. "
                "Be accurate and safe."
            )
            
            # Generate content using your existing prompts
            summary_prompt = (
                "Summarize the main idea of this ML video for a 10-year-old in 4–5 short sentences. "
                "Avoid formulas and jargon. End with when/why it's useful.\n\n"
                f"TITLE: {title}\nDESCRIPTION: {description}\nTRANSCRIPT_EXCERPT:\n{excerpt}"
            )
            
            analogy_prompt = (
                "Create one child-friendly analogy for the topic of this video, "
                "using a concrete everyday situation (sports, cooking, or playground). "
                f"Write 4–5 short sentences.\n\nTITLE: {title}\n"
            )
            
            quiz_prompt = (
                "Write one simple question and a short answer about this video topic for a 10-year-old. "
                f"Output exactly two lines: 'Q: ...' and 'A: ...'.\n\nTITLE: {title}\n"
            )
            
            # Generate content
            logger.info("🤖 Generating AI content...")
            summary = await self.llm_call(openai_client, system_tutor, summary_prompt)
            analogy = await self.llm_call(openai_client, system_tutor, analogy_prompt)
            quiz = await self.llm_call(openai_client, system_tutor, quiz_prompt)
            
            # Generate embeddings
            texts = [summary, analogy, quiz]
            logger.info("🔮 Generating embeddings...")
            embeddings = await self.generate_embeddings(openai_client, texts)
            
            # Prepare data for Milvus
            collection = Collection(collection_name)
            batch_rows = []
            
            for (kind, text), embedding in zip([("summary", summary), ("analogy", analogy), ("quiz", quiz)], embeddings):
                row = {
                    "doc_id": f"{video.video_id}__{kind}",
                    "title": title,
                    "source_url": video.url,
                    "source": "statquest",
                    "kind": kind,
                    "text": text,
                    "embedding": embedding,
                    "tags": "statistics,ml,education,statquest",
                }
                batch_rows.append(row)
            
            # Insert to Milvus
            logger.info("💾 Inserting to Milvus...")
            if batch_rows:
                collection.insert([
                    [r["doc_id"] for r in batch_rows],
                    [r["title"] for r in batch_rows],
                    [r["source_url"] for r in batch_rows],
                    [r["source"] for r in batch_rows],
                    [r["kind"] for r in batch_rows],
                    [r["text"] for r in batch_rows],
                    [r["embedding"] for r in batch_rows],
                    [r["tags"] for r in batch_rows],
                ])
                collection.flush()
            
            logger.info("✅ Milvus loading completed")
            return True
            
        except Exception as e:
            logger.error(f"Milvus loading failed: {e}")
            return False
    
    async def load_to_neo4j(self, video: VideoInfo) -> bool:
        """Load video metadata and relationships to Neo4j using existing pipeline"""
        try:
            logger.info("🕸️ Loading to Neo4j...")
            
            # Import Neo4j driver
            from neo4j import GraphDatabase
            
            # Connect to Neo4j
            uri = os.getenv("NEO4J_URI")
            username = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD")
            
            if not uri or not password:
                logger.error("Neo4j connection details not found")
                return False
            
            # Convert neo4j+s:// to bolt+s:// for direct connection (your SSL fix)
            if uri.startswith("neo4j+s://"):
                uri = uri.replace("neo4j+s://", "bolt+s://")
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            with driver.session(database="neo4j") as session:
                # Create video node
                video_query = """
                MERGE (v:Video {video_id: $video_id})
                SET v.title = $title,
                    v.url = $url,
                    v.source = $source,
                    v.view_count = $view_count,
                    v.duration = $duration,
                    v.published_at = $published_at,
                    v.updated_at = datetime()
                RETURN v
                """
                
                session.run(video_query, {
                    'video_id': video.video_id,
                    'title': video.title,
                    'url': video.url,
                    'source': 'statquest',
                    'view_count': video.view_count,
                    'duration': video.duration,
                    'published_at': video.published_at
                })
                
                # Create or merge channel node
                channel_query = """
                MERGE (c:Channel {name: $channel_name})
                RETURN c
                """
                session.run(channel_query, {'channel_name': 'StatQuest with Josh Starmer'})
                
                # Create relationship between video and channel
                relationship_query = """
                MATCH (v:Video {video_id: $video_id})
                MATCH (c:Channel {name: $channel_name})
                MERGE (v)-[:UPLOADED_BY]->(c)
                """
                session.run(relationship_query, {
                    'video_id': video.video_id,
                    'channel_name': 'StatQuest with Josh Starmer'
                })
                
                # Extract and link to ML concepts using your existing keyword mapping
                title_lower = video.title.lower()
                concept_keywords = {
                    "linear regression": "linear-regression",
                    "logistic regression": "logistic-regression", 
                    "decision tree": "decision-trees",
                    "random forest": "random-forest",
                    "support vector": "svm",
                    "k-means": "k-means",
                    "pca": "pca",
                    "overfitting": "overfitting",
                    "cross validation": "cross-val",
                    "neural network": "neural-networks",
                    "cnn": "cnn",
                    "rnn": "rnn",
                    "transformer": "transformers",
                    "embedding": "embeddings"
                }
                
                # Link to concepts based on title
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
                    session.run(concept_rel_query, {
                        'video_id': video.video_id,
                        'concept_slug': concept_slug
                    })
                
                logger.info(f"✅ Neo4j: Video linked to {len(linked_concepts)} concepts")
            
            driver.close()
            logger.info("✅ Neo4j loading completed")
            return True
            
        except Exception as e:
            logger.error(f"Neo4j loading failed: {e}")
            return False
    
    def connect_to_milvus(self) -> bool:
        """Connect to Milvus Cloud"""
        try:
            from pymilvus import connections
            
            milvus_uri = os.getenv('MILVUS_URI')
            milvus_token = os.getenv('MILVUS_TOKEN')
            
            if not milvus_uri or not milvus_token:
                logger.error("MILVUS_URI or MILVUS_TOKEN not found in environment")
                return False
            
            connections.connect(
                alias="realtime_monitor",
                uri=milvus_uri,
                token=milvus_token
            )
            
            logger.info("✅ Connected to Milvus Cloud")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
    
    async def llm_call(self, client, system: str, user: str, model: str = "gpt-4o-mini") -> str:
        """Make LLM call with retry logic"""
        import time
        import random
        
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ]
                )
                return (response.choices[0].message.content or "").strip()
                
            except Exception as e:
                if attempt == 2:
                    raise e
                wait_time = (2 ** attempt) + random.random()
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}, retrying in {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        return ""
    
    async def generate_embeddings(self, client, texts: list, model: str = "text-embedding-3-small") -> list:
        """Generate embeddings for texts"""
        try:
            # Process in batches to respect token limits
            embeddings = []
            batch_size = 32
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                response = client.embeddings.create(model=model, input=batch)
                embeddings.extend([d.embedding for d in response.data])
                await asyncio.sleep(0.1)  # Small delay between batches
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

class RealTimePipeline:
    def __init__(self, check_interval_minutes: int = 30):
        self.monitor = YouTubeMonitor()
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.running = False
    
    async def start_monitoring(self):
        """Start the real-time monitoring pipeline"""
        self.running = True
        logger.info("🚀 Starting YouTube real-time monitoring pipeline")
        logger.info(f"⏰ Check interval: {self.check_interval//60} minutes")
        
        while self.running:
            try:
                # Detect new videos
                new_videos = self.monitor.detect_new_videos()
                
                if new_videos:
                    logger.info(f"🔥 Found {len(new_videos)} new videos to process")
                    
                    # Process each new video
                    for video in new_videos:
                        success = await self.monitor.process_new_video(video)
                        if success:
                            logger.info(f"🎉 Successfully processed: {video.title}")
                        else:
                            logger.error(f"💥 Failed to process: {video.title}")
                        
                        # Small delay between videos to avoid rate limiting
                        await asyncio.sleep(5)
                else:
                    logger.info("😴 No new videos found")
                
                # Wait before next check
                logger.info(f"⏳ Sleeping for {self.check_interval//60} minutes...")
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("⛔ Received stop signal")
                self.running = False
                break
            except Exception as e:
                logger.error(f"💥 Pipeline error: {e}")
                logger.info("🔄 Continuing after error...")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop_monitoring(self):
        """Stop the monitoring pipeline"""
        self.running = False
        logger.info("🛑 Stopping monitoring pipeline")

# CLI Interface
async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Real-Time Monitor')
    parser.add_argument('--interval', type=int, default=30, 
                       help='Check interval in minutes (default: 30)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: check once and exit')
    
    args = parser.parse_args()
    
    pipeline = RealTimePipeline(check_interval_minutes=args.interval)
    
    if args.test:
        # Test mode: run once
        logger.info("🧪 Running in test mode")
        new_videos = pipeline.monitor.detect_new_videos()
        
        if new_videos:
            logger.info(f"Found {len(new_videos)} new videos:")
            for video in new_videos:
                logger.info(f"  📹 {video.title} ({video.published_at})")
        else:
            logger.info("No new videos found")
    else:
        # Production mode: continuous monitoring
        try:
            await pipeline.start_monitoring()
        except KeyboardInterrupt:
            logger.info("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())

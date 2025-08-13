#!/usr/bin/env python3
"""
Single YouTube Video Scraper for Neo4j Knowledge Graph
Scrapes metadata and transcript from a single YouTube video and stores in Neo4j
"""

# Set SSL certificate environment variables BEFORE importing any libraries
import os
from dotenv import load_dotenv
load_dotenv()

# Configure SSL certificates for all HTTPS requests
ssl_cert = os.getenv("SSL_CERT_FILE")
requests_ca = os.getenv("REQUESTS_CA_BUNDLE")

if ssl_cert and requests_ca:
    os.environ['REQUESTS_CA_BUNDLE'] = requests_ca
    os.environ['SSL_CERT_FILE'] = ssl_cert
    print(f"🔒 SSL certificates configured: {ssl_cert}")
else:
    print("⚠️ SSL certificates not configured")

import re
import json
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from neo4j import GraphDatabase
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeSingleScraper:
    """Scrapes a single YouTube video and stores in Neo4j knowledge graph"""
    
    def __init__(self):
        """Initialize the scraper with Neo4j connection"""
        self.driver = self._connect_to_neo4j()
        if not self.driver:
            raise ConnectionError("Failed to connect to Neo4j")
    
    def _connect_to_neo4j(self):
        """Connect to Neo4j Aura instance using SSL certificate solution"""
        
        # Get Neo4j connection details from .env
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            print("❌ Missing Neo4j environment variables")
            return None
        
        try:
            # Convert neo4j+s:// to bolt+s:// for direct connection
            if uri.startswith("neo4j+s://"):
                direct_uri = uri.replace("neo4j+s://", "bolt+s://")
                print(f"🔄 Using direct connection: {direct_uri}")
            else:
                direct_uri = uri
            
            # Create driver
            driver = GraphDatabase.driver(direct_uri, auth=(username, password))
            driver.verify_connectivity()
            print("✅ Neo4j connection established")
            return driver
            
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            return None
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        try:
            # Handle different YouTube URL formats
            if 'youtube.com/watch' in url:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                video_id = query_params.get('v', [None])[0]
            elif 'youtu.be/' in url:
                video_id = url.split('youtu.be/')[-1].split('?')[0]
            elif 'youtube.com/embed/' in url:
                video_id = url.split('youtube.com/embed/')[-1].split('?')[0]
            else:
                # Try to find video ID pattern
                match = re.search(r'[a-zA-Z0-9_-]{11}', url)
                video_id = match.group(0) if match else None
            
            if not video_id or len(video_id) != 11:
                raise ValueError("Invalid video ID format")
            
            return video_id
            
        except Exception as e:
            print(f"❌ Error extracting video ID: {e}")
            return None
    
    def extract_keywords(self, title, description, tags):
        """Extract relevant keywords from video metadata using simple regex approach"""
        try:
            print("🔍 Extracting keywords from video metadata...")
            
            # Combine all text sources
            text_content = f"{title} {description}"
            if tags:
                text_content += f" {' '.join(tags)}"
            
            # Convert to lowercase and clean
            text_content = text_content.lower()
            text_content = re.sub(r'[^\w\s]', ' ', text_content)  # Remove special characters
            
            # Simple word extraction using regex
            words = re.findall(r'\b\w{3,}\b', text_content)
            
            # Common stop words to filter out
            stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
                'after', 'above', 'below', 'between', 'among', 'within', 'without',
                'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be',
                'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                'would', 'could', 'should', 'may', 'might', 'can', 'shall', 'must',
                'what', 'when', 'where', 'why', 'how', 'which', 'who', 'whom', 'whose',
                'https', 'www', 'com', 'you', 'want', 'get', 'like', 'know', 'see',
                'make', 'take', 'go', 'come', 'look', 'find', 'think', 'feel', 'say',
                'tell', 'ask', 'give', 'put', 'set', 'let', 'try', 'use', 'work',
                'play', 'read', 'write', 'speak', 'hear', 'watch', 'help', 'show',
                'start', 'stop', 'begin', 'end', 'first', 'last', 'next', 'previous',
                'new', 'old', 'good', 'bad', 'big', 'small', 'high', 'low', 'long',
                'short', 'fast', 'slow', 'easy', 'hard', 'simple', 'complex', 'open',
                'close', 'left', 'right', 'top', 'bottom', 'front', 'back', 'inside',
                'outside', 'here', 'there', 'now', 'then', 'today', 'tomorrow', 'yesterday'
            }
            
            # Filter out stop words and short words
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            
            # ML/AI specific keywords to prioritize
            ml_keywords = {
                'machine', 'learning', 'deep', 'neural', 'network', 'artificial', 'intelligence',
                'ai', 'ml', 'data', 'science', 'computer', 'vision', 'nlp', 'natural', 'language', 'processing',
                'reinforcement', 'supervised', 'unsupervised', 'regression', 'classification', 'clustering',
                'optimization', 'gradient', 'descent', 'backpropagation', 'convolutional', 'recurrent',
                'transformer', 'bert', 'gpt', 'tensorflow', 'pytorch', 'scikit', 'pandas', 'numpy',
                'matplotlib', 'statistics', 'probability', 'linear', 'algebra', 'calculus', 'algorithm',
                'preprocessing', 'feature', 'engineering', 'evaluation', 'validation', 'overfitting',
                'underfitting', 'regularization', 'dropout', 'batch', 'normalization', 'tutorial',
                'introduction', 'basics', 'fundamentals', 'concepts', 'theory', 'practice', 'examples'
            }
            
            # Count word frequencies
            word_counts = {}
            for word in filtered_words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # Prioritize ML/AI keywords
            prioritized_keywords = []
            for word, count in word_counts.items():
                if word in ml_keywords:
                    prioritized_keywords.append((word, count + 5))  # Boost ML keywords
                else:
                    prioritized_keywords.append((word, count))
            
            # Sort by frequency (including boost)
            prioritized_keywords.sort(key=lambda x: x[1], reverse=True)
            
            # Extract top keywords (limit to 15)
            keywords = [word for word, count in prioritized_keywords[:15]]
            
            print(f"✅ Extracted {len(keywords)} keywords: {', '.join(keywords[:10])}{'...' if len(keywords) > 10 else ''}")
            return keywords
            
        except Exception as e:
            print(f"⚠️ Error extracting keywords: {e}")
            # Fallback: extract basic keywords from title
            fallback_keywords = re.findall(r'\b\w{3,}\b', title.lower())
            return fallback_keywords[:10]
    
    def scrape_video_metadata(self, video_id):
        """Scrape video metadata using yt-dlp"""
        try:
            print(f"🎥 Scraping metadata for video: {video_id}")
            
            # Configure yt-dlp options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writeinfojson': False,
                'skip_download': True,  # We only want metadata, not the video
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                video_info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # Extract relevant metadata
                # Extract keywords from metadata
                keywords = self.extract_keywords(
                    video_info.get('title', ''),
                    video_info.get('description', ''),
                    video_info.get('tags', [])
                )
                
                metadata = {
                    'video_id': video_id,
                    'title': video_info.get('title', ''),
                    'description': video_info.get('description', ''),
                    'duration': video_info.get('duration', 0),
                    'view_count': video_info.get('view_count', 0),
                    'like_count': video_info.get('like_count', 0),
                    'upload_date': video_info.get('upload_date', ''),
                    'channel': video_info.get('channel', ''),
                    'channel_id': video_info.get('channel_id', ''),
                    'tags': video_info.get('tags', []),
                    'categories': video_info.get('categories', []),
                    'thumbnail': video_info.get('thumbnail', ''),
                    'webpage_url': video_info.get('webpage_url', ''),
                    'keywords': keywords,
                    'scraped_at': datetime.now().isoformat()
                }
                
                print(f"✅ Metadata extracted: {metadata['title']}")
                return metadata
                
        except Exception as e:
            print(f"❌ Error scraping metadata: {e}")
            return None
    
    def get_video_transcript(self, video_id):
        """Get video transcript using yt-dlp (more reliable than YouTube Transcript API)"""
        try:
            print(f"📝 Getting transcript for video: {video_id}")
            
            # Configure yt-dlp options for transcript extraction
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writeinfojson': False,
                'skip_download': True,  # We only want metadata and transcript
                'writesubtitles': True,  # Enable subtitle writing
                'writeautomaticsub': True,  # Enable automatic subtitle writing
                'subtitleslangs': ['en'],  # Prefer English subtitles
                'writesubtitlesformat': 'json3',  # Get subtitles in JSON format
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info including subtitles
                video_info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # Check if we have subtitles
                if 'subtitles' in video_info and video_info['subtitles']:
                    print("✅ Found manual subtitles")
                    subtitle_data = video_info['subtitles']
                elif 'automatic_captions' in video_info and video_info['automatic_captions']:
                    print("✅ Found automatic captions")
                    subtitle_data = video_info['automatic_captions']
                else:
                    print("⚠️ No subtitles found, will use description and tags instead")
                    return None
                
                # Process subtitles into segments
                segments = []
                full_text = ""
                
                # Get English subtitles if available
                if 'en' in subtitle_data:
                    subtitle_list = subtitle_data['en']
                    if subtitle_list:
                        # Get the first available subtitle format
                        subtitle_url = subtitle_list[0]['url']
                        
                        # Try to download subtitle with SSL verification disabled
                        try:
                            import requests
                            import urllib3
                            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                            
                            # Create session with SSL verification disabled
                            session = requests.Session()
                            session.verify = False
                            
                            print("🔒 Attempting to download subtitle with SSL verification disabled...")
                            response = session.get(subtitle_url, timeout=30)
                            
                            if response.status_code == 200:
                                subtitle_content = response.text
                                
                                # Parse JSON3 format subtitles
                                import json
                                try:
                                    subtitle_json = json.loads(subtitle_content)
                                    if 'events' in subtitle_json:
                                        for event in subtitle_json['events']:
                                            if 'segs' in event and event['segs']:
                                                for seg in event['segs']:
                                                    if 'utf8' in seg:
                                                        text = seg['utf8']
                                                        start_time = event.get('tStartMs', 0) / 1000  # Convert to seconds
                                                        duration = event.get('dDurationMs', 0) / 1000  # Convert to seconds
                                                        
                                                        if text.strip():
                                                            segment_info = {
                                                                'start': start_time,
                                                                'duration': duration,
                                                                'text': text.strip()
                                                            }
                                                            segments.append(segment_info)
                                                            full_text += text.strip() + " "
                                        
                                        if segments:
                                            transcript_info = {
                                                'segments': segments,
                                                'full_text': full_text.strip(),
                                                'total_segments': len(segments),
                                                'total_duration': sum(seg['duration'] for seg in segments)
                                            }
                                            
                                            print(f"✅ Transcript extracted: {len(segments)} segments")
                                            return transcript_info
                                except json.JSONDecodeError:
                                    print("⚠️ Could not parse subtitle JSON")
                            else:
                                print(f"⚠️ Failed to download subtitle: HTTP {response.status_code}")
                                
                        except Exception as e:
                            print(f"⚠️ Error downloading subtitle: {e}")
                
                print("⚠️ No transcript segments found")
                return None
                    
        except Exception as e:
            print(f"❌ Error getting transcript with yt-dlp: {e}")
            return None
    
    def _get_transcript_alternative(self, video_id):
        """Alternative method to get transcript if yt-dlp fails"""
        try:
            print("🔄 Trying alternative transcript method...")
            
            # This is a fallback method - you could implement other approaches here
            # For now, we'll return None and continue with metadata only
            print("⚠️ Alternative method not implemented yet")
            return None
            
        except Exception as e:
            print(f"❌ Alternative transcript method failed: {e}")
            return None
    
    def create_neo4j_schema(self):
        """Create Neo4j schema for video knowledge graph"""
        try:
            with self.driver.session(database="neo4j") as session:
                
                # Create constraints and indexes
                schema_queries = [
                    # Video node constraints
                    "CREATE CONSTRAINT video_id_unique IF NOT EXISTS FOR (v:Video) REQUIRE v.video_id IS UNIQUE",
                    "CREATE INDEX video_title_index IF NOT EXISTS FOR (v:Video) ON (v.title)",
                    "CREATE INDEX video_channel_index IF NOT EXISTS FOR (v:Video) ON (v.channel)",
                    
                    # Channel node constraints
                    "CREATE CONSTRAINT channel_id_unique IF NOT EXISTS FOR (c:Channel) REQUIRE c.channel_id IS UNIQUE",
                    "CREATE INDEX channel_name_index IF NOT EXISTS FOR (c:Channel) ON (c.name)",
                    
                    # Transcript segment constraints
                    "CREATE INDEX segment_text_index IF NOT EXISTS FOR (s:TranscriptSegment) ON (s.text)",
                    
                    # Keyword constraints
                    "CREATE CONSTRAINT keyword_name_unique IF NOT EXISTS FOR (k:Keyword) REQUIRE k.name IS UNIQUE",
                    "CREATE INDEX keyword_name_index IF NOT EXISTS FOR (k:Keyword) ON (k.name)",
                    
                    # ML Concept constraints (for future integration)
                    "CREATE CONSTRAINT concept_name_unique IF NOT EXISTS FOR (m:MLConcept) REQUIRE m.name IS UNIQUE",
                    "CREATE INDEX concept_category_index IF NOT EXISTS FOR (m:MLConcept) ON (m.category)"
                ]
                
                for query in schema_queries:
                    try:
                        session.run(query)
                    except Exception as e:
                        # Ignore errors if constraints already exist
                        if "already exists" not in str(e).lower():
                            print(f"⚠️ Schema creation warning: {e}")
                
                print("✅ Neo4j schema created/verified")
                
        except Exception as e:
            print(f"❌ Error creating schema: {e}")
    
    def store_video_in_neo4j(self, metadata, transcript_info):
        """Store video data in Neo4j knowledge graph"""
        try:
            with self.driver.session(database="neo4j") as session:
                
                # Create or merge video node
                video_query = """
                MERGE (v:Video {video_id: $video_id})
                SET v.title = $title,
                    v.description = $description,
                    v.duration = $duration,
                    v.view_count = $view_count,
                    v.like_count = $like_count,
                    v.upload_date = $upload_date,
                    v.thumbnail = $thumbnail,
                    v.webpage_url = $webpage_url,
                    v.scraped_at = $scraped_at
                RETURN v
                """
                
                video_params = {
                    'video_id': metadata['video_id'],
                    'title': metadata['title'],
                    'description': metadata['description'][:1000],  # Limit description length
                    'duration': metadata['duration'],
                    'view_count': metadata['view_count'],
                    'like_count': metadata['like_count'],
                    'upload_date': metadata['upload_date'],
                    'thumbnail': metadata['thumbnail'],
                    'webpage_url': metadata['webpage_url'],
                    'scraped_at': metadata['scraped_at']
                }
                
                session.run(video_query, video_params)
                print(f"✅ Video node created: {metadata['title']}")
                
                # Create or merge channel node
                channel_query = """
                MERGE (c:Channel {channel_id: $channel_id})
                SET c.name = $channel_name
                RETURN c
                """
                
                channel_params = {
                    'channel_id': metadata['channel_id'],
                    'channel_name': metadata['channel']
                }
                
                session.run(channel_query, channel_params)
                print(f"✅ Channel node created: {metadata['channel']}")
                
                # Create relationship between video and channel
                relationship_query = """
                MATCH (v:Video {video_id: $video_id})
                MATCH (c:Channel {channel_id: $channel_id})
                MERGE (v)-[:UPLOADED_BY]->(c)
                """
                
                session.run(relationship_query, {
                    'video_id': metadata['video_id'],
                    'channel_id': metadata['channel_id']
                })
                print("✅ Video-Channel relationship created")
                
                # Store transcript segments
                if transcript_info and transcript_info['segments']:
                    for i, segment in enumerate(transcript_info['segments']):
                        segment_query = """
                        CREATE (s:TranscriptSegment {
                            segment_id: $segment_id,
                            start_time: $start_time,
                            duration: $duration,
                            text: $text
                        })
                        """
                        
                        segment_params = {
                            'segment_id': f"{metadata['video_id']}_seg_{i}",
                            'start_time': segment['start'],
                            'duration': segment['duration'],
                            'text': segment['text']
                        }
                        
                        session.run(segment_query, segment_params)
                        
                        # Create relationship between video and segment
                        segment_rel_query = """
                        MATCH (v:Video {video_id: $video_id})
                        MATCH (s:TranscriptSegment {segment_id: $segment_id})
                        MERGE (v)-[:CONTAINS_SEGMENT]->(s)
                        """
                        
                        session.run(segment_rel_query, {
                            'video_id': metadata['video_id'],
                            'segment_id': segment_params['segment_id']
                        })
                    
                    print(f"✅ Transcript segments stored: {len(transcript_info['segments'])} segments")
                
                # Store keywords as nodes and relationships
                if metadata['keywords']:
                    for keyword in metadata['keywords']:
                        keyword_query = """
                        MERGE (k:Keyword {name: $keyword_name})
                        """
                        session.run(keyword_query, {'keyword_name': keyword})
                        
                        # Create relationship between video and keyword
                        keyword_rel_query = """
                        MATCH (v:Video {video_id: $video_id})
                        MATCH (k:Keyword {name: $keyword_name})
                        MERGE (v)-[:HAS_KEYWORD]->(k)
                        """
                        session.run(keyword_rel_query, {
                            'video_id': metadata['video_id'],
                            'keyword_name': keyword
                        })
                    
                    print(f"✅ Keywords stored: {len(metadata['keywords'])} keywords")
                
                # Store tags as nodes and relationships
                if metadata['tags']:
                    for tag in metadata['tags'][:10]:  # Limit to first 10 tags
                        tag_query = """
                        MERGE (t:Tag {name: $tag_name})
                        """
                        session.run(tag_query, {'tag_name': tag})
                        
                        # Create relationship between video and tag
                        tag_rel_query = """
                        MATCH (v:Video {video_id: $video_id})
                        MATCH (t:Tag {name: $tag_name})
                        MERGE (v)-[:HAS_TAG]->(t)
                        """
                        session.run(tag_rel_query, {
                            'video_id': metadata['video_id'],
                            'tag_name': tag
                        })
                    
                    print(f"✅ Tags stored: {len(metadata['tags'])} tags")
                
                return True
                
        except Exception as e:
            print(f"❌ Error storing in Neo4j: {e}")
            return False
    
    def scrape_and_store_video(self, youtube_url):
        """Main function to scrape and store a single YouTube video"""
        
        print("🚀 YouTube Single Video Scraper")
        print("=" * 60)
        
        # Extract video ID
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            print("❌ Could not extract video ID from URL")
            return False
        
        print(f"🎯 Processing video ID: {video_id}")
        
        # Create Neo4j schema
        self.create_neo4j_schema()
        
        # Scrape video metadata
        metadata = self.scrape_video_metadata(video_id)
        if not metadata:
            print("❌ Failed to scrape video metadata")
            return False
        
        # Get video transcript
        transcript_info = self.get_video_transcript(video_id)
        if not transcript_info:
            print("⚠️ Could not get transcript, continuing with metadata only")
        
        # Store in Neo4j
        success = self.store_video_in_neo4j(metadata, transcript_info)
        
        if success:
            print("\n🎉 Video successfully added to Neo4j knowledge graph!")
            print(f"📊 Video: {metadata['title']}")
            print(f"📺 Channel: {metadata['channel']}")
            print(f"⏱️ Duration: {metadata['duration']} seconds")
            print(f"👀 Views: {metadata['view_count']:,}")
            if transcript_info:
                print(f"📝 Transcript: {transcript_info['total_segments']} segments")
            print(f"🔑 Keywords: {len(metadata['keywords'])} keywords")
            print(f"🏷️ Tags: {len(metadata['tags'])} tags")
        else:
            print("❌ Failed to store video in Neo4j")
        
        return success
    
    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            print("🔌 Neo4j connection closed")

def main():
    """Main function to run the scraper"""
    
    # Check if URL is provided as command line argument
    import sys
    if len(sys.argv) != 2:
        print("Usage: python youtube_single_scraper.py <youtube_url>")
        print("Example: python youtube_single_scraper.py https://www.youtube.com/watch?v=aircAruvnKk&list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi")
        return
    
    youtube_url = sys.argv[1]
    
    try:
        # Create scraper instance
        scraper = YouTubeSingleScraper()
        
        # Scrape and store video
        success = scraper.scrape_and_store_video(youtube_url)
        
        if success:
            print("\n💡 Next Steps:")
            print("   1. Check Neo4j browser to see the stored data")
            print("   2. Run neo4j_basic_read.py to verify data was stored")
            print("   3. Create ML concept relationships")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
    finally:
        # Always close the connection
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main()

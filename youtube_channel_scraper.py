#!/usr/bin/env python3
"""
YouTube Channel Scraper - Working Version
Scrapes verified working AI/ML YouTube channels
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
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeChannelScraperWorking:
    """Scrapes verified working AI/ML YouTube channels"""
    
    def __init__(self):
        """Initialize the scraper with Neo4j connection"""
        self.driver = self._connect_to_neo4j()
        if not self.driver:
            raise ConnectionError("Failed to connect to Neo4j")
        
        # Verified working AI/ML YouTube channels
        self.ai_ml_channels = {
            '3Blue1Brown': {
                'channel_id': 'UCYO_jab_esuFRV4b17AJtAw',
                'description': 'Mathematics and computer science education',
                'topics': ['mathematics', 'neural networks', 'linear algebra', 'calculus', 'algorithms']
            },
            'StatQuest': {
                'channel_id': '@statquest',
                'description': 'Statistics, Machine Learning, Data Science, and AI explained simply',
                'topics': ['statistics', 'machine learning', 'data science', 'regression', 'classification', 'clustering', 'AI']
            },
            'Two Minute Papers': {
                'channel_id': 'UCbfYPyITQ-7l4upoX8nvctg',
                'description': 'Latest AI research papers explained',
                'topics': ['AI research', 'deep learning', 'computer vision', 'NLP', 'generative AI']
            },
            'Lex Fridman': {
                'channel_id': 'UCSHZKyAWbqitGVtj8tLc3Qw',
                'description': 'AI, science, and technology discussions',
                'topics': ['artificial intelligence', 'machine learning', 'robotics', 'neuroscience', 'technology']
            },
            'Sentdex': {
                'channel_id': 'UCfzlCWGWYyIQ0aLC8wSN8lg',
                'description': 'Python programming and machine learning tutorials',
                'topics': ['python', 'machine learning', 'deep learning', 'tensorflow', 'pytorch']
            },
            'DeepMind': {
                'channel_id': 'UC0m0i6mJqBmUyJhFf2SYaGA',
                'description': 'Official DeepMind research and developments',
                'topics': ['AI research', 'deep learning', 'reinforcement learning', 'neuroscience', 'robotics']
            }
        }
    
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
    
    def extract_keywords(self, title, description, tags):
        """Extract relevant keywords from video metadata using simple regex approach"""
        try:
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
            
            return keywords
            
        except Exception as e:
            print(f"⚠️ Error extracting keywords: {e}")
            # Fallback: extract basic keywords from title
            fallback_keywords = re.findall(r'\b\w{3,}\b', title.lower())
            return fallback_keywords[:10]
    
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
    
    def scrape_channel_videos(self, channel_name, channel_info, max_videos=30):
        """Scrape videos from a specific channel"""
        try:
            print(f"\n🎬 Scraping channel: {channel_name}")
            print(f"📺 Channel ID: {channel_info['channel_id']}")
            print(f"📝 Description: {channel_info['description']}")
            print(f"🏷️ Topics: {', '.join(channel_info['topics'])}")
            print("-" * 60)
            
            # Configure yt-dlp options for channel scraping
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Extract flat info for faster processing
                'writeinfojson': False,
                'skip_download': True,  # We only want metadata
                'playlist_items': f'1-{max_videos}',  # Limit to max_videos
            }
            
            # Channel URL format - handle both channel IDs and @ handles
            if channel_info['channel_id'].startswith('@'):
                channel_url = f"https://www.youtube.com/{channel_info['channel_id']}/videos"
            else:
                channel_url = f"https://www.youtube.com/channel/{channel_info['channel_id']}/videos"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract channel info
                channel_data = ydl.extract_info(channel_url, download=False)
                
                if not channel_data or 'entries' not in channel_data:
                    print(f"⚠️ No videos found for channel: {channel_name}")
                    return []
                
                videos = []
                for entry in channel_data['entries']:
                    if entry:
                        video_info = {
                            'video_id': entry.get('id'),
                            'title': entry.get('title', ''),
                            'description': entry.get('description', ''),
                            'duration': entry.get('duration', 0),
                            'view_count': entry.get('view_count', 0),
                            'like_count': entry.get('like_count', 0),
                            'upload_date': entry.get('upload_date', ''),
                            'channel': channel_name,
                            'channel_id': channel_info['channel_id'],
                            'tags': entry.get('tags', []),
                            'categories': entry.get('categories', []),
                            'thumbnail': entry.get('thumbnail', ''),
                            'webpage_url': entry.get('webpage_url', ''),
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Extract keywords
                        video_info['keywords'] = self.extract_keywords(
                            video_info['title'],
                            video_info['description'],
                            video_info['tags']
                        )
                        
                        videos.append(video_info)
                        
                        if len(videos) % 10 == 0:
                            print(f"📊 Processed {len(videos)} videos...")
                
                print(f"✅ Channel {channel_name}: Found {len(videos)} videos")
                return videos
                
        except Exception as e:
            print(f"❌ Error scraping channel {channel_name}: {e}")
            return []
    
    def store_video_in_neo4j(self, metadata):
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
                
                # Create or merge channel node
                channel_query = """
                MERGE (c:Channel {channel_id: $channel_id})
                SET c.name = $channel_name,
                    c.description = $channel_description,
                    c.topics = $channel_topics
                RETURN c
                """
                
                channel_params = {
                    'channel_id': metadata['channel_id'],
                    'channel_name': metadata['channel'],
                    'channel_description': self.ai_ml_channels[metadata['channel']]['description'],
                    'channel_topics': self.ai_ml_channels[metadata['channel']]['topics']
                }
                
                session.run(channel_query, channel_params)
                
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
                
                return True
                
        except Exception as e:
            print(f"❌ Error storing in Neo4j: {e}")
            return False
    
    def scrape_all_channels(self, max_videos_per_channel=30):
        """Scrape all working AI/ML channels and build knowledge graph"""
        print("🚀 YouTube AI/ML Channel Scraper - WORKING VERSION")
        print("=" * 80)
        print(f"🎯 Target channels: {len(self.ai_ml_channels)}")
        print(f"📊 Max videos per channel: {max_videos_per_channel}")
        print("=" * 80)
        
        # Create Neo4j schema
        self.create_neo4j_schema()
        
        total_videos = 0
        successful_channels = 0
        
        for channel_name, channel_info in self.ai_ml_channels.items():
            try:
                print(f"\n🔍 Processing channel: {channel_name}")
                
                # Scrape channel videos
                videos = self.scrape_channel_videos(channel_name, channel_info, max_videos_per_channel)
                
                if videos:
                    # Store videos in Neo4j
                    successful_videos = 0
                    for video in videos:
                        if self.store_video_in_neo4j(video):
                            successful_videos += 1
                            total_videos += 1
                        
                        # Small delay to be respectful to YouTube
                        time.sleep(0.1)
                    
                    print(f"✅ Channel {channel_name}: Stored {successful_videos}/{len(videos)} videos")
                    successful_channels += 1
                else:
                    print(f"⚠️ Channel {channel_name}: No videos processed")
                
                # Delay between channels
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing channel {channel_name}: {e}")
                continue
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SCRAPING SUMMARY")
        print("=" * 80)
        print(f"✅ Successful channels: {successful_channels}/{len(self.ai_ml_channels)}")
        print(f"📹 Total videos stored: {total_videos}")
        print(f"🔑 Knowledge graph nodes: Video, Channel, Keyword")
        print(f"🔗 Knowledge graph relationships: UPLOADED_BY, HAS_KEYWORD")
        
        if successful_channels > 0:
            print(f"\n💡 Next Steps:")
            print(f"   1. Check Neo4j browser to explore the knowledge graph")
            print(f"   2. Run neo4j_basic_read.py to see statistics")
            print(f"   3. Create ML concept relationships")
            print(f"   4. Build recommendation queries")
        
        return total_videos
    
    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            print("🔌 Neo4j connection closed")

def main():
    """Main function to run the working channel scraper"""
    
    try:
        # Create scraper instance
        scraper = YouTubeChannelScraperWorking()
        
        # Scrape all working channels
        total_videos = scraper.scrape_all_channels(max_videos_per_channel=30)
        
        print(f"\n🎉 Channel scraping completed! Total videos: {total_videos}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
    finally:
        # Always close the connection
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main()

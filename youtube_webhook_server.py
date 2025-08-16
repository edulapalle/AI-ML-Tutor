#!/usr/bin/env python3
"""
YouTube Webhook Server for Real-Time Video Notifications
========================================================

Uses YouTube Data API v3 Push Notifications (PubSubHubbub) to get 
real-time notifications when StatQuest uploads new videos.

This is more efficient than polling as YouTube sends notifications instantly.

Setup:
1. Register webhook endpoint with YouTube
2. Run this server to receive notifications
3. Process videos immediately when notified

Run as: python youtube_webhook_server.py
"""

import os
import hmac
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qs
import asyncio
import aiohttp
from aiohttp import web
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeWebhookServer:
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
        # YouTube PubSubHubbub settings
        self.hub_url = "https://pubsubhubbub.appspot.com/subscribe"
        self.callback_url = os.getenv("WEBHOOK_CALLBACK_URL", f"http://your-domain.com/youtube-webhook")
        self.verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "your-secret-verify-token")
        
        # StatQuest channel ID
        self.statquest_channel_id = "UCtYLUTtgS3k1Fg4y5tAhLbw"
        
    def setup_routes(self):
        """Setup webhook routes"""
        self.app.router.add_get('/youtube-webhook', self.handle_verification)
        self.app.router.add_post('/youtube-webhook', self.handle_notification)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_post('/subscribe', self.subscribe_to_channel)
        self.app.router.add_post('/unsubscribe', self.unsubscribe_from_channel)
        
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "YouTube Webhook Server"
        })
    
    async def handle_verification(self, request):
        """Handle YouTube webhook verification challenge"""
        try:
            # YouTube sends GET request with challenge parameter
            hub_challenge = request.query.get('hub.challenge')
            hub_verify_token = request.query.get('hub.verify_token')
            hub_mode = request.query.get('hub.mode')
            
            logger.info(f"🔍 Verification request: mode={hub_mode}, token={hub_verify_token}")
            
            # Verify the token matches our expected token
            if hub_verify_token == self.verify_token and hub_mode == 'subscribe':
                logger.info("✅ Webhook verification successful")
                return web.Response(text=hub_challenge)
            else:
                logger.warning("❌ Webhook verification failed")
                return web.Response(status=404)
                
        except Exception as e:
            logger.error(f"💥 Verification error: {e}")
            return web.Response(status=500)
    
    async def handle_notification(self, request):
        """Handle YouTube webhook notification for new videos"""
        try:
            # Read the XML payload
            body = await request.read()
            logger.info(f"📨 Received notification: {len(body)} bytes")
            
            # Parse XML to extract video information
            root = ET.fromstring(body.decode('utf-8'))
            
            # YouTube uses Atom feed format
            # Namespaces used in YouTube notifications
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015'
            }
            
            # Extract video ID and metadata
            entries = root.findall('.//atom:entry', namespaces)
            
            for entry in entries:
                video_id = entry.find('.//yt:videoId', namespaces)
                title = entry.find('.//atom:title', namespaces)
                published = entry.find('.//atom:published', namespaces)
                channel_id = entry.find('.//yt:channelId', namespaces)
                
                if video_id is not None and channel_id is not None:
                    video_id_text = video_id.text
                    channel_id_text = channel_id.text
                    title_text = title.text if title is not None else "Unknown"
                    published_text = published.text if published is not None else ""
                    
                    logger.info(f"🎬 New video detected:")
                    logger.info(f"   📹 Title: {title_text}")
                    logger.info(f"   🆔 Video ID: {video_id_text}")
                    logger.info(f"   📺 Channel ID: {channel_id_text}")
                    logger.info(f"   📅 Published: {published_text}")
                    
                    # Only process StatQuest videos
                    if channel_id_text == self.statquest_channel_id:
                        logger.info("✅ StatQuest video confirmed - processing...")
                        
                        # Process the video asynchronously
                        asyncio.create_task(self.process_video(video_id_text, title_text))
                    else:
                        logger.info(f"ℹ️ Ignoring video from different channel: {channel_id_text}")
            
            return web.Response(status=200)
            
        except Exception as e:
            logger.error(f"💥 Notification processing error: {e}")
            return web.Response(status=500)
    
    async def process_video(self, video_id: str, title: str):
        """Process a new video: transcript → Milvus → Neo4j"""
        try:
            logger.info(f"🚀 Starting processing pipeline for: {title}")
            
            # Import your existing processing modules
            # from your_existing_modules import process_video_pipeline
            
            # Simulate processing steps
            logger.info("📝 Step 1: Extracting transcript...")
            await asyncio.sleep(2)  # Simulate transcript extraction
            
            logger.info("🔍 Step 2: Generating embeddings and loading to Milvus...")
            await asyncio.sleep(3)  # Simulate Milvus processing
            
            logger.info("🕸️ Step 3: Creating knowledge graph relationships in Neo4j...")
            await asyncio.sleep(2)  # Simulate Neo4j processing
            
            logger.info(f"🎉 Successfully processed video: {title}")
            
            # Here you would call your actual processing functions:
            # success = await process_video_pipeline(video_id, title)
            
        except Exception as e:
            logger.error(f"💥 Video processing failed for {title}: {e}")
    
    async def subscribe_to_channel(self, request):
        """Subscribe to YouTube channel notifications"""
        try:
            topic_url = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={self.statquest_channel_id}"
            
            data = {
                'hub.callback': self.callback_url,
                'hub.topic': topic_url,
                'hub.verify': 'async',
                'hub.mode': 'subscribe',
                'hub.verify_token': self.verify_token,
                'hub.lease_seconds': '864000'  # 10 days
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.hub_url, data=data) as response:
                    if response.status == 202:
                        logger.info("✅ Successfully subscribed to StatQuest channel notifications")
                        return web.json_response({
                            "status": "subscribed",
                            "channel_id": self.statquest_channel_id,
                            "topic_url": topic_url
                        })
                    else:
                        logger.error(f"❌ Subscription failed: {response.status}")
                        return web.json_response({
                            "error": "Subscription failed",
                            "status_code": response.status
                        }, status=500)
                        
        except Exception as e:
            logger.error(f"💥 Subscription error: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def unsubscribe_from_channel(self, request):
        """Unsubscribe from YouTube channel notifications"""
        try:
            topic_url = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={self.statquest_channel_id}"
            
            data = {
                'hub.callback': self.callback_url,
                'hub.topic': topic_url,
                'hub.verify': 'async',
                'hub.mode': 'unsubscribe',
                'hub.verify_token': self.verify_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.hub_url, data=data) as response:
                    if response.status == 202:
                        logger.info("✅ Successfully unsubscribed from StatQuest channel notifications")
                        return web.json_response({"status": "unsubscribed"})
                    else:
                        logger.error(f"❌ Unsubscription failed: {response.status}")
                        return web.json_response({
                            "error": "Unsubscription failed",
                            "status_code": response.status
                        }, status=500)
                        
        except Exception as e:
            logger.error(f"💥 Unsubscription error: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def start_server(self):
        """Start the webhook server"""
        logger.info(f"🚀 Starting YouTube webhook server on port {self.port}")
        logger.info(f"📡 Callback URL: {self.callback_url}")
        logger.info(f"📺 Monitoring channel: {self.statquest_channel_id}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info("✅ Webhook server started successfully")
        logger.info("💡 To subscribe to notifications, POST to /subscribe")
        logger.info("💡 To check health, GET /health")
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
        except KeyboardInterrupt:
            logger.info("⛔ Received stop signal")
        finally:
            await runner.cleanup()

# Usage instructions
async def main():
    """Main entry point with usage instructions"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Webhook Server')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    
    args = parser.parse_args()
    
    print("""
🎬 YouTube Real-Time Webhook Server
==================================

This server receives real-time notifications when StatQuest uploads new videos.

Setup Steps:
1. Deploy this server to a public URL (e.g., using ngrok for testing)
2. Set WEBHOOK_CALLBACK_URL in .env to your public URL + /youtube-webhook
3. Set WEBHOOK_VERIFY_TOKEN in .env to a random secret string
4. Start the server: python youtube_webhook_server.py
5. Subscribe to notifications: curl -X POST http://localhost:8080/subscribe

Environment Variables Needed:
- WEBHOOK_CALLBACK_URL=https://your-domain.com/youtube-webhook
- WEBHOOK_VERIFY_TOKEN=your-secret-token

For local testing with ngrok:
1. ngrok http 8080
2. Use the ngrok URL as your WEBHOOK_CALLBACK_URL

""")
    
    server = YouTubeWebhookServer(port=args.port)
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())

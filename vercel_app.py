#!/usr/bin/env python3
"""
Vercel-Optimized AI/ML Educational Platform
==========================================

This version is optimized for Vercel deployment with YouTube monitoring
implemented as on-demand functions rather than background processes.

Key changes for Vercel:
1. No background processes (not supported)
2. YouTube monitoring via API endpoints
3. Uses Supabase for tracking processed videos
4. Serverless-friendly architecture
"""

import os
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Optional
import logging

# Import your existing app components
try:
    from app import app as existing_app
    from app import get_current_user, supabase
    from youtube_realtime_monitor import YouTubeMonitor
except ImportError:
    # Fallback for development
    existing_app = FastAPI()
    get_current_user = lambda: {"id": "test"}
    supabase = None
    YouTubeMonitor = None

# Setup logging for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create new FastAPI app that extends your existing one
app = FastAPI(
    title="AI/ML Educational Platform (Vercel)",
    description="Educational platform with serverless YouTube monitoring",
    version="1.0.0"
)

# Mount your existing app
app.mount("/", existing_app)

class VercelYouTubeMonitor:
    """Vercel-compatible YouTube monitor using Supabase for state"""
    
    def __init__(self):
        self.youtube_monitor = YouTubeMonitor()
    
    async def get_processed_videos_from_supabase(self) -> set:
        """Get processed video IDs from Supabase instead of local file"""
        try:
            # Query youtube_processed_videos table
            result = supabase.table("youtube_processed_videos").select("video_id").execute()
            
            if result.data:
                return set(item['video_id'] for item in result.data)
            return set()
            
        except Exception as e:
            logger.error(f"Error getting processed videos from Supabase: {e}")
            return set()
    
    async def mark_video_processed(self, video_id: str):
        """Mark video as processed in Supabase"""
        try:
            supabase.table("youtube_processed_videos").insert({
                "video_id": video_id,
                "processed_at": datetime.now().isoformat(),
                "status": "completed"
            }).execute()
            
        except Exception as e:
            logger.error(f"Error marking video as processed: {e}")
    
    async def check_for_new_videos(self) -> list:
        """Check for new videos (Vercel-compatible)"""
        try:
            # Get processed videos from Supabase
            processed_videos = await self.get_processed_videos_from_supabase()
            
            # Get recent videos from YouTube
            recent_videos = self.youtube_monitor.get_recent_videos(
                channel_id="UCtYLUTtgS3k1Fg4y5tAhLbw",  # StatQuest
                hours_back=24
            )
            
            # Filter out already processed videos
            new_videos = [
                video for video in recent_videos 
                if video.video_id not in processed_videos
            ]
            
            logger.info(f"Found {len(new_videos)} new videos to process")
            return new_videos
            
        except Exception as e:
            logger.error(f"Error checking for new videos: {e}")
            return []
    
    async def process_video_serverless(self, video) -> bool:
        """Process a single video (serverless-friendly)"""
        try:
            logger.info(f"Processing video: {video.title}")
            
            # Extract transcript
            transcript_success = await self.youtube_monitor.extract_transcript(video)
            if not transcript_success:
                logger.warning(f"Could not get transcript for {video.title}")
            
            # Process and load to Milvus
            milvus_success = await self.youtube_monitor.load_to_milvus(video)
            if not milvus_success:
                logger.error(f"Failed to load to Milvus: {video.title}")
                return False
            
            # Load to Neo4j
            neo4j_success = await self.youtube_monitor.load_to_neo4j(video)
            if not neo4j_success:
                logger.error(f"Failed to load to Neo4j: {video.title}")
                return False
            
            # Mark as processed in Supabase
            await self.mark_video_processed(video.video_id)
            
            logger.info(f"Successfully processed: {video.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing video {video.title}: {e}")
            return False

# Initialize Vercel monitor
vercel_monitor = VercelYouTubeMonitor()

# Vercel-specific YouTube monitoring endpoints
@app.get("/api/youtube/check")
async def check_youtube_videos(current_user=Depends(get_current_user)):
    """
    Manual endpoint to check for new YouTube videos
    Call this from a cron job or manually to trigger monitoring
    """
    try:
        new_videos = await vercel_monitor.check_for_new_videos()
        
        return JSONResponse({
            "status": "success",
            "new_videos_found": len(new_videos),
            "videos": [
                {
                    "video_id": v.video_id,
                    "title": v.title,
                    "published_at": v.published_at
                } for v in new_videos
            ],
            "message": f"Found {len(new_videos)} new videos to process"
        })
        
    except Exception as e:
        logger.error(f"Error checking YouTube videos: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

@app.post("/api/youtube/process")
async def process_youtube_videos(background_tasks: BackgroundTasks, current_user=Depends(get_current_user)):
    """
    Process new YouTube videos found
    Uses background tasks to avoid timeout
    """
    try:
        new_videos = await vercel_monitor.check_for_new_videos()
        
        if not new_videos:
            return JSONResponse({
                "status": "success",
                "message": "No new videos to process"
            })
        
        # Process videos in background tasks (Vercel-friendly)
        for video in new_videos[:3]:  # Limit to 3 videos to avoid timeout
            background_tasks.add_task(vercel_monitor.process_video_serverless, video)
        
        return JSONResponse({
            "status": "success",
            "message": f"Started processing {min(len(new_videos), 3)} videos in background",
            "videos_queued": min(len(new_videos), 3),
            "total_found": len(new_videos)
        })
        
    except Exception as e:
        logger.error(f"Error processing YouTube videos: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

@app.get("/api/youtube/status")
async def youtube_monitor_status():
    """Get YouTube monitoring status"""
    try:
        processed_videos = await vercel_monitor.get_processed_videos_from_supabase()
        
        return JSONResponse({
            "status": "active",
            "processed_videos_count": len(processed_videos),
            "last_check": datetime.now().isoformat(),
            "monitoring_method": "serverless_endpoints"
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

# Health check for Vercel
@app.get("/api/health")
async def health_check():
    """Health check endpoint for Vercel"""
    return JSONResponse({
        "status": "healthy",
        "platform": "vercel",
        "features": [
            "rag_chat",
            "youtube_monitoring_serverless",
            "milvus_integration",
            "neo4j_integration",
            "supabase_auth"
        ],
        "timestamp": datetime.now().isoformat()
    })

# For Vercel, we need to export the app
# This will be the main entry point
def handler(request):
    """Vercel handler"""
    return app(request)

if __name__ == "__main__":
    # For local testing
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

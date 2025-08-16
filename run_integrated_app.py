#!/usr/bin/env python3
"""
Integrated App with Real-Time YouTube Monitoring
==============================================

This combines your existing RAG application with real-time YouTube monitoring
in a single process. Both services run simultaneously.

Usage: python run_integrated_app.py
"""

import asyncio
import signal
import sys
from pathlib import Path

# Import your existing app
from run_app import app

# Import the real-time monitor
from youtube_realtime_monitor import RealTimePipeline

class IntegratedApplication:
    """Runs both RAG app and YouTube monitor together"""
    
    def __init__(self):
        self.youtube_monitor = RealTimePipeline(check_interval_minutes=30)
        self.running = False
        
    async def start_youtube_monitoring(self):
        """Start YouTube monitoring in background"""
        print("🔄 Starting YouTube real-time monitoring...")
        try:
            await self.youtube_monitor.start_monitoring()
        except Exception as e:
            print(f"❌ YouTube monitoring error: {e}")
    
    async def start_web_server(self):
        """Start FastAPI web server"""
        print("🌐 Starting web server...")
        import uvicorn
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False  # Disable reload for integrated mode
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    async def run(self):
        """Run both services simultaneously"""
        self.running = True
        
        print("🚀 Starting Integrated AI/ML Educational Platform")
        print("=" * 60)
        print("🎓 Features:")
        print("   • FastAPI RAG Application (http://localhost:8000)")
        print("   • Real-Time YouTube Monitoring (30 min intervals)")
        print("   • Automatic Milvus + Neo4j Updates")
        print("=" * 60)
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            print(f"\n⛔ Received signal {signum}, shutting down...")
            self.running = False
            self.youtube_monitor.stop_monitoring()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Run both services concurrently
            await asyncio.gather(
                self.start_web_server(),
                self.start_youtube_monitoring(),
                return_exceptions=True
            )
        except KeyboardInterrupt:
            print("\n👋 Shutting down integrated application...")
        except Exception as e:
            print(f"❌ Application error: {e}")
        finally:
            self.running = False

async def main():
    """Main entry point"""
    app = IntegratedApplication()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())

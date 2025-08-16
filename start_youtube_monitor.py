#!/usr/bin/env python3
"""
Easy launcher for YouTube Real-Time Monitoring
==============================================

This script helps you start the YouTube monitoring service easily.

Usage:
    python start_youtube_monitor.py            # Start monitoring (30 min intervals)
    python start_youtube_monitor.py --interval 15  # Check every 15 minutes
    python start_youtube_monitor.py --test     # Test mode (check once and exit)
"""

import sys
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='YouTube Real-Time Monitor Launcher')
    parser.add_argument('--interval', type=int, default=30, 
                       help='Check interval in minutes (default: 30)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: check once and exit')
    
    args = parser.parse_args()
    
    print("🚀 YouTube Real-Time Monitor Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("youtube_realtime_monitor.py").exists():
        print("❌ youtube_realtime_monitor.py not found")
        print("💡 Make sure you're in the project directory")
        return
    
    # Check if virtual environment is available
    venv_python = Path(".venv/bin/python")
    if not venv_python.exists():
        print("❌ Virtual environment not found at .venv/")
        print("💡 Run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt")
        return
    
    # Prepare command
    cmd = [str(venv_python), "youtube_realtime_monitor.py"]
    
    if args.test:
        cmd.append("--test")
        print("🧪 Running in test mode...")
    else:
        cmd.extend(["--interval", str(args.interval)])
        print(f"⏰ Starting monitoring with {args.interval} minute intervals...")
        print("📺 Monitoring StatQuest channel for new videos")
        print("🔄 Will automatically process: Transcript → Milvus → Neo4j")
        print("⚠️ Press Ctrl+C to stop monitoring")
    
    try:
        # Run the monitor
        result = subprocess.run(cmd, cwd=Path.cwd())
        
        if result.returncode == 0:
            if args.test:
                print("✅ Test completed successfully")
            else:
                print("✅ Monitoring stopped normally")
        else:
            print(f"❌ Monitor exited with code {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n⛔ Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error running monitor: {e}")

if __name__ == "__main__":
    main()

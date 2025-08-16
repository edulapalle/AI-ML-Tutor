#!/usr/bin/env python3
"""
Complete System Launcher
========================

Easy launcher for your AI/ML Educational Platform with optional YouTube monitoring.

Options:
1. RAG App Only (existing behavior)
2. RAG App + YouTube Monitor (separate processes) 
3. Integrated App (single process)

Usage: python start_complete_system.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_environment():
    """Check if environment is ready"""
    print("🔧 Checking environment...")
    
    # Check virtual environment
    if not Path(".venv/bin/python").exists():
        print("❌ Virtual environment not found at .venv/")
        print("💡 Run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt")
        return False
    
    # Check required files
    required_files = ["run_app.py", "youtube_realtime_monitor.py"]
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file not found: {file}")
            return False
    
    print("✅ Environment ready")
    return True

def show_menu():
    """Show startup options"""
    print("\n🚀 AI/ML Educational Platform Launcher")
    print("=" * 50)
    print("Choose your startup option:")
    print()
    print("1️⃣  RAG App Only")
    print("   • Your existing educational platform")
    print("   • FastAPI + Milvus + Neo4j + Supabase")
    print("   • No YouTube monitoring")
    print()
    print("2️⃣  RAG App + YouTube Monitor (Separate)")
    print("   • RAG app + real-time YouTube monitoring")
    print("   • Two separate processes")
    print("   • Easy to control independently")
    print("   • Recommended for production")
    print()
    print("3️⃣  Integrated App (Single Process)")
    print("   • Everything in one process")
    print("   • Simpler deployment")
    print("   • Shared resources")
    print()
    print("4️⃣  YouTube Monitor Only")
    print("   • Only run YouTube monitoring")
    print("   • For testing or maintenance")
    print()
    print("0️⃣  Exit")
    print()

def start_option_1():
    """Start RAG app only"""
    print("🎓 Starting RAG App Only...")
    print("🌐 Access at: http://localhost:8000")
    print("⚠️ Press Ctrl+C to stop")
    
    cmd = [".venv/bin/python", "run_app.py"]
    subprocess.run(cmd)

def start_option_2():
    """Start RAG app + YouTube monitor (separate processes)"""
    print("🎓 Starting RAG App + YouTube Monitor (Separate Processes)...")
    print("🌐 RAG App: http://localhost:8000")
    print("📺 YouTube Monitor: Running in background")
    print("⚠️ Press Ctrl+C to stop both")
    
    try:
        # Start RAG app in background
        print("🚀 Starting RAG application...")
        rag_process = subprocess.Popen(
            [".venv/bin/python", "run_app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for RAG app to start
        time.sleep(3)
        
        # Start YouTube monitor in foreground (shows logs)
        print("📺 Starting YouTube monitor...")
        monitor_process = subprocess.Popen(
            [".venv/bin/python", "start_youtube_monitor.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Stream monitor output
        print("📊 YouTube Monitor Output:")
        print("-" * 30)
        
        try:
            for line in monitor_process.stdout:
                print(f"📺 {line.strip()}")
        except KeyboardInterrupt:
            print("\n⛔ Stopping both services...")
        
    except KeyboardInterrupt:
        print("\n⛔ Stopping both services...")
    finally:
        # Clean up processes
        try:
            monitor_process.terminate()
            rag_process.terminate()
            print("✅ Both services stopped")
        except:
            pass

def start_option_3():
    """Start integrated app"""
    print("🔗 Starting Integrated App...")
    print("🌐 Access at: http://localhost:8000")
    print("📺 YouTube monitoring included")
    print("⚠️ Press Ctrl+C to stop")
    
    cmd = [".venv/bin/python", "run_integrated_app.py"]
    subprocess.run(cmd)

def start_option_4():
    """Start YouTube monitor only"""
    print("📺 Starting YouTube Monitor Only...")
    print("🔄 Monitoring StatQuest channel")
    print("⚠️ Press Ctrl+C to stop")
    
    cmd = [".venv/bin/python", "start_youtube_monitor.py"]
    subprocess.run(cmd)

def main():
    """Main function"""
    if not check_environment():
        return
    
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (1-4, 0 to exit): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                start_option_1()
            elif choice == "2":
                start_option_2()
            elif choice == "3":
                start_option_3()
            elif choice == "4":
                start_option_4()
            else:
                print("❌ Invalid choice. Please enter 1-4 or 0.")
                continue
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
        
        # Return to menu after each option
        print("\n" + "="*50)
        input("Press Enter to return to menu...")

if __name__ == "__main__":
    main()

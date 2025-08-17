#!/usr/bin/env python3
"""Debug pip installation issues for Railway"""

import subprocess
import sys
import os

def test_package_installation():
    """Test individual package installation"""
    
    print("🐍 Python Package Installation Debug")
    print("=" * 50)
    
    # Core packages that should always work
    core_packages = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "python-dotenv==1.0.0",
        "jinja2==3.1.2",
        "httpx==0.25.2",
        "certifi==2023.11.17"
    ]
    
    # Potentially problematic packages
    complex_packages = [
        "pymilvus==2.3.4",
        "neo4j==5.14.1", 
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "openai==1.3.6",
        "supabase==2.0.2"
    ]
    
    print("🧪 Testing core packages...")
    for package in core_packages:
        try:
            print(f"  Installing {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package], 
                capture_output=True, 
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"  ✅ {package} - SUCCESS")
            else:
                print(f"  ❌ {package} - FAILED")
                print(f"     Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"  ❌ {package} - EXCEPTION: {e}")
    
    print("\n🔬 Testing complex packages...")
    for package in complex_packages:
        try:
            print(f"  Installing {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package], 
                capture_output=True, 
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print(f"  ✅ {package} - SUCCESS")
            else:
                print(f"  ❌ {package} - FAILED")
                print(f"     Error: {result.stderr.strip()[:200]}...")
        except Exception as e:
            print(f"  ❌ {package} - EXCEPTION: {e}")
    
    print("\n🔍 System Information:")
    print(f"  Python version: {sys.version}")
    print(f"  Platform: {sys.platform}")
    print(f"  Pip version: ", end="")
    try:
        pip_result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                  capture_output=True, text=True)
        print(pip_result.stdout.strip())
    except:
        print("Unknown")

if __name__ == "__main__":
    test_package_installation()

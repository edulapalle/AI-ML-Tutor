#!/usr/bin/env python3
"""
Comprehensive Railway Debugging Tool
Diagnoses health check and CSS loading issues
"""

import os
import sys
import asyncio
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class RailwayDebugger:
    def __init__(self):
        self.base_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "http://localhost:8000")
        self.results = []
    
    def log(self, status, message, details=None):
        """Log a test result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results.append({
            "time": timestamp,
            "status": status,
            "message": message,
            "details": details
        })
        
        status_icon = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "ℹ️": "ℹ️"}.get(status, "📝")
        print(f"{status_icon} [{timestamp}] {message}")
        if details:
            print(f"    └─ {details}")
    
    async def test_health_endpoints(self):
        """Test both health check endpoints"""
        self.log("ℹ️", "Testing Health Check Endpoints")
        
        endpoints = ["/health", "/api/health", "/api/detailed-health"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.log("✅", f"{endpoint} working", f"Status: {data.get('status', 'unknown')}")
                    else:
                        self.log("❌", f"{endpoint} failed", f"HTTP {response.status_code}")
                        
                except Exception as e:
                    self.log("❌", f"{endpoint} error", str(e))
    
    async def test_css_loading(self):
        """Test CSS file loading"""
        self.log("ℹ️", "Testing CSS Loading")
        
        css_files = [
            "/static/css/dashboard.css",
            "/static/js/dashboard.js"
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for css_file in css_files:
                try:
                    url = f"{self.base_url}{css_file}"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        size = len(response.content)
                        self.log("✅", f"{css_file} accessible", f"Size: {size} bytes")
                    else:
                        self.log("❌", f"{css_file} failed", f"HTTP {response.status_code}")
                        
                except Exception as e:
                    self.log("❌", f"{css_file} error", str(e))
    
    async def test_external_resources(self):
        """Test external CDN resources"""
        self.log("ℹ️", "Testing External Resources")
        
        external_urls = [
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for url in external_urls:
                try:
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        self.log("✅", "Font Awesome CDN accessible", f"Size: {len(response.content)} bytes")
                    else:
                        self.log("❌", "Font Awesome CDN failed", f"HTTP {response.status_code}")
                        
                except Exception as e:
                    self.log("❌", "Font Awesome CDN error", str(e))
    
    async def test_main_pages(self):
        """Test main application pages"""
        self.log("ℹ️", "Testing Main Pages")
        
        pages = [
            "/",
            "/login", 
            "/register",
            "/test-css"
        ]
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for page in pages:
                try:
                    url = f"{self.base_url}{page}"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        # Check if it's HTML
                        content_type = response.headers.get("content-type", "")
                        if "text/html" in content_type:
                            self.log("✅", f"{page} accessible", f"HTML page loaded")
                        else:
                            self.log("⚠️", f"{page} wrong content type", content_type)
                    else:
                        self.log("❌", f"{page} failed", f"HTTP {response.status_code}")
                        
                except Exception as e:
                    self.log("❌", f"{page} error", str(e))
    
    async def test_debug_endpoints(self):
        """Test custom debug endpoints"""
        self.log("ℹ️", "Testing Debug Endpoints")
        
        debug_endpoints = ["/api/css-debug"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in debug_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.log("✅", f"{endpoint} working", f"Data keys: {list(data.keys())}")
                        
                        # Log specific CSS debug info
                        if "static_files" in data:
                            css_exists = data["static_files"].get("css_exists", False)
                            self.log("ℹ️", f"CSS file exists: {css_exists}")
                        
                    else:
                        self.log("❌", f"{endpoint} failed", f"HTTP {response.status_code}")
                        
                except Exception as e:
                    self.log("❌", f"{endpoint} error", str(e))
    
    def test_local_files(self):
        """Test if files exist locally"""
        self.log("ℹ️", "Testing Local File Existence")
        
        files_to_check = [
            "static/css/dashboard.css",
            "static/js/dashboard.js", 
            "templates/dashboard.html",
            "app.py",
            "requirements.txt"
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                self.log("✅", f"{file_path} exists", f"Size: {size} bytes")
            else:
                self.log("❌", f"{file_path} missing")
    
    def test_environment(self):
        """Test environment configuration"""
        self.log("ℹ️", "Testing Environment Configuration")
        
        env_vars = [
            "OPENAI_API_KEY",
            "RAILWAY_ENVIRONMENT_NAME", 
            "RAILWAY_PUBLIC_DOMAIN",
            "PORT"
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Don't log full API keys
                display_value = value[:10] + "..." if len(value) > 10 else value
                self.log("✅", f"{var} set", display_value)
            else:
                self.log("⚠️", f"{var} not set")
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("🚂 Railway Comprehensive Debugging Tool")
        print("=" * 60)
        print(f"🎯 Target URL: {self.base_url}")
        print("=" * 60)
        
        # Local tests first
        self.test_environment()
        self.test_local_files()
        
        # Remote tests (if URL is accessible)
        if self.base_url.startswith("http"):
            await self.test_health_endpoints()
            await self.test_css_loading()
            await self.test_external_resources()
            await self.test_main_pages()
            await self.test_debug_endpoints()
        else:
            self.log("⚠️", "No remote URL configured, skipping remote tests")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_count = len([r for r in self.results if r["status"] == "✅"])
        warning_count = len([r for r in self.results if r["status"] == "⚠️"])
        error_count = len([r for r in self.results if r["status"] == "❌"])
        
        print(f"✅ Successful: {success_count}")
        print(f"⚠️ Warnings: {warning_count}")
        print(f"❌ Errors: {error_count}")
        
        # Recommendations
        print("\n🎯 RECOMMENDATIONS:")
        if error_count == 0:
            print("✅ All tests passed! Railway deployment should work correctly.")
        else:
            print("❌ Issues found. Check the errors above and:")
            print("   1. Verify environment variables in Railway dashboard")
            print("   2. Check Railway build/deploy logs")
            print("   3. Test CSS loading with /test-css endpoint")
            print("   4. Use /api/css-debug for detailed CSS diagnostics")

async def main():
    """Main function"""
    debugger = RailwayDebugger()
    await debugger.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())

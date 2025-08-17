#!/usr/bin/env python3
"""
Test script to verify health check doesn't redirect
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import uvicorn
import os

# Create test app
app = FastAPI()

# Simulate Railway environment
os.environ["RAILWAY_ENVIRONMENT_NAME"] = "production"

# Add custom HTTPS redirect middleware (same as in main app)
@app.middleware("http")
async def custom_https_redirect(request: Request, call_next):
    print(f"🔍 Request: {request.method} {request.url.path} (scheme: {request.url.scheme})")
    
    # Skip HTTPS redirect for health checks
    if request.url.path in ["/health", "/api/health"]:
        print("✅ Health check detected - skipping redirect")
        response = await call_next(request)
        print(f"✅ Health check response: {response.status_code}")
        return response
    
    # For other paths, enforce HTTPS in production
    if request.url.scheme == "http":
        print("🔄 Non-health path - redirecting to HTTPS")
        https_url = request.url.replace(scheme="https")
        return RedirectResponse(https_url, status_code=301)
    
    return await call_next(request)

@app.get("/health")
async def health():
    """Test health endpoint"""
    return {"status": "healthy", "test": "no_redirect"}

@app.get("/api/health") 
async def api_health():
    """Test API health endpoint"""
    return {"status": "healthy", "test": "no_redirect", "endpoint": "api"}

@app.get("/test")
async def test():
    """Test regular endpoint (should redirect)"""
    return {"status": "test", "redirect": "should_happen"}

if __name__ == "__main__":
    print("🧪 Testing Health Check Redirect Behavior")
    print("=" * 50)
    print("📝 Test URLs:")
    print("   - http://localhost:8001/health (should NOT redirect)")
    print("   - http://localhost:8001/api/health (should NOT redirect)")
    print("   - http://localhost:8001/test (SHOULD redirect)")
    print("=" * 50)
    
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")

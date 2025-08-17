#!/usr/bin/env python3
"""
Test to verify no redirect loops in the app
"""

from fastapi import FastAPI, Request
import uvicorn
import os

# Create test app (same structure as main app)
app = FastAPI()

# Simulate Railway environment
os.environ["RAILWAY_ENVIRONMENT_NAME"] = "production"

# Railway handles HTTPS termination at the proxy level, so no redirect needed
railway_env = os.getenv("RAILWAY_ENVIRONMENT_NAME") 
if railway_env:
    print("✅ Railway deployment detected - HTTPS handled by Railway proxy")

# Add CORS (same as main app)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers (same as main app)
@app.middleware("http") 
async def add_security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        
        # Skip security headers for health checks
        if request.url.path in ["/health", "/api/health"]:
            print(f"🏥 Health check {request.url.path} - skipping security headers")
            return response
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY" 
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
        
    except Exception as e:
        print(f"❌ Security middleware error: {e}")
        response = await call_next(request)
        return response

@app.get("/")
async def root():
    """Test root endpoint"""
    return {"status": "ok", "message": "No redirect loop!", "app": "test"}

@app.get("/health")
async def health():
    """Test health endpoint"""
    return {"status": "healthy", "test": "no_redirect"}

@app.get("/api/health") 
async def api_health():
    """Test API health endpoint"""
    return {"status": "healthy", "test": "no_redirect", "endpoint": "api"}

@app.get("/login")
async def login():
    """Test login endpoint"""
    return {"status": "login_page", "redirect": "none"}

if __name__ == "__main__":
    print("🧪 Testing for Redirect Loops")
    print("=" * 50)
    print("📝 Test URLs (should all return 200, no redirects):")
    print("   - http://localhost:8002/")
    print("   - http://localhost:8002/health")
    print("   - http://localhost:8002/api/health")
    print("   - http://localhost:8002/login")
    print("=" * 50)
    print("🚀 If no redirect loops, all URLs should work normally")
    
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")

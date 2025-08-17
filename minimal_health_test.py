#!/usr/bin/env python3
"""
Minimal health check test server
Use this to test if Railway can reach the health endpoint
"""

from fastapi import FastAPI
from datetime import datetime
import os
import uvicorn

app = FastAPI(title="Health Check Test")

@app.get("/")
@app.get("/health")
@app.get("/api/health")
async def health():
    """Ultra-simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Health check working!",
        "port": os.getenv("PORT", "8000")
    }

@app.get("/test")
async def test():
    """Test endpoint"""
    return {"test": "working", "env_vars": len([k for k in os.environ.keys() if not k.startswith("_")])}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting minimal health test server on port {port}")
    print(f"🔗 Health check available at: http://localhost:{port}/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )

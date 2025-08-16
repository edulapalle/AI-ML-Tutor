#!/usr/bin/env python3
"""
Vercel-Compatible API Entry Point for AI/ML Educational Platform
================================================================

This file serves as the main entry point for Vercel deployment.
It imports and exposes the FastAPI app from the root directory.
"""

import sys
import os

# Add the parent directory to Python path so we can import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import the main FastAPI app
    from app import app
    
    # For Vercel, we need to expose the app directly
    # Vercel will automatically handle ASGI/WSGI compatibility
    
except ImportError as e:
    # Fallback for development or if imports fail
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return JSONResponse({
            "error": "Import failed",
            "message": str(e),
            "suggestion": "Check that all dependencies are installed"
        })

# This is what Vercel will use as the handler
def handler(request):
    """Vercel serverless function handler"""
    return app

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

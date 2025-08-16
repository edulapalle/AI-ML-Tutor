#!/usr/bin/env python3
"""
FastAPI Middleware for Abuse Protection
Integrates abuse protection into the FastAPI application
"""

import json
import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from abuse_protection import validate_request_content

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbuseProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware to apply abuse protection to relevant endpoints"""
    
    def __init__(self, app, protected_paths: Optional[list] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or [
            "/api/chat",
            "/api/query", 
            "/query"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request through abuse protection if needed"""
        
        # Only protect specified paths
        if not any(request.url.path.startswith(path) for path in self.protected_paths):
            return await call_next(request)
        
        # Only protect POST requests (where content is submitted)
        if request.method != "POST":
            return await call_next(request)
        
        try:
            # Extract content from request body
            body = await request.body()
            
            # Parse JSON body
            try:
                body_json = json.loads(body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Invalid JSON - let the application handle it
                return await call_next(request)
            
            # Extract content to validate
            content = None
            user_id = None
            
            if "message" in body_json:
                content = body_json["message"]
            elif "question" in body_json:
                content = body_json["question"]
            
            # Extract user ID if available (from token, headers, etc.)
            # This would be extracted from your authentication system
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # You could decode the JWT token here to get user_id
                # For now, we'll use a simple approach
                user_id = f"user_{hash(auth_header) % 10000}"
            
            if content:
                # Validate the content
                validation_result = await validate_request_content(request, content, user_id)
                
                if not validation_result["is_valid"]:
                    # Log the blocked request
                    logger.warning(
                        f"Request blocked: {validation_result['error_type']} - "
                        f"IP: {request.client.host if request.client else 'unknown'} - "
                        f"Content: {content[:100]}..."
                    )
                    
                    # Return appropriate error response
                    error_response = {
                        "error": validation_result["error_message"],
                        "type": validation_result["error_type"],
                        "status_code": validation_result["status_code"]
                    }
                    
                    # Add retry-after header for rate limiting
                    headers = {}
                    if "retry_after" in validation_result:
                        headers["Retry-After"] = str(int(validation_result["retry_after"]))
                    
                    return JSONResponse(
                        status_code=validation_result["status_code"],
                        content=error_response,
                        headers=headers
                    )
                else:
                    # Log successful validation for monitoring
                    logger.info(
                        f"Request validated: ML confidence {validation_result.get('ml_confidence', 'N/A')} - "
                        f"Method: {validation_result.get('validation_method', 'N/A')}"
                    )
            
            # Reconstruct request with original body for downstream processing
            async def receive():
                return {"type": "http.request", "body": body}
            
            request._receive = receive
            
        except Exception as e:
            # Log error but don't block request - fail open for availability
            logger.error(f"Abuse protection middleware error: {e}")
        
        # Continue to the actual endpoint
        return await call_next(request)

def create_protection_dependency():
    """
    Create a FastAPI dependency for endpoint-level protection
    Use this for specific endpoints that need protection
    """
    async def protection_dependency(request: Request, content: str, user_id: Optional[str] = None):
        """Dependency function for endpoint-level protection"""
        validation_result = await validate_request_content(request, content, user_id)
        
        if not validation_result["is_valid"]:
            # Determine the appropriate HTTP exception
            status_code = validation_result["status_code"]
            error_message = validation_result["error_message"]
            
            if status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail=error_message,
                    headers={"Retry-After": str(int(validation_result.get("retry_after", 60)))}
                )
            elif status_code == 403:
                raise HTTPException(status_code=403, detail=error_message)
            else:
                raise HTTPException(status_code=400, detail=error_message)
        
        return validation_result
    
    return protection_dependency

# Pre-created dependency instance
protection_check = create_protection_dependency()

async def validate_chat_message(request: Request, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Specific validation function for chat messages
    Use this in your chat endpoints
    """
    return await validate_request_content(request, message, user_id)

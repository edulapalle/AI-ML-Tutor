#!/usr/bin/env python3
"""
Comprehensive Abuse Protection System
Implements rate limiting, content filtering, and security measures
"""

import time
import re
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncio
from fastapi import HTTPException, Request
import openai
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class RateLimitBucket:
    """Rate limiting bucket for tracking requests"""
    requests: deque = field(default_factory=deque)
    max_requests: int = 10
    window_seconds: int = 60
    
    def is_allowed(self) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        
        # Remove old requests outside the window
        while self.requests and self.requests[0] <= now - self.window_seconds:
            self.requests.popleft()
        
        # Check if we're under the limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def time_until_allowed(self) -> float:
        """Get seconds until next request is allowed"""
        if not self.requests:
            return 0.0
        
        oldest_request = self.requests[0]
        return max(0.0, self.window_seconds - (time.time() - oldest_request))

class RateLimiter:
    """Rate limiting system with per-IP and per-user tracking"""
    
    def __init__(self):
        self.ip_buckets: Dict[str, RateLimitBucket] = defaultdict(RateLimitBucket)
        self.user_buckets: Dict[str, RateLimitBucket] = defaultdict(RateLimitBucket)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def cleanup_old_buckets(self):
        """Remove inactive buckets to prevent memory leaks"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Clean IP buckets
        to_remove = []
        for ip, bucket in self.ip_buckets.items():
            if not bucket.requests or bucket.requests[-1] < now - 3600:  # 1 hour
                to_remove.append(ip)
        
        for ip in to_remove:
            del self.ip_buckets[ip]
        
        # Clean user buckets
        to_remove = []
        for user_id, bucket in self.user_buckets.items():
            if not bucket.requests or bucket.requests[-1] < now - 3600:  # 1 hour
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.user_buckets[user_id]
        
        self.last_cleanup = now
    
    def check_rate_limit(self, request: Request, user_id: Optional[str] = None) -> Tuple[bool, float]:
        """
        Check if request is within rate limits
        Returns (is_allowed, retry_after_seconds)
        """
        self.cleanup_old_buckets()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check IP-based rate limit
        ip_bucket = self.ip_buckets[client_ip]
        ip_allowed = ip_bucket.is_allowed()
        
        # Check user-based rate limit if user is authenticated
        user_allowed = True
        user_retry_after = 0.0
        
        if user_id:
            user_bucket = self.user_buckets[user_id]
            user_allowed = user_bucket.is_allowed()
            user_retry_after = user_bucket.time_until_allowed()
        
        # Use the most restrictive limit
        is_allowed = ip_allowed and user_allowed
        retry_after = max(ip_bucket.time_until_allowed(), user_retry_after)
        
        return is_allowed, retry_after

class ContentValidator:
    """Content validation and filtering system"""
    
    def __init__(self):
        # Content length limits
        self.max_content_length = 1000
        self.min_content_length = 1
        
        # Profanity patterns (basic set - expand as needed)
        self.profanity_patterns = [
            r'\bf[u*]+ck\w*\b',
            r'\bs[h*]+[i!1]t\w*\b', 
            r'\bb[i!1]tch\w*\b',
            r'\ba[s*]+h[o0]le\w*\b',
            r'\bd[a@]mn\w*\b',
            r'\bcr[a@]p\w*\b',
            r'\bh[e3]ll\w*\b'
        ]
        
        # Prompt injection patterns
        self.injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'ignore\s+all\s+previous',
            r'system\s*:\s*you\s+are\s+now',
            r'forget\s+everything',
            r'new\s+instructions\s*:',
            r'override\s+safety',
            r'disable\s+guardrails',
            r'reveal\s+your\s+prompt',
            r'system_override\s*=\s*true',
            r'---\s*injection\s*---',
            r'```\s*system',
            r'<\s*system\s*>',
            r'jailbreak\s+mode',
            r'developer\s+mode\s+enabled'
        ]
        
        # Compile regex patterns for efficiency
        self.profanity_regex = re.compile('|'.join(self.profanity_patterns), re.IGNORECASE)
        self.injection_regex = re.compile('|'.join(self.injection_patterns), re.IGNORECASE)
    
    def validate_content_length(self, content: str) -> Tuple[bool, str]:
        """Validate content length"""
        if len(content) > self.max_content_length:
            return False, f"Content too long ({len(content)} chars). Maximum {self.max_content_length} characters allowed."
        
        if len(content) < self.min_content_length:
            return False, "Content cannot be empty."
        
        return True, ""
    
    def check_profanity(self, content: str) -> Tuple[bool, List[str]]:
        """Check for profanity in content"""
        matches = self.profanity_regex.findall(content.lower())
        has_profanity = len(matches) > 0
        return has_profanity, matches
    
    def check_injection_attempt(self, content: str) -> Tuple[bool, List[str]]:
        """Check for prompt injection attempts"""
        matches = self.injection_regex.findall(content.lower())
        has_injection = len(matches) > 0
        return has_injection, matches
    
    def validate_content(self, content: str) -> Dict:
        """
        Comprehensive content validation
        Returns validation result with details
        """
        result = {
            "is_valid": True,
            "status_code": 200,
            "error_type": None,
            "error_message": "",
            "issues": []
        }
        
        # Check content length
        length_valid, length_error = self.validate_content_length(content)
        if not length_valid:
            result["is_valid"] = False
            result["status_code"] = 400
            result["error_type"] = "content_too_long"
            result["error_message"] = length_error
            result["issues"].append("length")
            return result  # Return early for length issues
        
        # Check for profanity
        has_profanity, profanity_matches = self.check_profanity(content)
        if has_profanity:
            result["is_valid"] = False
            result["status_code"] = 403
            result["error_type"] = "inappropriate_content"
            result["error_message"] = "Content contains inappropriate language and has been blocked."
            result["issues"].append("profanity")
            result["profanity_matches"] = profanity_matches
            return result  # Return early for profanity
        
        # Check for injection attempts
        has_injection, injection_matches = self.check_injection_attempt(content)
        if has_injection:
            result["is_valid"] = False
            result["status_code"] = 400
            result["error_type"] = "injection_attempt"
            result["error_message"] = "Potential security violation detected. Please rephrase your request."
            result["issues"].append("injection")
            result["injection_matches"] = injection_matches
            return result
        
        return result

class MLTopicValidator:
    """Enhanced ML/AI topic validation"""
    
    def __init__(self):
        # ML/AI related keywords (expanded list)
        self.ml_keywords = {
            'machine learning', 'ml', 'ai', 'artificial intelligence',
            'deep learning', 'neural network', 'cnn', 'rnn', 'lstm', 'gru',
            'supervised learning', 'unsupervised learning', 'reinforcement learning',
            'classification', 'regression', 'clustering', 'dimensionality reduction',
            'feature engineering', 'data preprocessing', 'cross validation',
            'overfitting', 'underfitting', 'bias', 'variance', 'regularization',
            'gradient descent', 'backpropagation', 'optimization',
            'decision tree', 'random forest', 'svm', 'support vector machine',
            'naive bayes', 'k-means', 'pca', 'linear regression', 'logistic regression',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'computer vision', 'nlp', 'natural language processing',
            'transformers', 'bert', 'gpt', 'attention mechanism',
            'convolutional', 'recurrent', 'autoencoder', 'gan', 'generative',
            'model evaluation', 'accuracy', 'precision', 'recall', 'f1-score',
            'confusion matrix', 'roc curve', 'auc', 'loss function',
            'hyperparameter', 'tuning', 'grid search', 'random search',
            'ensemble', 'bagging', 'boosting', 'xgboost', 'adaboost',
            'data science', 'statistics', 'probability', 'algorithm'
        }
        
        # Clearly non-ML topics
        self.non_ml_topics = {
            'cooking', 'recipe', 'food', 'restaurant', 'kitchen',
            'weather', 'temperature', 'rain', 'snow', 'climate',
            'sports', 'football', 'basketball', 'soccer', 'tennis',
            'politics', 'election', 'government', 'politician',
            'entertainment', 'movie', 'music', 'celebrity', 'actor',
            'travel', 'vacation', 'hotel', 'flight', 'destination',
            'shopping', 'clothes', 'fashion', 'brand', 'sale',
            'health', 'medicine', 'doctor', 'hospital', 'disease',
            'car', 'automotive', 'driving', 'mechanic', 'repair',
            'finance', 'stock', 'investment', 'bank', 'money'
        }
        
        # Initialize OpenAI client for AI-based validation
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def keyword_based_validation(self, content: str) -> Tuple[bool, float]:
        """Fast keyword-based ML topic validation"""
        content_lower = content.lower()
        
        # Count ML-related keywords
        ml_score = sum(1 for keyword in self.ml_keywords if keyword in content_lower)
        
        # Count non-ML keywords
        non_ml_score = sum(1 for keyword in self.non_ml_topics if keyword in content_lower)
        
        # Calculate confidence score
        total_keywords = ml_score + non_ml_score
        if total_keywords == 0:
            return True, 0.5  # Neutral - let AI decide
        
        ml_confidence = ml_score / total_keywords
        
        # Strong indicators
        if ml_confidence >= 0.7:
            return True, ml_confidence
        elif ml_confidence <= 0.3:
            return False, 1 - ml_confidence
        else:
            return True, 0.5  # Uncertain - let it through with low confidence
    
    async def ai_based_validation(self, content: str) -> Tuple[bool, float]:
        """AI-based ML topic validation using OpenAI"""
        if not self.openai_client:
            return True, 0.5  # Fallback if no OpenAI key
        
        try:
            prompt = f"""
            Determine if the following question is related to Machine Learning, Artificial Intelligence, Data Science, or Computer Science concepts.

            Question: "{content}"

            Respond with only "YES" if it's ML/AI/Data Science related, or "NO" if it's clearly about other topics (cooking, weather, sports, entertainment, etc.).

            If unsure, respond with "YES" to be inclusive of learning questions.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a topic classifier. Respond only with YES or NO."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0
            )
            
            answer = response.choices[0].message.content.strip().upper()
            is_ml_related = answer == "YES"
            confidence = 0.9 if answer in ["YES", "NO"] else 0.5
            
            return is_ml_related, confidence
            
        except Exception as e:
            print(f"AI validation error: {e}")
            return True, 0.5  # Fallback to allowing the request
    
    async def validate_ml_topic(self, content: str) -> Dict:
        """
        Comprehensive ML topic validation
        Returns validation result with confidence score
        """
        # First try fast keyword-based validation
        keyword_valid, keyword_confidence = self.keyword_based_validation(content)
        
        # If keyword validation is confident, use it
        if keyword_confidence >= 0.7:
            if keyword_valid:
                return {
                    "is_valid": True,
                    "confidence": keyword_confidence,
                    "method": "keyword",
                    "error_message": ""
                }
            else:
                return {
                    "is_valid": False,
                    "confidence": keyword_confidence,
                    "method": "keyword",
                    "error_message": "Question appears to be outside the scope of ML/AI topics. Please ask about machine learning, AI, data science, or related technical topics."
                }
        
        # If keyword validation is uncertain, use AI validation
        ai_valid, ai_confidence = await self.ai_based_validation(content)
        
        if ai_valid:
            return {
                "is_valid": True,
                "confidence": ai_confidence,
                "method": "ai",
                "error_message": ""
            }
        else:
            return {
                "is_valid": False,
                "confidence": ai_confidence,
                "method": "ai", 
                "error_message": "I'm here to help with AI and machine learning topics. Please ask about ML, AI, data science, or related technical topics."
            }

class AbuseProtectionSystem:
    """Main abuse protection system coordinating all components"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.content_validator = ContentValidator()
        self.ml_topic_validator = MLTopicValidator()
        
        # Cache for repeated validations
        self.validation_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_cleanup = time.time()
    
    def _get_cache_key(self, content: str) -> str:
        """Generate cache key for content"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _cleanup_cache(self):
        """Remove expired cache entries"""
        now = time.time()
        if now - self.last_cache_cleanup < 60:  # Cleanup every minute
            return
        
        expired_keys = []
        for key, entry in self.validation_cache.items():
            if now - entry.get('timestamp', 0) > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.validation_cache[key]
        
        self.last_cache_cleanup = now
    
    async def validate_request(self, request: Request, content: str, user_id: Optional[str] = None) -> Dict:
        """
        Comprehensive request validation
        Returns validation result with appropriate HTTP status codes
        """
        self._cleanup_cache()
        
        # Check cache first
        cache_key = self._get_cache_key(content)
        if cache_key in self.validation_cache:
            cached_result = self.validation_cache[cache_key].copy()
            cached_result.pop('timestamp', None)  # Remove timestamp from result
            
            # Still check rate limiting (not cached)
            rate_allowed, retry_after = self.rate_limiter.check_rate_limit(request, user_id)
            if not rate_allowed:
                return {
                    "is_valid": False,
                    "status_code": 429,
                    "error_type": "rate_limit_exceeded",
                    "error_message": f"Rate limit exceeded. Please wait {retry_after:.1f} seconds before trying again.",
                    "retry_after": retry_after
                }
            
            return cached_result
        
        # 1. Check rate limiting first
        rate_allowed, retry_after = self.rate_limiter.check_rate_limit(request, user_id)
        if not rate_allowed:
            return {
                "is_valid": False,
                "status_code": 429,
                "error_type": "rate_limit_exceeded",
                "error_message": f"Rate limit exceeded. Please wait {retry_after:.1f} seconds before trying again.",
                "retry_after": retry_after
            }
        
        # 2. Validate content (length, profanity, injection)
        content_result = self.content_validator.validate_content(content)
        if not content_result["is_valid"]:
            # Cache negative results
            self.validation_cache[cache_key] = {**content_result, "timestamp": time.time()}
            return content_result
        
        # 3. Validate ML topic relevance
        ml_result = await self.ml_topic_validator.validate_ml_topic(content)
        if not ml_result["is_valid"]:
            result = {
                "is_valid": False,
                "status_code": 400,
                "error_type": "non_ml_topic",
                "error_message": ml_result["error_message"],
                "confidence": ml_result["confidence"],
                "validation_method": ml_result["method"]
            }
            # Cache negative results
            self.validation_cache[cache_key] = {**result, "timestamp": time.time()}
            return result
        
        # All validations passed
        result = {
            "is_valid": True,
            "status_code": 200,
            "error_type": None,
            "error_message": "",
            "ml_confidence": ml_result["confidence"],
            "validation_method": ml_result["method"]
        }
        
        # Cache positive results
        self.validation_cache[cache_key] = {**result, "timestamp": time.time()}
        return result

# Global instance
abuse_protection = AbuseProtectionSystem()

async def validate_request_content(request: Request, content: str, user_id: Optional[str] = None) -> Dict:
    """
    Main entry point for request validation
    Use this function in your FastAPI endpoints
    """
    return await abuse_protection.validate_request(request, content, user_id)

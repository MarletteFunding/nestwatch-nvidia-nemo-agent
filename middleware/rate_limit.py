"""
Rate Limiting Middleware
Implements token bucket rate limiting for LLM endpoints
"""
import logging
import time
import threading
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import os

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: float, burst: int):
        """
        Initialize token bucket
        
        Args:
            rate: Tokens per second
            burst: Maximum burst capacity
        """
        self.rate = rate
        self.capacity = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if bucket is empty
        """
        with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                return False
    
    def get_retry_after(self) -> float:
        """Get seconds until next token is available"""
        with self.lock:
            if self.tokens >= 1:
                return 0.0
            
            # Calculate time needed for one token
            return (1.0 - self.tokens) / self.rate

class RateLimiter:
    """Rate limiter for LLM endpoints"""
    
    def __init__(self):
        # Configuration
        self.llm_rps = float(os.getenv("LLM_RPS", "0.5"))  # 0.5 requests per second
        self.llm_burst = int(os.getenv("LLM_BURST", "2"))  # Burst capacity of 2
        
        # Create token bucket
        self.bucket = TokenBucket(self.llm_rps, self.llm_burst)
        
        # Track requests per IP (optional)
        self.ip_buckets: Dict[str, TokenBucket] = {}
        self.ip_cleanup_time = 0
        
        logger.info(f"Rate limiter initialized: {self.llm_rps} RPS, burst={self.llm_burst}")
    
    def _cleanup_ip_buckets(self):
        """Clean up old IP buckets"""
        current_time = time.time()
        if current_time - self.ip_cleanup_time < 300:  # Cleanup every 5 minutes
            return
        
        self.ip_cleanup_time = current_time
        expired_ips = []
        
        for ip, bucket in self.ip_buckets.items():
            # Remove buckets that haven't been used in 10 minutes
            if current_time - bucket.last_update > 600:
                expired_ips.append(ip)
        
        for ip in expired_ips:
            del self.ip_buckets[ip]
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def check_rate_limit(self, request: Request) -> Optional[Response]:
        """
        Check if request should be rate limited
        
        Args:
            request: FastAPI request object
            
        Returns:
            Response object if rate limited, None if allowed
        """
        # Clean up old IP buckets
        self._cleanup_ip_buckets()
        
        # Check global rate limit
        if not self.bucket.consume():
            retry_after = self.bucket.get_retry_after()
            logger.warning(f"Global rate limit exceeded, retry after {retry_after:.1f}s")
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests to LLM endpoints",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(int(retry_after) + 1)}
            )
        
        # Check per-IP rate limit (optional, more restrictive)
        client_ip = self._get_client_ip(request)
        if client_ip != "unknown":
            if client_ip not in self.ip_buckets:
                # Create IP-specific bucket (more restrictive)
                self.ip_buckets[client_ip] = TokenBucket(
                    self.llm_rps * 0.5,  # Half the global rate
                    max(1, self.llm_burst // 2)  # Half the burst
                )
            
            ip_bucket = self.ip_buckets[client_ip]
            if not ip_bucket.consume():
                retry_after = ip_bucket.get_retry_after()
                logger.warning(f"IP rate limit exceeded for {client_ip}, retry after {retry_after:.1f}s")
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests from IP {client_ip}",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(int(retry_after) + 1)}
                )
        
        return None  # Request allowed
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        return {
            "global_tokens": self.bucket.tokens,
            "global_capacity": self.bucket.capacity,
            "global_rate": self.bucket.rate,
            "active_ip_buckets": len(self.ip_buckets),
            "retry_after": self.bucket.get_retry_after()
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    # Only apply rate limiting to LLM endpoints
    if request.url.path.startswith("/api/v1/sre/enhanced-summary"):
        rate_limit_response = rate_limiter.check_rate_limit(request)
        if rate_limit_response:
            return rate_limit_response
    
    response = call_next(request)
    return response

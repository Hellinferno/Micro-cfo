#!/usr/bin/env python3
"""
Rate Limiting Middleware for MicroCFO Integration Server
Prevents abuse by limiting request rates per user/IP

Requirements: 5.4
"""

import logging
import time
from typing import Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration for different endpoint types"""
    
    # Default limits (requests per minute)
    DEFAULT_LIMIT = 60
    
    # Endpoint-specific limits
    LIMITS = {
        # Authentication endpoints - stricter limits
        "/api/v1/auth/login": 5,
        "/api/v1/auth/register": 3,
        
        # Agent endpoints - moderate limits
        "/api/v1/agents/visual-auditor": 20,
        "/api/v1/agents/legal-sentinel": 30,
        "/api/v1/agents/subsidy-hunter": 30,
        "/api/v1/agents/negotiator": 20,
        
        # WebSocket - higher limit for real-time
        "/ws": 100,
        
        # Health check - no limit
        "/health": 1000,
    }
    
    # Time window in seconds
    WINDOW_SIZE = 60  # 1 minute
    
    @classmethod
    def get_limit(cls, path: str) -> int:
        """
        Get rate limit for a specific path
        
        Args:
            path: Request path
            
        Returns:
            Rate limit (requests per minute)
        """
        # Check for exact match
        if path in cls.LIMITS:
            return cls.LIMITS[path]
        
        # Check for prefix match
        for limit_path, limit in cls.LIMITS.items():
            if path.startswith(limit_path):
                return limit
        
        # Return default limit
        return cls.DEFAULT_LIMIT


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm
    
    Requirements: 5.4
    """
    
    def __init__(self):
        # Store request timestamps: {client_id: {endpoint: [timestamps]}}
        self.requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # Cleanup every 5 minutes
    
    def _cleanup_old_requests(self):
        """Remove old request timestamps to prevent memory bloat"""
        current_time = time.time()
        
        # Only cleanup periodically
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - RateLimitConfig.WINDOW_SIZE
        
        # Clean up old timestamps
        for client_id in list(self.requests.keys()):
            for endpoint in list(self.requests[client_id].keys()):
                # Remove timestamps older than window
                self.requests[client_id][endpoint] = [
                    ts for ts in self.requests[client_id][endpoint]
                    if ts > cutoff_time
                ]
                
                # Remove empty endpoint entries
                if not self.requests[client_id][endpoint]:
                    del self.requests[client_id][endpoint]
            
            # Remove empty client entries
            if not self.requests[client_id]:
                del self.requests[client_id]
        
        self.last_cleanup = current_time
        logger.debug(f"Rate limiter cleanup completed - {len(self.requests)} active clients")
    
    def is_allowed(self, client_id: str, endpoint: str, limit: int) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit
        
        Args:
            client_id: Client identifier (user ID or IP)
            endpoint: Request endpoint
            limit: Rate limit for this endpoint
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time)
        """
        current_time = time.time()
        cutoff_time = current_time - RateLimitConfig.WINDOW_SIZE
        
        # Get request timestamps for this client and endpoint
        timestamps = self.requests[client_id][endpoint]
        
        # Remove old timestamps (sliding window)
        timestamps = [ts for ts in timestamps if ts > cutoff_time]
        self.requests[client_id][endpoint] = timestamps
        
        # Check if limit exceeded
        request_count = len(timestamps)
        remaining = max(0, limit - request_count)
        
        if request_count >= limit:
            # Calculate reset time (when oldest request expires)
            reset_time = int(timestamps[0] + RateLimitConfig.WINDOW_SIZE) if timestamps else int(current_time)
            return False, 0, reset_time
        
        # Add current request timestamp
        timestamps.append(current_time)
        
        # Calculate reset time
        reset_time = int(current_time + RateLimitConfig.WINDOW_SIZE)
        
        # Periodic cleanup
        self._cleanup_old_requests()
        
        return True, remaining - 1, reset_time
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        return {
            "active_clients": len(self.requests),
            "total_tracked_endpoints": sum(len(endpoints) for endpoints in self.requests.values()),
            "last_cleanup": datetime.fromtimestamp(self.last_cleanup).isoformat()
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests
    
    Requirements: 5.4
    """
    
    def __init__(self, app: ASGIApp, enabled: bool = True):
        super().__init__(app)
        self.logger = logging.getLogger("rate_limit")
        self.enabled = enabled
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier for rate limiting
        
        Prefers user ID if authenticated, falls back to IP address
        
        Args:
            request: Incoming request
            
        Returns:
            Client identifier string
        """
        # Try to get user ID from authenticated context
        user_context = getattr(request.state, "user", None)
        if user_context and hasattr(user_context, "user_id"):
            return f"user:{user_context.user_id}"
        
        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"
        
        # Last resort - use a generic identifier
        return "unknown"
    
    async def dispatch(self, request: Request, call_next):
        """
        Check rate limit before processing request
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response or rate limit error
        """
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get rate limit for this endpoint
        limit = RateLimitConfig.get_limit(request.url.path)
        
        # Check rate limit
        is_allowed, remaining, reset_time = rate_limiter.is_allowed(
            client_id, request.url.path, limit
        )
        
        # Skip enforcement if disabled (for testing), but still add headers
        if not self.enabled:
            response = await call_next(request)
            # Always add rate limit headers for client awareness
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            return response
        
        if not is_allowed:
            # Log rate limit violation
            self.logger.warning(
                f"Rate limit exceeded: {client_id} - {request.url.path}",
                extra={
                    "client_id": client_id,
                    "path": request.url.path,
                    "limit": limit,
                    "reset_time": reset_time
                }
            )
            
            # Log security event
            from middleware.logging_middleware import log_security_event
            log_security_event(
                event_type="rate_limit_exceeded",
                user_id=client_id,
                details={
                    "path": request.url.path,
                    "limit": limit,
                    "reset_time": reset_time
                },
                severity="warning"
            )
            
            # Return rate limit error
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "details": {
                        "limit": limit,
                        "window": f"{RateLimitConfig.WINDOW_SIZE}s",
                        "reset_time": reset_time
                    },
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(time.time()))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


def get_rate_limiter_stats() -> dict:
    """
    Get rate limiter statistics
    
    Returns:
        Dictionary with rate limiter stats
    """
    return rate_limiter.get_stats()

import os
import json
import hashlib
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

# Initialize Redis client
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure idempotency for POST/PUT/PATCH requests.
    Requires 'Idempotency-Key' header.
    """
    def __init__(self, app, expiry: int = 86400): # Default 24h
        super().__init__(app)
        self.expiry = expiry

    async def dispatch(self, request: Request, call_next):
        # Only check idempotency for state-changing methods
        if request.method not in ["POST", "PUT", "PATCH"]:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # Create a unique cache key based on user (if constrained) or global
        # basic implementation: idempotency:{key}
        cache_key = f"idempotency:{idempotency_key}"

        # 1. Check if key exists
        cached_response = await redis_client.get(cache_key)
        if cached_response:
            logger.info(f"Idempotency hit for key: {idempotency_key}")
            try:
                data = json.loads(cached_response)
                return JSONResponse(
                    content=data["body"],
                    status_code=data["status_code"],
                    headers=data.get("headers", {})
                )
            except Exception as e:
                logger.error(f"Failed to load cached idempotency data: {e}")
                # Fallthrough to process if cache is corrupted

        # 2. Process request
        response = await call_next(request)

        # 3. Cache successful responses
        if 200 <= response.status_code < 300:
            # We need to capture the response body. 
            # StreamingResponse is complex to cache, assuming JSON for this API.
            
            # Check content type
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                # Consume body
                response_body = [section async for section in response.body_iterator]
                response.body_iterator = iter(response_body)
                body_text = b"".join(response_body).decode()
                
                try:
                    body_json = json.loads(body_text)
                    
                    cache_data = {
                        "status_code": response.status_code,
                        "body": body_json,
                        "headers": dict(response.headers)
                    }
                    
                    # Store in Redis
                    await redis_client.set(cache_key, json.dumps(cache_data), ex=self.expiry)
                    logger.info(f"Idempotency key stored: {idempotency_key}")
                    
                except json.JSONDecodeError:
                    pass

        return response

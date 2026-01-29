"""
Authentication middleware for MicroCFO Integration Server
Handles JWT token validation and user context injection
"""

import logging
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth import token_handler, UserContext

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer()


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate requests using JWT tokens
    Injects user context into request state for protected endpoints
    """
    
    # Endpoints that don't require authentication
    PUBLIC_PATHS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/status"
    ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and validate authentication
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response from next handler
        """
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Extract and verify token
        user_context = await self._authenticate_request(request)
        
        if user_context:
            # Inject user context into request state
            request.state.user = user_context
            logger.debug(f"Authenticated user {user_context.user_id} for {request.url.path}")
        else:
            # Authentication failed for protected endpoint
            logger.warning(f"Authentication failed for {request.url.path}")
            return self._unauthorized_response()
        
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require authentication)"""
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)
    
    async def _authenticate_request(self, request: Request) -> Optional[UserContext]:
        """
        Authenticate request by extracting and verifying JWT token
        
        Args:
            request: FastAPI request object
            
        Returns:
            UserContext if authentication successful, None otherwise
        """
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return None
        
        # Parse Bearer token
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "")
        
        # Verify token and extract user context
        user_context = token_handler.verify_token(token)
        
        return user_context
    
    def _unauthorized_response(self):
        """Return unauthorized response"""
        from fastapi.responses import JSONResponse
        from datetime import datetime
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "authentication_failed",
                "message": "Invalid or missing authentication token",
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user(request: Request) -> UserContext:
    """
    Dependency to get current authenticated user from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        UserContext of authenticated user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return request.state.user


async def get_optional_user(request: Request) -> Optional[UserContext]:
    """
    Dependency to get current user if authenticated, None otherwise
    
    Args:
        request: FastAPI request object
        
    Returns:
        UserContext if authenticated, None otherwise
    """
    return getattr(request.state, "user", None)


async def get_current_user_ws(token: str) -> dict:
    """
    Authenticate WebSocket connection using JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        User data dictionary
        
    Raises:
        Exception: If token is invalid
    """
    user_context = token_handler.verify_token(token)
    
    if not user_context:
        raise Exception("Invalid or expired token")
    
    return {
        "user_id": user_context.user_id,
        "business_name": user_context.business_name,
        "industry_code": user_context.industry_code,
        "turnover_tier": user_context.turnover_tier,
        "role": user_context.role
    }

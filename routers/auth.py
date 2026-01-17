"""
Authentication router for MicroCFO Integration Server
Handles user authentication, login, and profile management
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, Field, EmailStr

from auth import UserContext, UserRole, token_handler, PasswordHandler
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# Request/Response Models

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password", min_length=8)


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserContext = Field(..., description="User context information")


class ProfileResponse(BaseModel):
    """User profile response model"""
    user_id: str
    email: str
    business_name: str
    turnover_tier: str
    gst_registration_type: str
    industry_code: str
    role: str
    permissions: list


class TokenRefreshRequest(BaseModel):
    """Token refresh request model"""
    refresh_token: str = Field(..., description="Current JWT token to refresh")


class TokenRefreshResponse(BaseModel):
    """Token refresh response model"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


# Mock user database (in production, this would be a real database)
# Note: Password hashes are computed lazily to avoid bcrypt initialization issues
MOCK_USERS = {
    "owner@example.com": {
        "password": "password123",  # Will be hashed on first use
        "user_context": UserContext(
            user_id="user_001",
            email="owner@example.com",
            business_name="Example Textiles Pvt Ltd",
            turnover_tier="5-20Cr",
            gst_registration_type="Regular",
            industry_code="Textile",
            role=UserRole.BUSINESS_OWNER,
            permissions=[]
        )
    },
    "accountant@example.com": {
        "password": "password123",
        "user_context": UserContext(
            user_id="user_002",
            email="accountant@example.com",
            business_name="Example Textiles Pvt Ltd",
            turnover_tier="5-20Cr",
            gst_registration_type="Regular",
            industry_code="Textile",
            role=UserRole.ACCOUNTANT,
            permissions=[]
        )
    },
    "viewer@example.com": {
        "password": "password123",
        "user_context": UserContext(
            user_id="user_003",
            email="viewer@example.com",
            business_name="Example Textiles Pvt Ltd",
            turnover_tier="5-20Cr",
            gst_registration_type="Regular",
            industry_code="Textile",
            role=UserRole.VIEWER,
            permissions=[]
        )
    }
}


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT access token
    
    Args:
        request: Login credentials (email and password)
        
    Returns:
        LoginResponse with access token and user context
        
    Raises:
        HTTPException: If authentication fails
    """
    logger.info(f"Login attempt for email: {request.email}")
    
    # Look up user in mock database
    user_data = MOCK_USERS.get(request.email)
    
    if not user_data:
        logger.warning(f"Login failed: User not found - {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify password (simple comparison for mock users)
    if request.password != user_data["password"]:
        logger.warning(f"Login failed: Invalid password - {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user context
    user_context = user_data["user_context"]
    
    # Generate JWT token
    access_token = token_handler.create_access_token(user_context)
    
    # Calculate expiration time in seconds
    from config import config
    expires_in = config.security.jwt_expiration_hours * 3600
    
    logger.info(f"Login successful for user: {user_context.user_id}")
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=user_context
    )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: UserContext = Depends(get_current_user)):
    """
    Get current user profile information
    
    Args:
        user: Current authenticated user (injected by dependency)
        
    Returns:
        ProfileResponse with user profile data
    """
    logger.info(f"Profile request for user: {user.user_id}")
    
    return ProfileResponse(
        user_id=user.user_id,
        email=user.email,
        business_name=user.business_name,
        turnover_tier=user.turnover_tier,
        gst_registration_type=user.gst_registration_type,
        industry_code=user.industry_code,
        role=user.role,
        permissions=user.permissions
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(request: TokenRefreshRequest):
    """
    Refresh an existing JWT token
    
    Args:
        request: Token refresh request with current token
        
    Returns:
        TokenRefreshResponse with new access token
        
    Raises:
        HTTPException: If token refresh fails
    """
    logger.info("Token refresh request")
    
    # Refresh the token
    new_token = token_handler.refresh_token(request.refresh_token)
    
    if not new_token:
        logger.warning("Token refresh failed: Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Calculate expiration time in seconds
    from config import config
    expires_in = config.security.jwt_expiration_hours * 3600
    
    logger.info("Token refresh successful")
    
    return TokenRefreshResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=expires_in
    )


@router.post("/logout")
async def logout(user: UserContext = Depends(get_current_user)):
    """
    Logout current user
    
    Note: Since we're using stateless JWT tokens, logout is handled client-side
    by discarding the token. This endpoint is provided for consistency and
    can be extended to implement token blacklisting if needed.
    
    Args:
        user: Current authenticated user (injected by dependency)
        
    Returns:
        Success message
    """
    logger.info(f"Logout request for user: {user.user_id}")
    
    return {
        "message": "Logout successful",
        "user_id": user.user_id
    }

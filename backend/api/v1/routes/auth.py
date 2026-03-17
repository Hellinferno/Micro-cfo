"""
Authentication API Routes
Handles user registration, login, and token management
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from src.database import get_db
from src.models import User, UserProfile
from src.auth import token_handler, PasswordHandler, UserContext, UserRole
from middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============== Request/Response Models ==============

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password", min_length=6)


class RegisterRequest(BaseModel):
    """Registration request model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password", min_length=8)
    full_name: str = Field(..., description="Full name", min_length=2)
    company_name: str = Field(..., description="Company/business name")
    phone_number: Optional[str] = Field(None, description="Phone number")


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserContext = Field(..., description="User context information")


class RegisterResponse(BaseModel):
    """Registration response model"""
    message: str
    user_id: str
    email: str
    access_token: Optional[str] = None


class ProfileResponse(BaseModel):
    """User profile response model"""
    user_id: str
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    phone_number: Optional[str]
    business_sector: Optional[str]
    turnover_tier: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    profile: Optional[dict] = None


class UpdateProfileRequest(BaseModel):
    """Update profile request model"""
    full_name: Optional[str] = Field(None, min_length=2)
    company_name: Optional[str] = None
    phone_number: Optional[str] = None
    business_sector: Optional[str] = None
    turnover_tier: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    registered_address: Optional[str] = None


# ============== Routes ==============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token

    Args:
        request: Login credentials (email and password)
        db: Database session

    Returns:
        LoginResponse with access token and user context

    Raises:
        HTTPException: If authentication fails
    """
    # Look up user in database
    stmt = select(User).where(User.email == request.email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify password
    if not PasswordHandler.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Create user context
    user_context = UserContext(
        user_id=str(user.id),
        email=user.email,
        business_name=user.company_name or "Unknown Business",
        turnover_tier=user.turnover_tier or "Not specified",
        gst_registration_type="Regular",  # Default, can be updated
        industry_code=user.business_sector or "General",
        role=UserRole(user.role) if user.role else UserRole.BUSINESS_OWNER,
        permissions=[]
    )

    # Generate JWT token
    access_token = token_handler.create_access_token(user_context)
    expires_in = 24 * 3600  # 24 hours

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=user_context
    )


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account

    Args:
        request: Registration details
        db: Database session

    Returns:
        RegisterResponse with user information

    Raises:
        HTTPException: If email already exists or validation fails
    """
    # Check if email already exists
    stmt = select(User).where(User.email == request.email)
    existing_user = db.execute(stmt).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = PasswordHandler.hash_password(request.password)

    # Create new user
    new_user = User(
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
        company_name=request.company_name,
        phone_number=request.phone_number,
        role="owner",
        is_active=True,
        is_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create user profile
    user_profile = UserProfile(
        user_id=new_user.id,
        preferences={}
    )
    db.add(user_profile)
    db.commit()

    # Auto-login after registration
    user_context = UserContext(
        user_id=str(new_user.id),
        email=new_user.email,
        business_name=new_user.company_name or "Unknown Business",
        turnover_tier=new_user.turnover_tier or "Not specified",
        gst_registration_type="Regular",
        industry_code=new_user.business_sector or "General",
        role=UserRole.BUSINESS_OWNER,
        permissions=[]
    )

    access_token = token_handler.create_access_token(user_context)

    return RegisterResponse(
        message="Registration successful",
        user_id=str(new_user.id),
        email=new_user.email,
        access_token=access_token
    )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile information

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        ProfileResponse with user profile data
    """
    # Get user from database
    stmt = select(User).where(User.id == uuid.UUID(current_user.user_id))
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user profile
    profile_stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    profile = db.execute(profile_stmt).scalar_one_or_none()

    profile_data = None
    if profile:
        profile_data = {
            "id": str(profile.id),
            "business_type": profile.business_type,
            "gst_number": profile.gst_number,
            "pan_number": profile.pan_number,
            "registered_address": profile.registered_address,
            "preferences": profile.preferences or {}
        }

    return ProfileResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        company_name=user.company_name,
        phone_number=user.phone_number,
        business_sector=user.business_sector,
        turnover_tier=user.turnover_tier,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        profile=profile_data
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile

    Args:
        request: Profile update data
        current_user: Authenticated user
        db: Database session

    Returns:
        ProfileResponse with updated profile data
    """
    # Get user from database
    stmt = select(User).where(User.id == uuid.UUID(current_user.user_id))
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update user fields
    update_fields = request.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # Get updated profile
    profile_stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    profile = db.execute(profile_stmt).scalar_one_or_none()

    profile_data = None
    if profile:
        profile_data = {
            "id": str(profile.id),
            "business_type": profile.business_type,
            "gst_number": profile.gst_number,
            "pan_number": profile.pan_number,
            "registered_address": profile.registered_address,
            "preferences": profile.preferences or {}
        }

    return ProfileResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        company_name=user.company_name,
        phone_number=user.phone_number,
        business_sector=user.business_sector,
        turnover_tier=user.turnover_tier,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        profile=profile_data
    )


@router.post("/logout")
async def logout(current_user: UserContext = Depends(get_current_user)):
    """
    Logout current user

    Note: Since we're using stateless JWT tokens, logout is handled client-side
    by discarding the token. This endpoint is provided for logging purposes.

    Args:
        current_user: Authenticated user

    Returns:
        Success message
    """
    return {
        "message": "Logout successful",
        "user_id": current_user.user_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/refresh")
async def refresh_token(current_user: UserContext = Depends(get_current_user)):
    """
    Refresh current JWT token

    Args:
        current_user: Authenticated user

    Returns:
        New access token
    """
    new_token = token_handler.refresh_token(
        token_handler.create_access_token(current_user)
    )

    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": 24 * 3600
    }

"""
Authentication module for MicroCFO Integration Server
Handles JWT token generation, validation, and user context management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

import jwt
import bcrypt
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User role enumeration"""
    BUSINESS_OWNER = "business_owner"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class UserContext(BaseModel):
    """
    User context model with business profile data
    Maintains user session information and business context
    """
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    business_name: str = Field(..., description="Business name")
    turnover_tier: str = Field(..., description="Turnover tier: <5Cr, 5-20Cr, >20Cr")
    gst_registration_type: str = Field(..., description="GST registration type")
    industry_code: str = Field(..., description="Industry classification code")
    role: UserRole = Field(..., description="User role in the system")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    
    class Config:
        use_enum_values = True


class TokenData(BaseModel):
    """Token payload data"""
    sub: str  # Subject (user_id)
    email: str
    role: str
    exp: datetime
    iat: datetime


class JWTTokenHandler:
    """
    JWT token handler for authentication
    Handles token generation, validation, and decoding
    """
    
    def __init__(self):
        self.secret_key = config.security.jwt_secret_key
        self.algorithm = config.security.jwt_algorithm
        self.expiration_hours = config.security.jwt_expiration_hours
    
    def create_access_token(self, user_context: UserContext) -> str:
        """
        Create a JWT access token for a user
        
        Args:
            user_context: User context with business profile data
            
        Returns:
            str: Encoded JWT token
        """
        now = datetime.utcnow()
        expire = now + timedelta(hours=self.expiration_hours)
        
        payload = {
            "sub": user_context.user_id,
            "email": user_context.email,
            "role": user_context.role,
            "business_name": user_context.business_name,
            "turnover_tier": user_context.turnover_tier,
            "gst_registration_type": user_context.gst_registration_type,
            "industry_code": user_context.industry_code,
            "permissions": user_context.permissions,
            "exp": expire,
            "iat": now
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Created access token for user {user_context.user_id}")
        
        return token
    
    def verify_token(self, token: str) -> Optional[UserContext]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            UserContext if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Extract user context from payload
            user_context = UserContext(
                user_id=payload["sub"],
                email=payload["email"],
                business_name=payload["business_name"],
                turnover_tier=payload["turnover_tier"],
                gst_registration_type=payload["gst_registration_type"],
                industry_code=payload["industry_code"],
                role=payload["role"],
                permissions=payload.get("permissions", [])
            )
            
            logger.debug(f"Token verified for user {user_context.user_id}")
            return user_context
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh an existing token
        
        Args:
            token: Current JWT token
            
        Returns:
            New JWT token if current token is valid, None otherwise
        """
        user_context = self.verify_token(token)
        if user_context:
            return self.create_access_token(user_context)
        return None


class PasswordHandler:
    """
    Password hashing and verification handler
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password, salt).decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)


# Global token handler instance
token_handler = JWTTokenHandler()

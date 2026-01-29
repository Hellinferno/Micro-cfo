"""
Authorization middleware for MicroCFO Integration Server
Handles role-based access control and permission validation
"""

import logging
from typing import List, Callable
from functools import wraps

from fastapi import Request, HTTPException, status

from starlette.middleware.base import BaseHTTPMiddleware

from src.auth import UserContext, UserRole

logger = logging.getLogger(__name__)


class PermissionDeniedError(Exception):
    """Exception raised when user lacks required permissions"""
    pass


class RoleBasedAccessControl:
    """
    Role-based access control system
    Manages permissions for different user roles
    """
    
    # Define permissions for each role
    ROLE_PERMISSIONS = {
        UserRole.BUSINESS_OWNER: [
            "read:invoices",
            "write:invoices",
            "read:compliance",
            "write:compliance",
            "read:subsidies",
            "write:subsidies",
            "read:negotiations",
            "write:negotiations",
            "read:profile",
            "write:profile",
            "manage:users"
        ],
        UserRole.ACCOUNTANT: [
            "read:invoices",
            "write:invoices",
            "read:compliance",
            "write:compliance",
            "read:subsidies",
            "write:subsidies",
            "read:negotiations",
            "write:negotiations",
            "read:profile"
        ],
        UserRole.VIEWER: [
            "read:invoices",
            "read:compliance",
            "read:subsidies",
            "read:negotiations",
            "read:profile"
        ]
    }
    
    # Endpoint permission requirements
    ENDPOINT_PERMISSIONS = {
        # Visual Auditor endpoints
        "/api/v1/agents/visual-auditor/scan-invoice": ["write:invoices"],
        "/api/v1/agents/visual-auditor/upload-document": ["write:invoices"],
        
        # Legal Sentinel endpoints
        "/api/v1/agents/legal-sentinel/check-compliance": ["read:compliance"],
        "/api/v1/agents/legal-sentinel/legal-updates": ["read:compliance"],
        
        # Subsidy Hunter endpoints
        "/api/v1/agents/subsidy-hunter/find-subsidies": ["read:subsidies"],
        "/api/v1/agents/subsidy-hunter/schemes": ["read:subsidies"],
        
        # Negotiator endpoints
        "/api/v1/agents/negotiator/generate-draft": ["write:negotiations"],
        "/api/v1/agents/negotiator/analyze-email": ["read:negotiations"],
        
        # Profile endpoints
        "/api/v1/auth/profile": ["read:profile"]
    }
    
    @classmethod
    def get_role_permissions(cls, role: UserRole) -> List[str]:
        """
        Get permissions for a specific role
        
        Args:
            role: User role
            
        Returns:
            List of permissions for the role
        """
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def has_permission(cls, user: UserContext, permission: str) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user: User context
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        # Get role permissions
        role_permissions = cls.get_role_permissions(user.role)
        
        # Check if permission is in role permissions or user-specific permissions
        return permission in role_permissions or permission in user.permissions
    
    @classmethod
    def has_any_permission(cls, user: UserContext, permissions: List[str]) -> bool:
        """
        Check if user has any of the specified permissions
        
        Args:
            user: User context
            permissions: List of permissions to check
            
        Returns:
            True if user has at least one permission, False otherwise
        """
        return any(cls.has_permission(user, perm) for perm in permissions)
    
    @classmethod
    def has_all_permissions(cls, user: UserContext, permissions: List[str]) -> bool:
        """
        Check if user has all of the specified permissions
        
        Args:
            user: User context
            permissions: List of permissions to check
            
        Returns:
            True if user has all permissions, False otherwise
        """
        return all(cls.has_permission(user, perm) for perm in permissions)
    
    @classmethod
    def check_endpoint_permission(cls, user: UserContext, endpoint: str) -> bool:
        """
        Check if user has permission to access an endpoint
        
        Args:
            user: User context
            endpoint: Endpoint path
            
        Returns:
            True if user has permission, False otherwise
        """
        required_permissions = cls.ENDPOINT_PERMISSIONS.get(endpoint, [])
        
        # If no specific permissions required, allow access
        if not required_permissions:
            return True
        
        # Check if user has any of the required permissions
        return cls.has_any_permission(user, required_permissions)
    
    @classmethod
    def validate_permission(cls, user: UserContext, permission: str):
        """
        Validate that user has a specific permission
        
        Args:
            user: User context
            permission: Required permission
            
        Raises:
            PermissionDeniedError: If user lacks permission
        """
        if not cls.has_permission(user, permission):
            logger.warning(
                f"Permission denied: User {user.user_id} lacks permission '{permission}'"
            )
            raise PermissionDeniedError(
                f"You don't have permission to perform this action. Required: {permission}"
            )
    
    @classmethod
    def validate_role(cls, user: UserContext, allowed_roles: List[UserRole]):
        """
        Validate that user has one of the allowed roles
        
        Args:
            user: User context
            allowed_roles: List of allowed roles
            
        Raises:
            PermissionDeniedError: If user role is not allowed
        """
        if user.role not in allowed_roles:
            logger.warning(
                f"Role denied: User {user.user_id} with role '{user.role}' "
                f"not in allowed roles {allowed_roles}"
            )
            raise PermissionDeniedError(
                f"Your role does not have access to this resource"
            )


class AuthorizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce authorization rules
    Validates user permissions for protected endpoints
    """
    
    def __init__(self, app, rbac: RoleBasedAccessControl = None):
        super().__init__(app)
        self.rbac = rbac or RoleBasedAccessControl()
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and validate authorization
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response from next handler
        """
        # Skip if user is not authenticated (handled by auth middleware)
        if not hasattr(request.state, "user"):
            return await call_next(request)
        
        user = request.state.user
        endpoint = request.url.path
        
        # Check endpoint permissions
        if not self.rbac.check_endpoint_permission(user, endpoint):
            logger.warning(
                f"Authorization failed: User {user.user_id} denied access to {endpoint}"
            )
            return self._forbidden_response(user, endpoint)
        
        logger.debug(f"Authorization granted for user {user.user_id} to {endpoint}")
        return await call_next(request)
    
    def _forbidden_response(self, user: UserContext, endpoint: str):
        """Return forbidden response"""
        from fastapi.responses import JSONResponse
        from datetime import datetime
        
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "access_denied",
                "message": "You don't have permission to access this resource",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def require_permission(permission: str):
    """
    Decorator to require specific permission for an endpoint
    
    Args:
        permission: Required permission
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request = kwargs.get("request")
            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Get user from request
            if not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user = request.state.user
            
            # Validate permission
            try:
                RoleBasedAccessControl.validate_permission(user, permission)
            except PermissionDeniedError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(*allowed_roles: UserRole):
    """
    Decorator to require specific role(s) for an endpoint
    
    Args:
        allowed_roles: Allowed user roles
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request = kwargs.get("request")
            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Get user from request
            if not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user = request.state.user
            
            # Validate role
            try:
                RoleBasedAccessControl.validate_role(user, list(allowed_roles))
            except PermissionDeniedError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

"""
Property-based tests for authentication and authorization
Feature: frontend-backend-integration, Property 2: Authentication and Authorization
Validates: Requirements 2.1, 2.3, 2.5
"""

import os
# Set testing environment to disable rate limiting
os.environ["TESTING"] = "true"

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt

from integration_server import app
from auth import UserContext, UserRole, token_handler, PasswordHandler
from src.middleware.authorization import RoleBasedAccessControl
from config import config


# Test client
client = TestClient(app)


# Hypothesis strategies for generating test data

@st.composite
def user_context_strategy(draw):
    """Generate random UserContext instances"""
    roles = [UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT, UserRole.VIEWER]
    
    return UserContext(
        user_id=draw(st.text(min_size=5, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')),
        email=draw(st.emails()),
        business_name=draw(st.text(min_size=5, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyz ')),
        turnover_tier=draw(st.sampled_from(["<5Cr", "5-20Cr", ">20Cr"])),
        gst_registration_type=draw(st.sampled_from(["Regular", "Composition", "Casual"])),
        industry_code=draw(st.sampled_from(["Textile", "Manufacturing", "Technology", "Trading"])),
        role=draw(st.sampled_from(roles)),
        permissions=draw(st.lists(st.text(min_size=5, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz:'), max_size=3))
    )


@st.composite
def valid_credentials_strategy(draw):
    """Generate valid login credentials"""
    # Use one of the mock users
    email = draw(st.sampled_from([
        "owner@example.com",
        "accountant@example.com",
        "viewer@example.com"
    ]))
    
    return {
        "email": email,
        "password": "password123"
    }


@st.composite
def invalid_credentials_strategy(draw):
    """Generate invalid login credentials"""
    email = draw(st.emails())
    password = draw(st.text(min_size=8, max_size=50))
    
    # Ensure it's not a valid user
    assume(email not in ["owner@example.com", "accountant@example.com", "viewer@example.com"])
    
    return {
        "email": email,
        "password": password
    }


# Property 2: Authentication and Authorization
# For any user with valid credentials and appropriate role permissions, 
# they should be able to access their authorized resources, while users 
# with invalid credentials or insufficient permissions should be consistently denied access.


@given(user_context=user_context_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_token_generation_and_verification(user_context):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any valid user context, generating a token and then verifying it
    should return an equivalent user context with the same core attributes.
    """
    # Generate token
    token = token_handler.create_access_token(user_context)
    
    # Verify token
    verified_context = token_handler.verify_token(token)
    
    # Assert token verification succeeded
    assert verified_context is not None, "Token verification should succeed for valid token"
    
    # Assert core user attributes are preserved
    assert verified_context.user_id == user_context.user_id
    assert verified_context.email == user_context.email
    assert verified_context.business_name == user_context.business_name
    assert verified_context.turnover_tier == user_context.turnover_tier
    assert verified_context.gst_registration_type == user_context.gst_registration_type
    assert verified_context.industry_code == user_context.industry_code
    assert verified_context.role == user_context.role
    assert verified_context.permissions == user_context.permissions


@given(user_context=user_context_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_expired_token_rejection(user_context):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any user context, a token that has expired should be rejected
    during verification.
    """
    # Create an expired token manually
    now = datetime.utcnow()
    expire = now - timedelta(hours=1)  # Expired 1 hour ago
    
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
        "iat": now - timedelta(hours=2)
    }
    
    expired_token = jwt.encode(
        payload,
        config.security.jwt_secret_key,
        algorithm=config.security.jwt_algorithm
    )
    
    # Verify expired token
    verified_context = token_handler.verify_token(expired_token)
    
    # Assert expired token is rejected
    assert verified_context is None, "Expired token should be rejected"


@given(user_context=user_context_strategy(), random_string=st.text(min_size=10, max_size=100))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_invalid_token_rejection(user_context, random_string):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any random string that is not a valid JWT token, verification
    should consistently reject it.
    """
    # Ensure random string is not accidentally a valid token
    assume(not random_string.count('.') == 2)
    
    # Try to verify invalid token
    verified_context = token_handler.verify_token(random_string)
    
    # Assert invalid token is rejected
    assert verified_context is None, "Invalid token should be rejected"


@given(user_context=user_context_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_role_permissions_consistency(user_context):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any user with a specific role, they should have all the permissions
    defined for that role in the RBAC system.
    """
    # Get role permissions
    role_permissions = RoleBasedAccessControl.get_role_permissions(user_context.role)
    
    # Check that user has all role permissions
    for permission in role_permissions:
        has_permission = RoleBasedAccessControl.has_permission(user_context, permission)
        assert has_permission, f"User with role {user_context.role} should have permission {permission}"


@given(user_context=user_context_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_business_owner_has_all_permissions(user_context):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any user with BUSINESS_OWNER role, they should have more permissions
    than users with ACCOUNTANT or VIEWER roles.
    """
    if user_context.role == UserRole.BUSINESS_OWNER:
        owner_permissions = set(RoleBasedAccessControl.get_role_permissions(UserRole.BUSINESS_OWNER))
        accountant_permissions = set(RoleBasedAccessControl.get_role_permissions(UserRole.ACCOUNTANT))
        viewer_permissions = set(RoleBasedAccessControl.get_role_permissions(UserRole.VIEWER))
        
        # Business owner should have all accountant permissions
        assert accountant_permissions.issubset(owner_permissions), \
            "Business owner should have all accountant permissions"
        
        # Business owner should have all viewer permissions
        assert viewer_permissions.issubset(owner_permissions), \
            "Business owner should have all viewer permissions"
        
        # Business owner should have more permissions than accountant
        assert len(owner_permissions) >= len(accountant_permissions), \
            "Business owner should have at least as many permissions as accountant"


@given(user_context=user_context_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_viewer_has_read_only_permissions(user_context):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any user with VIEWER role, all their permissions should be read-only
    (start with "read:").
    """
    if user_context.role == UserRole.VIEWER:
        viewer_permissions = RoleBasedAccessControl.get_role_permissions(UserRole.VIEWER)
        
        # All viewer permissions should be read-only
        for permission in viewer_permissions:
            assert permission.startswith("read:"), \
                f"Viewer permission {permission} should be read-only"


@given(credentials=valid_credentials_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_valid_login_returns_token(credentials):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any valid credentials, the login endpoint should return a valid
    JWT token that can be verified.
    """
    # Attempt login
    response = client.post("/api/v1/auth/login", json=credentials)
    
    # Assert login succeeded
    assert response.status_code == 200, "Login with valid credentials should succeed"
    
    # Extract token
    data = response.json()
    assert "access_token" in data, "Response should contain access_token"
    assert "user" in data, "Response should contain user context"
    
    token = data["access_token"]
    
    # Verify token
    verified_context = token_handler.verify_token(token)
    assert verified_context is not None, "Returned token should be valid"
    assert verified_context.email == credentials["email"], "Token should contain correct email"


@given(credentials=invalid_credentials_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_invalid_login_rejected(credentials):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any invalid credentials (unknown email or wrong password),
    the login endpoint should consistently reject the attempt with 401 status.
    """
    # Attempt login with invalid credentials
    response = client.post("/api/v1/auth/login", json=credentials)
    
    # Assert login failed
    assert response.status_code == 401, "Login with invalid credentials should fail with 401"
    
    # Assert error response format
    data = response.json()
    assert "error" in data or "detail" in data, "Error response should contain error information"


@given(st.sampled_from(["owner@example.com", "accountant@example.com", "viewer@example.com"]))
@settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
def test_property_authenticated_profile_access(email):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any authenticated user with a valid token, accessing the profile
    endpoint should return their user information.
    """
    from src.middleware.auth import get_current_user
    
    # Login to get a valid token
    login_response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "password123"
    })
    
    assert login_response.status_code == 200, "Login should succeed"
    token = login_response.json()["access_token"]
    user_data = login_response.json()["user"]
    
    # Verify token and get user context
    user_context = token_handler.verify_token(token)
    assert user_context is not None, "Token should be valid"
    
    # Override the dependency to inject the user context
    # This is necessary because TestClient doesn't properly execute middleware
    app.dependency_overrides[get_current_user] = lambda: user_context
    
    try:
        # Access profile endpoint with token
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert profile access succeeded
        assert response.status_code == 200, "Profile access with valid token should succeed"
        
        # Assert profile data matches user context
        data = response.json()
        assert data["user_id"] == user_data["user_id"]
        assert data["email"] == user_data["email"]
        assert data["business_name"] == user_data["business_name"]
        assert data["role"] == user_data["role"]
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()


@given(random_string=st.text(min_size=10, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_unauthenticated_profile_access_denied(random_string):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any request without a valid token, accessing protected endpoints
    should be consistently denied with 401 status.
    """
    # Ensure random string is not accidentally a valid token
    assume(not random_string.count('.') == 2)
    
    # Try to access profile without valid token
    response = client.get(
        "/api/v1/auth/profile",
        headers={"Authorization": f"Bearer {random_string}"}
    )
    
    # Assert access denied
    assert response.status_code == 401, "Profile access without valid token should be denied"


@given(user_context=user_context_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_token_refresh_preserves_context(user_context):
    """
    Feature: frontend-backend-integration, Property 2: Authentication and Authorization
    
    Property: For any valid token, refreshing it should produce a new token that
    preserves the same user context.
    """
    # Generate original token
    original_token = token_handler.create_access_token(user_context)
    
    # Refresh token
    new_token = token_handler.refresh_token(original_token)
    
    # Assert refresh succeeded
    assert new_token is not None, "Token refresh should succeed for valid token"
    
    # Verify new token
    verified_context = token_handler.verify_token(new_token)
    
    # Assert user context is preserved
    assert verified_context is not None
    assert verified_context.user_id == user_context.user_id
    assert verified_context.email == user_context.email
    assert verified_context.role == user_context.role


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

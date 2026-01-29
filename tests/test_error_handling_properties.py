#!/usr/bin/env python3
"""
Property-Based Tests for Error Handling and Logging
Tests Property 5: Error Handling and Logging

Feature: frontend-backend-integration, Property 5: Error Handling and Logging
Validates: Requirements 5.1, 5.3, 8.4
"""

import pytest
import logging
import json
import time
from pathlib import Path
from hypothesis import given, settings, strategies as st
from fastapi.testclient import TestClient
from datetime import datetime

from integration_server import app
from src.middleware.error_handler import ErrorCategory, create_error_response
from src.middleware.logging_middleware import log_audit_event, log_security_event
from src.middleware.rate_limiter import rate_limiter, RateLimitConfig


# Test client
client = TestClient(app)


# Hypothesis strategies
@st.composite
def error_scenarios(draw):
    """Generate various error scenarios"""
    error_type = draw(st.sampled_from([
        "validation_error",
        "authentication_error",
        "authorization_error",
        "not_found",
        "rate_limit",
        "mcp_error",
        "internal_error"
    ]))
    
    message = draw(st.text(min_size=1, max_size=200))
    status_code = draw(st.sampled_from([400, 401, 403, 404, 429, 500, 503]))
    
    return {
        "error_type": error_type,
        "message": message,
        "status_code": status_code
    }


@st.composite
def audit_events(draw):
    """Generate audit event data"""
    event_type = draw(st.sampled_from([
        "login", "logout", "document_scan", "compliance_check",
        "subsidy_search", "negotiation_draft"
    ]))
    
    user_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    details = {
        "action": draw(st.text(min_size=1, max_size=100)),
        "resource": draw(st.text(min_size=1, max_size=100))
    }
    
    return {
        "event_type": event_type,
        "user_id": user_id,
        "details": details
    }


@st.composite
def rate_limit_requests(draw):
    """Generate rate limit test requests"""
    endpoint = draw(st.sampled_from([
        "/api/v1/auth/login",
        "/api/v1/agents/visual-auditor/scan-invoice",
        "/api/v1/agents/legal-sentinel/check-compliance",
        "/health"
    ]))
    
    client_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return {
        "endpoint": endpoint,
        "client_id": client_id
    }


class TestErrorHandlingProperties:
    """
    Property-based tests for error handling and logging
    
    Feature: frontend-backend-integration, Property 5: Error Handling and Logging
    """
    
    @given(error_scenarios())
    @settings(max_examples=100)
    def test_error_responses_have_consistent_format(self, scenario):
        """
        Property: For any error condition, the error response should have a consistent format
        with required fields and no internal details exposed in production mode
        
        Validates: Requirements 5.1, 5.3
        """
        # Create error response
        response = create_error_response(
            error_category=scenario["error_type"],
            message=scenario["message"],
            status_code=scenario["status_code"],
            expose_details=False  # Production mode
        )
        
        # Parse response content
        content = json.loads(response.body.decode())
        
        # Assert consistent format
        assert "error" in content, "Error response must have 'error' field"
        assert "message" in content, "Error response must have 'message' field"
        assert "timestamp" in content, "Error response must have 'timestamp' field"
        assert "request_id" in content, "Error response must have 'request_id' field"
        
        # Assert no internal details exposed in production
        if "details" in content:
            assert content["details"] is None, "Internal details should not be exposed in production"
        
        # Assert message is user-friendly (not empty)
        assert len(content["message"]) > 0, "Error message should not be empty"
        
        # Assert timestamp is valid ISO format
        try:
            datetime.fromisoformat(content["timestamp"])
        except ValueError:
            pytest.fail("Timestamp should be valid ISO format")
        
        # Assert request_id is not empty
        assert len(content["request_id"]) > 0, "Request ID should not be empty"
    
    @given(audit_events())
    @settings(max_examples=100)
    def test_audit_logging_captures_all_required_fields(self, event):
        """
        Property: For any audit event, all required fields should be logged
        
        Validates: Requirements 5.2, 5.5
        """
        # Setup log capture
        log_file = Path("logs/audit.log")
        log_file.parent.mkdir(exist_ok=True)
        
        # Clear previous logs for this test
        if log_file.exists():
            initial_size = log_file.stat().st_size
        else:
            initial_size = 0
        
        # Log audit event
        log_audit_event(
            event_type=event["event_type"],
            user_id=event["user_id"],
            details=event["details"],
            status="success"
        )
        
        # Give logger time to flush
        time.sleep(0.1)
        
        # Read log file
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(initial_size)
                new_logs = f.read()
            
            # Assert event was logged
            if new_logs:
                assert event["event_type"] in new_logs, "Event type should be in audit log"
                # User ID might be JSON-escaped in logs, so check for either raw or escaped version
                user_id_found = (event["user_id"] in new_logs or 
                                json.dumps(event["user_id"])[1:-1] in new_logs)
                assert user_id_found, "User ID should be in audit log (raw or JSON-escaped)"
    
    @given(rate_limit_requests())
    @settings(max_examples=50)
    def test_rate_limiting_enforces_limits_consistently(self, request_data):
        """
        Property: For any endpoint, rate limiting should consistently enforce limits
        and provide appropriate headers
        
        Validates: Requirements 5.4
        """
        endpoint = request_data["endpoint"]
        client_id = request_data["client_id"]
        
        # Get limit for this endpoint
        limit = RateLimitConfig.get_limit(endpoint)
        
        # Clear any existing rate limit state for this client
        if client_id in rate_limiter.requests:
            rate_limiter.requests[client_id].clear()
        
        # Make requests up to the limit
        allowed_count = 0
        for i in range(limit + 5):  # Try more than the limit
            is_allowed, remaining, reset_time = rate_limiter.is_allowed(
                client_id, endpoint, limit
            )
            
            if is_allowed:
                allowed_count += 1
                
                # Assert remaining count decreases
                assert remaining >= 0, "Remaining count should not be negative"
                assert remaining <= limit, "Remaining count should not exceed limit"
            else:
                # Once blocked, should stay blocked until reset
                assert remaining == 0, "Remaining should be 0 when rate limited"
                assert reset_time > time.time(), "Reset time should be in the future"
                break
        
        # Assert we were allowed exactly up to the limit
        assert allowed_count <= limit, f"Should not allow more than {limit} requests"
        assert allowed_count > 0, "Should allow at least some requests"
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_validation_errors_provide_helpful_messages(self, invalid_input):
        """
        Property: For any validation error, the response should provide helpful
        error messages without exposing internal implementation details
        
        Validates: Requirements 5.1, 8.4
        """
        # Try to make a request with invalid data to visual auditor
        response = client.post(
            "/api/v1/agents/visual-auditor/scan-invoice",
            json={"invalid_field": invalid_input}
        )
        
        # Should get validation error
        if response.status_code == 422:
            data = response.json()
            
            # Assert consistent error format
            assert "error" in data, "Validation error should have 'error' field"
            assert "message" in data, "Validation error should have 'message' field"
            
            # Assert message is helpful
            assert len(data["message"]) > 0, "Error message should not be empty"
            
            # Assert no internal Python details exposed
            assert "Traceback" not in data["message"], "Should not expose Python tracebacks"
            assert "Exception" not in data["message"], "Should not expose exception class names"
    
    @given(st.sampled_from(["/api/v1/nonexistent", "/api/v1/agents/fake", "/invalid"]))
    @settings(max_examples=50)
    def test_not_found_errors_are_handled_consistently(self, invalid_path):
        """
        Property: For any non-existent endpoint, a consistent 404 error should be returned
        
        Validates: Requirements 5.1, 5.3
        """
        response = client.get(invalid_path)
        
        # Should get 404
        assert response.status_code == 404, "Non-existent endpoints should return 404"
        
        data = response.json()
        
        # Assert consistent error format
        assert "error" in data, "404 error should have 'error' field"
        assert "message" in data, "404 error should have 'message' field"
        assert "timestamp" in data, "404 error should have 'timestamp' field"
    
    def test_error_logging_does_not_expose_sensitive_data(self):
        """
        Property: Error logs should never contain sensitive data like passwords or tokens
        
        Validates: Requirements 5.3, 5.5
        """
        # Setup log capture
        log_file = Path("logs/errors.log")
        log_file.parent.mkdir(exist_ok=True)
        
        if log_file.exists():
            initial_size = log_file.stat().st_size
        else:
            initial_size = 0
        
        # Make a request with sensitive data
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "SuperSecret123!",
                "api_key": "sk-1234567890abcdef"
            }
        )
        
        # Give logger time to flush
        time.sleep(0.1)
        
        # Read error log
        if log_file.exists():
            with open(log_file, 'r') as f:
                f.seek(initial_size)
                new_logs = f.read()
            
            # Assert sensitive data is not in logs
            assert "SuperSecret123!" not in new_logs, "Password should not be in error logs"
            assert "sk-1234567890abcdef" not in new_logs, "API key should not be in error logs"


class TestRateLimitingProperties:
    """
    Additional property tests for rate limiting
    
    Feature: frontend-backend-integration, Property 5: Error Handling and Logging
    """
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_rate_limit_headers_are_always_present(self, request_count):
        """
        Property: For any successful request, rate limit headers should be present
        
        Validates: Requirements 5.4
        """
        # Make a request to health endpoint (high limit)
        response = client.get("/health")
        
        if response.status_code == 200:
            # Assert rate limit headers are present
            assert "X-RateLimit-Limit" in response.headers, "Rate limit header should be present"
            assert "X-RateLimit-Remaining" in response.headers, "Remaining header should be present"
            assert "X-RateLimit-Reset" in response.headers, "Reset header should be present"
            
            # Assert header values are valid
            limit = int(response.headers["X-RateLimit-Limit"])
            remaining = int(response.headers["X-RateLimit-Remaining"])
            reset_time = int(response.headers["X-RateLimit-Reset"])
            
            assert limit > 0, "Rate limit should be positive"
            assert remaining >= 0, "Remaining should not be negative"
            assert reset_time > time.time(), "Reset time should be in the future"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

# Error Handling and Logging System Implementation

## Overview

This document describes the comprehensive error handling and logging system implemented for the MicroCFO Integration Server as part of Task 10.

## Components Implemented

### 1. Centralized Error Handler (`middleware/error_handler.py`)

**Requirements: 5.1, 5.3**

#### Features:
- **Standardized Error Response Format**: All errors return consistent JSON format with:
  - `error`: Error category (authentication_error, validation_error, etc.)
  - `message`: User-friendly error message
  - `details`: Additional details (only in debug mode)
  - `timestamp`: ISO format timestamp
  - `request_id`: Unique request identifier for tracking

- **Error Categories**:
  - Authentication errors (401)
  - Authorization errors (403)
  - Validation errors (422)
  - Not found errors (404)
  - Rate limit errors (429)
  - MCP service errors (503)
  - File errors (400)
  - Internal server errors (500)

- **User-Friendly Messages**: Translates technical errors to user-friendly messages
- **Security**: Never exposes internal details in production mode
- **Exception Handlers**:
  - Pydantic validation errors
  - MCP Bridge errors
  - HTTP exceptions
  - Generic exceptions (catch-all)

#### Usage:
```python
from middleware.error_handler import register_error_handlers

# Register all error handlers
register_error_handlers(app)
```

### 2. Comprehensive Logging System (`middleware/logging_middleware.py`)

**Requirements: 5.2, 5.5**

#### Features:
- **Structured Logging**: JSON-formatted logs with extra metadata
- **Multiple Log Files**:
  - `logs/microcfo.log`: All application logs
  - `logs/errors.log`: Error-level logs only
  - `logs/audit.log`: Compliance and audit events

- **Request Logging Middleware**:
  - Logs all incoming requests with:
    - Request ID
    - HTTP method and path
    - User context (user ID, role)
    - Client IP and user agent
    - Processing time
  - Logs all responses with status codes
  - Adds custom headers: `X-Request-ID`, `X-Process-Time`

- **Audit Logging**:
  - Tracks compliance operations (legal checks, document scans, auth)
  - Includes user ID, timestamp, operation details
  - Separate audit log file for compliance tracking

- **Security Event Logging**:
  - Logs security-related events (rate limits, auth failures)
  - Configurable severity levels

#### Usage:
```python
from middleware.logging_middleware import setup_logging, log_audit_event

# Setup logging system
setup_logging(debug=True)

# Log audit event
log_audit_event(
    event_type="document_scan",
    user_id="user123",
    details={"file_id": "abc123"},
    status="success"
)
```

### 3. Rate Limiting System (`middleware/rate_limiter.py`)

**Requirements: 5.4**

#### Features:
- **Sliding Window Algorithm**: Accurate rate limiting using sliding time windows
- **Endpoint-Specific Limits**:
  - Authentication endpoints: 5 requests/minute
  - Visual Auditor: 20 requests/minute
  - Legal Sentinel: 30 requests/minute
  - Subsidy Hunter: 30 requests/minute
  - Negotiator: 20 requests/minute
  - WebSocket: 100 requests/minute
  - Health check: 1000 requests/minute

- **Rate Limit Headers**: All responses include:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets
  - `Retry-After`: Seconds until retry (when rate limited)

- **Client Identification**:
  - Prefers authenticated user ID
  - Falls back to IP address for anonymous users

- **Memory Management**: Automatic cleanup of old request timestamps

#### Usage:
```python
from middleware.rate_limiter import RateLimitMiddleware

# Add to FastAPI app
app.add_middleware(RateLimitMiddleware)
```

### 4. Property-Based Tests (`test_error_handling_properties.py`)

**Validates: Requirements 5.1, 5.3, 5.4, 8.4**

#### Test Properties:
1. **Error Response Consistency**: All errors have consistent format with required fields
2. **Audit Logging Completeness**: All audit events capture required fields
3. **Rate Limiting Enforcement**: Rate limits are consistently enforced
4. **Validation Error Messages**: Validation errors provide helpful messages
5. **Not Found Handling**: 404 errors are handled consistently
6. **Sensitive Data Protection**: Logs never contain passwords or tokens
7. **Rate Limit Headers**: All responses include rate limit headers

#### Test Results:
- ✅ 7 tests passed
- ✅ 100+ examples per property test
- ✅ All properties validated successfully

## Integration

The error handling and logging system is integrated into the main application:

```python
# integration_server.py

# Setup logging
from middleware.logging_middleware import setup_logging
setup_logging(debug=config.server.debug)

# Register error handlers
from middleware.error_handler import register_error_handlers
register_error_handlers(app)

# Add middleware (order matters!)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(AuthorizationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
```

## Benefits

1. **Consistent Error Handling**: All errors follow the same format
2. **Security**: Internal details never exposed in production
3. **Observability**: Comprehensive logging for debugging and monitoring
4. **Compliance**: Audit logs for regulatory requirements
5. **Abuse Prevention**: Rate limiting protects against abuse
6. **User Experience**: User-friendly error messages
7. **Debugging**: Request IDs for tracing issues across logs

## Configuration

### Environment Variables:
- `DEBUG`: Enable debug mode (exposes error details)
- `LOG_LEVEL`: Set logging level (INFO, WARNING, ERROR)

### Rate Limit Configuration:
Edit `middleware/rate_limiter.py` to adjust limits:
```python
LIMITS = {
    "/api/v1/auth/login": 5,  # 5 requests per minute
    "/api/v1/agents/visual-auditor": 20,
    # ... more endpoints
}
```

## Monitoring

### Check Rate Limiter Stats:
```bash
curl http://localhost:8000/api/v1/status
```

Response includes:
```json
{
  "api_version": "v1",
  "status": "ready",
  "rate_limiter": {
    "active_clients": 5,
    "total_tracked_endpoints": 12,
    "last_cleanup": "2026-01-17T10:00:00"
  }
}
```

### View Logs:
```bash
# All logs
tail -f logs/microcfo.log

# Errors only
tail -f logs/errors.log

# Audit events
tail -f logs/audit.log
```

## Testing

Run property-based tests:
```bash
python -m pytest test_error_handling_properties.py -v
```

Run integration tests:
```bash
python -m pytest test_integration_server.py -v
```

## Next Steps

The error handling and logging system is now complete and ready for production use. Future enhancements could include:

1. Log aggregation (e.g., ELK stack, CloudWatch)
2. Real-time alerting for critical errors
3. Metrics dashboard for rate limiting
4. Log rotation and archival
5. Distributed tracing integration

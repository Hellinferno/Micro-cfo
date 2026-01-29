#!/usr/bin/env python3
"""
Centralized Error Handler for MicroCFO Integration Server
Provides consistent error handling and user-friendly error messages

Requirements: 5.1, 5.3
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from src.mcp_bridge import MCPBridgeError

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standardized error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: str


class ErrorCategory:
    """Error category constants"""
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION = "authorization_error"
    VALIDATION = "validation_error"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit_exceeded"
    MCP_ERROR = "mcp_service_error"
    FILE_ERROR = "file_error"
    INTERNAL = "internal_server_error"


# User-friendly error message mappings
ERROR_MESSAGES = {
    # Authentication errors
    ErrorCategory.AUTHENTICATION: "Authentication failed. Please log in again.",
    
    # Authorization errors
    ErrorCategory.AUTHORIZATION: "You don't have permission to access this resource.",
    
    # Validation errors
    ErrorCategory.VALIDATION: "Invalid input data. Please check your request and try again.",
    
    # Not found errors
    ErrorCategory.NOT_FOUND: "The requested resource was not found.",
    
    # Rate limiting errors
    ErrorCategory.RATE_LIMIT: "Too many requests. Please try again later.",
    
    # MCP service errors
    ErrorCategory.MCP_ERROR: "Unable to process your request at this time. Please try again.",
    
    # File errors
    ErrorCategory.FILE_ERROR: "File processing failed. Please check the file format and try again.",
    
    # Internal errors
    ErrorCategory.INTERNAL: "An unexpected error occurred. Please try again later."
}


def create_error_response(
    error_category: str,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    request_id: Optional[str] = None,
    expose_details: bool = False
) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        error_category: Error category from ErrorCategory class
        message: Custom error message (uses default if None)
        details: Additional error details (only exposed in debug mode)
        status_code: HTTP status code
        request_id: Request ID for tracking
        expose_details: Whether to expose internal details (debug mode)
        
    Returns:
        JSONResponse with standardized error format
    """
    # Generate request ID if not provided
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Use default message if not provided
    if not message:
        message = ERROR_MESSAGES.get(error_category, ERROR_MESSAGES[ErrorCategory.INTERNAL])
    
    # Only include details if explicitly allowed (debug mode)
    response_details = details if expose_details else None
    
    error_response = ErrorResponse(
        error=error_category,
        message=message,
        details=response_details,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors with user-friendly messages
    
    Requirements: 5.1, 8.4
    """
    request_id = str(uuid.uuid4())
    
    # Extract validation errors
    validation_errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    # Log validation error
    logger.warning(
        f"Validation error {request_id}: {len(validation_errors)} field(s) failed validation",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": validation_errors
        }
    )
    
    # Check if we should expose details (debug mode)
    from config import config
    expose_details = config.server.debug
    
    return create_error_response(
        error_category=ErrorCategory.VALIDATION,
        message="Invalid input data. Please check the following fields and try again.",
        details={"validation_errors": validation_errors} if expose_details else None,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=request_id,
        expose_details=expose_details
    )


async def mcp_bridge_exception_handler(request: Request, exc: MCPBridgeError) -> JSONResponse:
    """
    Handle MCP Bridge errors with user-friendly messages
    
    Requirements: 5.1, 5.3
    """
    request_id = str(uuid.uuid4())
    
    # Log MCP error with full details
    logger.error(
        f"MCP Bridge error {request_id}: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": type(exc).__name__
        },
        exc_info=True
    )
    
    # Check if we should expose details (debug mode)
    from config import config
    expose_details = config.server.debug
    
    # Create user-friendly message
    user_message = "Unable to process your request at this time. Our team has been notified."
    
    return create_error_response(
        error_category=ErrorCategory.MCP_ERROR,
        message=user_message,
        details={"error_type": type(exc).__name__, "error": str(exc)} if expose_details else None,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        request_id=request_id,
        expose_details=expose_details
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions with user-friendly messages
    
    Requirements: 5.1, 5.3
    """
    request_id = str(uuid.uuid4())
    
    # Log full error details server-side
    logger.error(
        f"Unhandled exception {request_id}: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__
        },
        exc_info=True
    )
    
    # Check if we should expose details (debug mode)
    from config import config
    expose_details = config.server.debug
    
    return create_error_response(
        error_category=ErrorCategory.INTERNAL,
        message=ERROR_MESSAGES[ErrorCategory.INTERNAL],
        details={"error_type": type(exc).__name__, "error": str(exc)} if expose_details else None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
        expose_details=expose_details
    )


def register_error_handlers(app):
    """
    Register all error handlers with the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import HTTPException
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    # Register validation error handler
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # Register MCP Bridge error handler
    app.add_exception_handler(MCPBridgeError, mcp_bridge_exception_handler)
    
    # Register generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # HTTP exception handler (for FastAPI HTTPException)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        request_id = str(uuid.uuid4())
        
        # Map status codes to error categories
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error_category = ErrorCategory.AUTHENTICATION
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            error_category = ErrorCategory.AUTHORIZATION
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            error_category = ErrorCategory.NOT_FOUND
        elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_category = ErrorCategory.RATE_LIMIT
        elif exc.status_code >= 400 and exc.status_code < 500:
            error_category = ErrorCategory.VALIDATION
        else:
            error_category = ErrorCategory.INTERNAL
        
        # Log HTTP exception
        log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
        logger.log(
            log_level,
            f"HTTP exception {request_id}: {exc.status_code} - {exc.detail}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status_code": exc.status_code
            }
        )
        
        # Check if we should expose details
        from config import config
        expose_details = config.server.debug
        
        return create_error_response(
            error_category=error_category,
            message=exc.detail,
            status_code=exc.status_code,
            request_id=request_id,
            expose_details=expose_details
        )
    
    # Starlette HTTP exception handler (for middleware errors)
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        request_id = str(uuid.uuid4())
        
        # Map status codes to error categories
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error_category = ErrorCategory.AUTHENTICATION
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            error_category = ErrorCategory.AUTHORIZATION
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            error_category = ErrorCategory.NOT_FOUND
        else:
            error_category = ErrorCategory.INTERNAL
        
        logger.warning(
            f"Starlette HTTP exception {request_id}: {exc.status_code} - {exc.detail}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status_code": exc.status_code
            }
        )
        
        from config import config
        expose_details = config.server.debug
        
        return create_error_response(
            error_category=error_category,
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=request_id,
            expose_details=expose_details
        )
    
    logger.info("Error handlers registered successfully")

#!/usr/bin/env python3
"""
Comprehensive Logging Middleware for MicroCFO Integration Server
Provides request logging, audit logging, and structured logging

Requirements: 5.2, 5.5
"""

import logging
import time
import json
from datetime import datetime
from typing import Callable, Optional
from pathlib import Path

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Configure structured logging format
STRUCTURED_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra_data)s'


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON extra data"""
    
    def format(self, record):
        # Extract extra data
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'extra_data']:
                extra_data[key] = value
        
        # Add extra data to record
        record.extra_data = json.dumps(extra_data) if extra_data else '{}'
        
        return super().format(record)


def setup_logging(debug: bool = False):
    """
    Configure comprehensive logging system
    
    Args:
        debug: Whether to enable debug mode logging
        
    Requirements: 5.2, 5.5
    """
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with structured format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if debug else logging.WARNING)
    console_formatter = StructuredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    all_logs_file = LOGS_DIR / "microcfo.log"
    file_handler = logging.FileHandler(all_logs_file)
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    file_formatter = StructuredFormatter(STRUCTURED_LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error log file
    error_logs_file = LOGS_DIR / "errors.log"
    error_handler = logging.FileHandler(error_logs_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Audit log file for compliance operations
    audit_logs_file = LOGS_DIR / "audit.log"
    audit_handler = logging.FileHandler(audit_logs_file)
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(file_formatter)
    
    # Create audit logger
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_handler)
    audit_logger.propagate = False  # Don't propagate to root logger
    
    logging.info(f"✅ Logging system initialized - Debug mode: {debug}")
    logging.info(f"📁 Log files: {LOGS_DIR.absolute()}")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging
    
    Requirements: 5.2, 5.5
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("request")
        self.audit_logger = logging.getLogger("audit")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response with timing and user context
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from handler
        """
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID", f"req_{int(time.time() * 1000)}")
        
        # Extract user context
        user_context = getattr(request.state, "user", None)
        user_id = user_context.user_id if user_context else "anonymous"
        user_role = user_context.role if user_context else "none"
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        self.logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "user_id": user_id,
                "user_role": user_role,
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            self.logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                    "user_id": user_id
                }
            )
            
            # Audit log for compliance operations
            if self._is_compliance_operation(request.url.path):
                self.audit_logger.info(
                    f"Compliance operation: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "operation": request.url.path,
                        "user_id": user_id,
                        "user_role": user_role,
                        "status_code": response.status_code,
                        "timestamp": datetime.utcnow().isoformat(),
                        "client_ip": request.client.host if request.client else "unknown"
                    }
                )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            
            self.logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time": f"{process_time:.3f}s",
                    "user_id": user_id
                },
                exc_info=True
            )
            
            # Re-raise to be handled by error handlers
            raise
    
    def _is_compliance_operation(self, path: str) -> bool:
        """
        Check if the request path is a compliance-related operation
        
        Args:
            path: Request path
            
        Returns:
            True if compliance operation, False otherwise
        """
        compliance_paths = [
            "/api/v1/agents/legal-sentinel",
            "/api/v1/agents/visual-auditor",
            "/api/v1/auth"
        ]
        
        return any(path.startswith(cp) for cp in compliance_paths)


def log_audit_event(
    event_type: str,
    user_id: str,
    details: dict,
    status: str = "success"
):
    """
    Log an audit event for compliance tracking
    
    Args:
        event_type: Type of event (e.g., "login", "document_scan", "compliance_check")
        user_id: User ID performing the action
        details: Additional event details
        status: Event status (success, failure, etc.)
        
    Requirements: 5.5
    """
    audit_logger = logging.getLogger("audit")
    
    audit_logger.info(
        f"Audit event: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            **details
        }
    )


def log_security_event(
    event_type: str,
    user_id: Optional[str],
    details: dict,
    severity: str = "warning"
):
    """
    Log a security-related event
    
    Args:
        event_type: Type of security event
        user_id: User ID if available
        details: Event details
        severity: Severity level (info, warning, error, critical)
        
    Requirements: 5.5
    """
    security_logger = logging.getLogger("security")
    
    log_method = getattr(security_logger, severity.lower(), security_logger.warning)
    
    log_method(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id or "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            **details
        }
    )

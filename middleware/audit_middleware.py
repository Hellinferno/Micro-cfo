#!/usr/bin/env python3
"""
Audit Middleware for MicroCFO
Automatically logs all API requests with user context
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from audit_logger import AuditLogger, AuditAction, AuditSeverity

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically logs all API requests
    
    Captures:
    - Who: User ID from authentication
    - What: HTTP method and endpoint
    - When: Timestamp (automatic)
    - Where: IP address and user agent
    - How: Request/response details
    """
    
    # Endpoints that should be audited
    AUDITED_ENDPOINTS = {
        # Invoice endpoints
        '/api/v1/agents/visual-auditor/upload-document': AuditAction.INVOICE_UPLOADED,
        '/api/v1/agents/visual-auditor/scan-invoice': AuditAction.INVOICE_VIEWED,
        
        # Legal endpoints
        '/api/v1/agents/legal-sentinel/search': AuditAction.LEGAL_QUERY,
        '/api/v1/agents/legal-sentinel/assess-risk': AuditAction.LEGAL_RISK_ASSESSED,
        
        # Subsidy endpoints
        '/api/v1/agents/subsidy-hunter/search': AuditAction.SUBSIDY_SEARCHED,
        '/api/v1/agents/subsidy-hunter/find-for-invoice': AuditAction.SUBSIDY_SEARCHED,
        
        # Negotiation endpoints
        '/api/v1/agents/negotiator/generate-email': AuditAction.NEGOTIATION_EMAIL_GENERATED,
        
        # Auth endpoints
        '/api/v1/auth/login': AuditAction.LOGIN,
        '/api/v1/auth/logout': AuditAction.LOGOUT,
        '/api/v1/auth/register': AuditAction.USER_CREATED,
    }
    
    # Endpoints to skip (health checks, static files, etc.)
    SKIP_ENDPOINTS = {
        '/health',
        '/docs',
        '/redoc',
        '/openapi.json',
        '/favicon.ico',
    }
    
    def __init__(self, app: ASGIApp, enabled: bool = True):
        """
        Initialize audit middleware
        
        Args:
            app: ASGI application
            enabled: Whether auditing is enabled
        """
        super().__init__(app)
        self.enabled = enabled
        if enabled:
            logger.info("✅ Audit middleware enabled")
        else:
            logger.warning("⚠️  Audit middleware disabled")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log audit trail
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from handler
        """
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip certain endpoints
        if self._should_skip(request):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract request context
        user_context = self._extract_user_context(request)
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', 'Unknown')
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log audit trail (async, don't block response)
        try:
            self._log_request(
                request=request,
                response=response,
                user_context=user_context,
                ip_address=ip_address,
                user_agent=user_agent,
                duration=duration
            )
        except Exception as e:
            logger.error(f"Failed to log audit trail: {e}", exc_info=True)
        
        return response
    
    def _should_skip(self, request: Request) -> bool:
        """Check if endpoint should be skipped"""
        path = request.url.path
        
        # Skip health checks and static files
        for skip_path in self.SKIP_ENDPOINTS:
            if path.startswith(skip_path):
                return True
        
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return True
        
        return False
    
    def _extract_user_context(self, request: Request) -> dict:
        """
        Extract user context from request
        
        Returns:
            Dictionary with user_id and user_email
        """
        user_context = {
            'user_id': None,
            'user_email': None
        }
        
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, 'user'):
            user = request.state.user
            user_context['user_id'] = str(user.user_id) if hasattr(user, 'user_id') else None
            user_context['user_email'] = user.email if hasattr(user, 'email') else None
        
        return user_context
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request
        
        Checks X-Forwarded-For header first (for proxies/load balancers)
        Falls back to direct client IP
        
        Returns:
            IP address string
        """
        # Check X-Forwarded-For header (proxy/load balancer)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            # Take first IP if multiple
            return forwarded_for.split(',')[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return 'Unknown'
    
    def _log_request(
        self,
        request: Request,
        response: Response,
        user_context: dict,
        ip_address: str,
        user_agent: str,
        duration: float
    ):
        """
        Log request to audit trail
        
        Args:
            request: Request object
            response: Response object
            user_context: User context dictionary
            ip_address: Client IP address
            user_agent: User agent string
            duration: Request duration in seconds
        """
        path = request.url.path
        method = request.method
        status_code = response.status_code
        
        # Determine action type
        action = self._determine_action(path, method)
        
        # Determine severity based on status code
        severity = self._determine_severity(status_code)
        
        # Build details
        details = {
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'query_params': dict(request.query_params) if request.query_params else None,
        }
        
        # Add error details for failed requests
        if status_code >= 400:
            details['error'] = True
            if status_code == 401:
                details['error_type'] = 'Unauthorized'
            elif status_code == 403:
                details['error_type'] = 'Forbidden'
            elif status_code == 404:
                details['error_type'] = 'Not Found'
            elif status_code >= 500:
                details['error_type'] = 'Server Error'
        
        # Log to audit trail
        AuditLogger.log(
            action=action,
            user_id=user_context['user_id'],
            user_email=user_context['user_email'],
            resource_type='api_request',
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity
        )
    
    def _determine_action(self, path: str, method: str) -> AuditAction:
        """
        Determine audit action type from path and method
        
        Args:
            path: Request path
            method: HTTP method
            
        Returns:
            AuditAction enum value
        """
        # Check for exact match
        if path in self.AUDITED_ENDPOINTS:
            return self.AUDITED_ENDPOINTS[path]
        
        # Check for pattern matches
        if '/invoice' in path:
            if method == 'POST':
                return AuditAction.INVOICE_UPLOADED
            elif method == 'GET':
                return AuditAction.INVOICE_VIEWED
            elif method == 'PUT' or method == 'PATCH':
                return AuditAction.INVOICE_UPDATED
            elif method == 'DELETE':
                return AuditAction.INVOICE_DELETED
        
        elif '/legal' in path:
            return AuditAction.LEGAL_QUERY
        
        elif '/subsidy' in path:
            return AuditAction.SUBSIDY_SEARCHED
        
        elif '/negotiat' in path:
            return AuditAction.NEGOTIATION_EMAIL_GENERATED
        
        elif '/auth/login' in path:
            return AuditAction.LOGIN
        
        elif '/auth/logout' in path:
            return AuditAction.LOGOUT
        
        # Default: generic API access
        return AuditAction.INVOICE_VIEWED  # Generic read action
    
    def _determine_severity(self, status_code: int) -> AuditSeverity:
        """
        Determine severity based on HTTP status code
        
        Args:
            status_code: HTTP status code
            
        Returns:
            AuditSeverity enum value
        """
        if status_code >= 500:
            return AuditSeverity.ERROR
        elif status_code == 401 or status_code == 403:
            return AuditSeverity.WARNING
        elif status_code >= 400:
            return AuditSeverity.WARNING
        else:
            return AuditSeverity.INFO


def get_audit_middleware(enabled: bool = True) -> AuditMiddleware:
    """
    Factory function to create audit middleware
    
    Args:
        enabled: Whether auditing is enabled
        
    Returns:
        AuditMiddleware instance
    """
    return lambda app: AuditMiddleware(app, enabled=enabled)

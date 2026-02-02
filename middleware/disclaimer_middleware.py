#!/usr/bin/env python3
"""
Disclaimer Middleware for MicroCFO
Automatically appends legal disclaimers to API responses
"""

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json

from src.legal_disclaimers import LegalDisclaimers, DisclaimerType

logger = logging.getLogger(__name__)


class DisclaimerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically append disclaimers to API responses
    
    This middleware adds appropriate disclaimers based on the endpoint being called.
    """
    
    # Map endpoints to disclaimer types
    ENDPOINT_DISCLAIMERS = {
        "/agents/negotiator": DisclaimerType.NEGOTIATION,
        "/agents/visual-auditor": DisclaimerType.INVOICE_PROCESSING,
        "/agents/legal-sentinel": DisclaimerType.LEGAL_ADVICE,
        "/agents/subsidy-hunter": DisclaimerType.SUBSIDY_APPLICATION,
    }
    
    def __init__(self, app, enabled: bool = True):
        """
        Initialize disclaimer middleware
        
        Args:
            app: FastAPI application
            enabled: Whether middleware is enabled
        """
        super().__init__(app)
        self.enabled = enabled
        logger.info(f"DisclaimerMiddleware initialized (enabled={enabled})")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add disclaimer to response if applicable
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with disclaimer added if applicable
        """
        if not self.enabled:
            return await call_next(request)
        
        # Get response from next handler
        response = await call_next(request)
        
        # Only add disclaimers to JSON responses from agent endpoints
        if (
            response.status_code == 200 and
            response.headers.get("content-type", "").startswith("application/json") and
            "/agents/" in request.url.path
        ):
            try:
                # Determine disclaimer type based on endpoint
                disclaimer_type = self._get_disclaimer_type(request.url.path)
                
                if disclaimer_type:
                    # Read response body
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                    
                    # Parse JSON
                    data = json.loads(body.decode())
                    
                    # Add disclaimer if not already present
                    if "disclaimer" not in data:
                        disclaimer_data = LegalDisclaimers.format_for_api_response(disclaimer_type)
                        data["disclaimer_info"] = disclaimer_data
                        
                        logger.debug(
                            f"Added {disclaimer_type.value} disclaimer to response for {request.url.path}"
                        )
                    
                    # Create new response with disclaimer
                    return JSONResponse(
                        content=data,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
            except Exception as e:
                logger.error(f"Error adding disclaimer to response: {str(e)}")
                # Return original response if error occurs
                pass
        
        return response
    
    def _get_disclaimer_type(self, path: str) -> DisclaimerType:
        """
        Determine disclaimer type based on endpoint path
        
        Args:
            path: Request path
            
        Returns:
            Disclaimer type or None
        """
        for endpoint_prefix, disclaimer_type in self.ENDPOINT_DISCLAIMERS.items():
            if path.startswith(endpoint_prefix):
                return disclaimer_type
        
        return None

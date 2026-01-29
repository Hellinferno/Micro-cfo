import re
import json
from typing import Any, Union, Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, StreamingResponse
import logging

logger = logging.getLogger(__name__)

# Compile regex patterns for common PII
PATTERNS = {
    'PAN': re.compile(r'[A-Z]{5}[0-9]{4}[A-Z]{1}'),
    'AADHAAR': re.compile(r'\b\d{4}\s\d{4}\s\d{4}\b'),
    'PHONE': re.compile(r'\b(\+91[\-\s]?)?[6789]\d{9}\b'),
    'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'CREDIT_CARD': re.compile(r'\b(?:\d[ -]*?){13,16}\b')
}

class PIIRedactionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redact sensitive PII data from API responses.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only process JSON responses
        if response.headers.get("content-type") == "application/json":
            # Consume the response body
            response_body = [section async for section in response.body_iterator]
            response.body_iterator = iter(response_body)
            body_text = b"".join(response_body).decode()

            try:
                data = json.loads(body_text)
                redacted_data = self.redact_data(data)
                
                # Create a new JSONResponse
                return JSONResponse(
                    content=redacted_data,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            except json.JSONDecodeError:
                # Not valid JSON, return original
                pass

        return response

    def redact_data(self, data: Any) -> Any:
        """
        Recursively redact PII from data.
        """
        if isinstance(data, dict):
            return {k: self.redact_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.redact_data(item) for item in data]
        elif isinstance(data, str):
            # Apply all regex patterns
            redacted = data
            for name, pattern in PATTERNS.items():
                if name == 'EMAIL': # Partial redaction for email
                     redacted = pattern.sub(lambda m: self._partial_mask_email(m.group(0)), redacted)
                elif name == 'CREDIT_CARD':
                     redacted = pattern.sub("****-****-****-****", redacted)
                else:
                     redacted = pattern.sub(f"[{name}_REDACTED]", redacted)
            return redacted
        else:
            return data

    def _partial_mask_email(self, email: str) -> str:
        try:
            user, domain = email.split('@')
            if len(user) > 2:
                masked_user = user[:2] + '*' * (len(user) - 2)
            else:
                masked_user = user # Too short to mask safely
            return f"{masked_user}@{domain}"
        except:
            return email

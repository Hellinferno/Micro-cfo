"""
Cost tracking middleware for LLM usage
Tracks token usage and stores per-request costs in the database
"""

import logging
import time
from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from database import SessionLocal
from models import UsageLog

logger = logging.getLogger(__name__)

# Context variable to store usage per request
request_cost_context: ContextVar[dict] = ContextVar(
    "request_cost",
    default={"input_tokens": 0, "output_tokens": 0, "model_used": None, "metadata": {}}
)

# Pricing table (per 1K tokens in USD)
PRICING_TABLE = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
    "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
}


class CostTrackerMiddleware(BaseHTTPMiddleware):
    """Tracks LLM token usage and logs per-request costs"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        token_usage = {"input_tokens": 0, "output_tokens": 0, "model_used": None, "metadata": {}}
        token = request_cost_context.set(token_usage)

        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            process_time = time.time() - start_time
            usage_data = request_cost_context.get()
            total_cost = self._calculate_cost(usage_data)

            try:
                user_id = getattr(getattr(request, "state", None), "user", None)
                user_id = getattr(user_id, "user_id", None)

                self._persist_usage(
                    user_id=user_id,
                    route=request.url.path,
                    method=request.method,
                    status_code=getattr(response, "status_code", None),
                    model_used=usage_data.get("model_used"),
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0),
                    total_cost=total_cost,
                    duration_ms=process_time * 1000,
                    request_id=request.headers.get("X-Request-ID"),
                    metadata=usage_data.get("metadata") or {},
                )

                if response is not None:
                    response.headers["X-Request-Cost"] = str(total_cost)
                    response.headers["X-Process-Time"] = f"{process_time:.3f}"

            except Exception as exc:
                logger.warning("Failed to persist usage log: %s", exc)
            finally:
                request_cost_context.reset(token)

    def _calculate_cost(self, usage: dict) -> float:
        model = usage.get("model_used")
        if not model or model not in PRICING_TABLE:
            return 0.0

        in_cost = (usage.get("input_tokens", 0) / 1000) * PRICING_TABLE[model]["input"]
        out_cost = (usage.get("output_tokens", 0) / 1000) * PRICING_TABLE[model]["output"]
        return round(in_cost + out_cost, 6)

    def _persist_usage(
        self,
        user_id: Optional[str],
        route: str,
        method: str,
        status_code: Optional[int],
        model_used: Optional[str],
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        duration_ms: float,
        request_id: Optional[str],
        metadata: dict,
    ) -> None:
        db = SessionLocal()
        try:
            usage_log = UsageLog(
                user_id=user_id,
                route=route,
                method=method,
                status_code=status_code,
                model_used=model_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_cost_usd=total_cost,
                duration_ms=duration_ms,
                request_id=request_id,
                meta_info=metadata,  # Column renamed from 'metadata'
            )
            db.add(usage_log)
            db.commit()
        finally:
            db.close()


def track_usage(model: str, input_tokens: int, output_tokens: int, metadata: Optional[dict] = None) -> None:
    """Helper to be called inside services to accumulate token usage"""
    current_usage = request_cost_context.get()
    current_usage["input_tokens"] = current_usage.get("input_tokens", 0) + input_tokens
    current_usage["output_tokens"] = current_usage.get("output_tokens", 0) + output_tokens
    current_usage["model_used"] = model

    if metadata:
        current_usage.setdefault("metadata", {}).update(metadata)

    request_cost_context.set(current_usage)

"""
MicroCFO - Main FastAPI Application Entry Point
AI-powered financial compliance platform for Indian MSMEs
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import time
from structlog import get_logger
from datetime import datetime, timezone

from backend.app.config import settings

# Lazy import routes to avoid circular dependencies
def get_api_router():
    """Lazy import of API router to prevent circular imports"""
    from backend.api.v1.routes import router as api_v1_router
    return api_v1_router

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered financial compliance platform for Indian MSMEs",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize rate limiter
app.state.limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://"
)
app.add_event_handler("startup", app.state.limiter.slowapi_startup)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        "HTTP exception",
        path=str(request.url.path),
        status_code=exc.status_code,
        detail=exc.detail
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error": f"HTTP_{exc.status_code}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(
        "Validation exception",
        path=str(request.url.path),
        errors=exc.errors()
    )
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "Validation error",
            "error": "VALIDATION_ERROR",
            "details": exc.errors(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions"""
    logger.error(
        "Unhandled exception",
        path=str(request.url.path),
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": "INTERNAL_ERROR",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms
    )

    return response


# Include API Routes (lazy import to avoid circular dependencies)
app.include_router(get_api_router(), prefix=settings.API_V1_PREFIX)


# Root Endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "success": True,
        "data": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": "AI-powered financial compliance platform for Indian MSMEs",
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/api/v1/health",
                "api_v1": settings.API_V1_PREFIX
            }
        }
    }


# Health Check (legacy endpoint for backward compatibility)
@app.get("/health")
async def health_check():
    """Legacy health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Startup Event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(
        "MicroCFO starting up",
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        environment="development" if settings.DEBUG else "production"
    )
    
    # Initialize database
    try:
        from src.database import init_db
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
    
    # Initialize agents
    try:
        from backend.agents import initialize_agents
        initialize_agents()
        logger.info("Agents initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize agents", error=str(e), exc_info=True)
        if not settings.DEBUG:
            raise  # Fail fast in production


# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("MicroCFO shutting down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

#!/usr/bin/env python3
"""
FastAPI Integration Server for MicroCFO
Bridges React frontend with MCP server backend
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from config import config
from mcp_bridge import MCPBridge, MCPBridgeError

# Configure comprehensive logging system
from middleware.logging_middleware import setup_logging
setup_logging(debug=config.server.debug)
logger = logging.getLogger(__name__)

# Health check response model
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    environment: str

# Error response model
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str
    request_id: Optional[str] = None

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    logger.info("🚀 Starting MicroCFO Integration Server")
    logger.info(f"📡 CORS enabled for origins: {config.cors.allowed_origins}")
    logger.info(f"🔧 Debug mode: {config.server.debug}")
    logger.info(f"🌐 Server will run on {config.server.host}:{config.server.port}")
    
    # Initialize MCP bridge
    mcp_bridge = MCPBridge()
    app.state.mcp_bridge = mcp_bridge
    logger.info("✅ MCP Bridge initialized successfully")
    
    # Initialize Legal Sentinel with WebSocket manager
    from websocket_manager import websocket_manager
    from sentinel_monitor import LegalSentinel
    from operation_tracker import operation_tracker
    
    # Set WebSocket manager for operation tracker
    operation_tracker.websocket_manager = websocket_manager
    
    sentinel = LegalSentinel(websocket_manager=websocket_manager)
    app.state.sentinel = sentinel
    logger.info("✅ Legal Sentinel initialized with WebSocket support")
    logger.info("✅ Operation Tracker initialized with WebSocket support")
    
    # Start WebSocket heartbeat checker
    from websocket_manager import websocket_manager
    import asyncio
    
    async def heartbeat_checker():
        """Background task to check for stale WebSocket connections"""
        while True:
            await asyncio.sleep(60)  # Check every minute
            await websocket_manager.check_stale_connections()
    
    async def operation_cleanup():
        """Background task to cleanup old completed operations"""
        while True:
            await asyncio.sleep(3600)  # Check every hour
            operation_tracker.cleanup_completed_operations(max_age_hours=24)
    
    heartbeat_task = asyncio.create_task(heartbeat_checker())
    cleanup_task = asyncio.create_task(operation_cleanup())
    logger.info("✅ WebSocket heartbeat checker started")
    logger.info("✅ Operation cleanup task started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down MicroCFO Integration Server")
    
    # Cancel background tasks
    heartbeat_task.cancel()
    cleanup_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# Create FastAPI application
app = FastAPI(
    title=config.api.title,
    description=config.api.description,
    version=config.api.version,
    docs_url="/docs" if config.server.debug else None,
    redoc_url="/redoc" if config.server.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allowed_origins,
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
    expose_headers=["*"]
)

# Add authentication middleware
from middleware.auth import AuthenticationMiddleware
app.add_middleware(AuthenticationMiddleware)

# Add authorization middleware
from middleware.authorization import AuthorizationMiddleware
app.add_middleware(AuthorizationMiddleware)

# Add rate limiting middleware
from middleware.rate_limiter import RateLimitMiddleware
import os
# Disable rate limiting in test environment
rate_limit_enabled = os.getenv("TESTING") != "true"
app.add_middleware(RateLimitMiddleware, enabled=rate_limit_enabled)

# Add request logging middleware
from middleware.logging_middleware import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)

# Add audit middleware for comprehensive audit trails
from middleware.audit_middleware import AuditMiddleware
audit_enabled = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
app.add_middleware(AuditMiddleware, enabled=audit_enabled)
if audit_enabled:
    logger.info("✅ Audit middleware enabled - all actions will be logged")
else:
    logger.warning("⚠️  Audit middleware disabled")

# Add disclaimer middleware for legal disclaimers
from middleware.disclaimer_middleware import DisclaimerMiddleware
disclaimer_enabled = os.getenv("DISCLAIMER_ENABLED", "true").lower() == "true"
app.add_middleware(DisclaimerMiddleware, enabled=disclaimer_enabled)
if disclaimer_enabled:
    logger.info("✅ Disclaimer middleware enabled - legal disclaimers will be added to responses")
else:
    logger.warning("⚠️  Disclaimer middleware disabled")

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.security.trusted_hosts
)

# Register centralized error handlers
from middleware.error_handler import register_error_handlers
register_error_handlers(app)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    
    Returns:
        HealthResponse: Current system status and information
    """
    return HealthResponse(
        status="healthy",
        message="MicroCFO Integration Server is running",
        version=config.api.version,
        environment="development" if config.server.debug else "production"
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "name": config.api.title,
        "version": config.api.version,
        "status": "running",
        "docs_url": "/docs" if config.server.debug else "disabled",
        "health_url": "/health"
    }

# API v1 router and agent routers
from fastapi import APIRouter
from routers.visual_auditor import router as visual_auditor_router
from routers.legal_sentinel import router as legal_sentinel_router
from routers.subsidy_hunter import router as subsidy_hunter_router
from routers.negotiator import router as negotiator_router
from routers.auth import router as auth_router
from routers.websocket import router as websocket_router
from routers.tasks import router as tasks_router
from routers.audit import router as audit_router
from routers.erp_export import router as erp_export_router
from routers.onboarding import router as onboarding_router

api_v1_router = APIRouter(prefix=config.api.v1_prefix)

# Include agent routers
api_v1_router.include_router(visual_auditor_router)
api_v1_router.include_router(legal_sentinel_router)
api_v1_router.include_router(subsidy_hunter_router)
api_v1_router.include_router(negotiator_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(erp_export_router)
api_v1_router.include_router(onboarding_router)

# Include WebSocket router (not under api_v1 prefix for cleaner URLs)
app.include_router(websocket_router)

@api_v1_router.get("/status")
async def api_status():
    """API v1 status endpoint"""
    from middleware.rate_limiter import get_rate_limiter_stats
    from cache_manager import cache_manager
    from connection_pool import connection_pool, resource_queue
    
    return {
        "api_version": "v1",
        "status": "ready",
        "message": "MCP Bridge is initialized and ready for agent calls",
        "rate_limiter": get_rate_limiter_stats(),
        "cache": cache_manager.get_stats(),
        "connection_pool": connection_pool.get_stats(),
        "resource_queue": resource_queue.get_stats()
    }

@api_v1_router.get("/mcp/test")
async def test_mcp_bridge(request):
    """Test MCP bridge connectivity"""
    try:
        mcp_bridge = request.app.state.mcp_bridge
        
        # Test getting user profile
        profile_result = await mcp_bridge.get_user_profile()
        
        return {
            "status": "success",
            "message": "MCP Bridge is working correctly",
            "test_result": profile_result
        }
    except Exception as e:
        logger.error(f"MCP Bridge test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP Bridge test failed: {str(e)}"
        )

# Include the API router
app.include_router(api_v1_router)

# Development server runner
def run_dev_server():
    """Run development server with hot reload"""
    uvicorn.run(
        "integration_server:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload or config.server.debug,
        log_level="info" if config.server.debug else "warning",
        timeout_keep_alive=config.server.keepalive_timeout
    )

if __name__ == "__main__":
    run_dev_server()
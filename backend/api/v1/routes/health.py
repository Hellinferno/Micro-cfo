"""
Health Check API
System health monitoring and status
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add project root to path
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from backend.app.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    app: str
    version: str
    timestamp: str
    environment: str
    database: Optional[str] = None
    ai_services: Optional[str] = None


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@router.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Comprehensive health check endpoint
    
    Returns system status including:
    - Application status
    - Database connectivity
    - AI service availability
    - Environment information
    """
    health_status = {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "development" if settings.DEBUG else "production"
    }
    
    # Check database connection
    try:
        from src.database import check_db_connection
        db_status = check_db_connection()
        health_status["database"] = "connected" if db_status else "disconnected"
        if not db_status:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check AI services
    try:
        ai_available = bool(settings.GEMINI_API_KEY or settings.OPENROUTER_API_KEY)
        health_status["ai_services"] = "available" if ai_available else "not_configured"
    except Exception:
        health_status["ai_services"] = "unknown"
    
    return HealthResponse(**health_status)


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/load balancers
    
    Returns 200 only if all critical services are healthy
    """
    try:
        # Check database
        from src.database import check_db_connection
        if not check_db_connection():
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "Database connection failed"}
            )
        
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": str(e)}
        )


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes
    
    Returns 200 if the application is running
    """
    return {"status": "alive"}

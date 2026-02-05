#!/usr/bin/env python3
"""
Admin Router for MicroCFO
Handles user management, system monitoring, and SaaS administration.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, timedelta

from database import get_db
from models import User, UserProfile, Invoice, AuditLog
# Corrected import for get_current_user
from middleware.auth import get_current_user
from auth import UserContext 

router = APIRouter(prefix="/api/v1/admin", tags=["Super Admin"])

# --- Response Models ---
class AdminUserList(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    business_sector: Optional[str]
    created_at: datetime
    is_active: bool
    is_verified: bool
    invoice_count: int

class SystemOverview(BaseModel):
    total_users: int
    active_users_24h: int
    total_invoices_processed: int
    total_api_calls_24h: int
    system_health: str

# --- Dependency ---
def require_super_admin(user: UserContext = Depends(get_current_user)):
    """
    Hard-coded security check for the Super Admin.
    In production, use a proper Role enum like UserRole.SYSTEM_ADMIN.
    For now, we protect it by email or a specific DB flag.
    """
    # Allowed admin accounts
    ALLOWED_ADMINS = [
        "admin@microcfo.com", 
        "hellinferno@microcfo.com",
        "superadmin@microcfo.com"
    ]
    
    # Also allow by username
    ALLOWED_USERNAMES = ["hellinferno", "admin", "superadmin"]
    
    if user.email not in ALLOWED_ADMINS and getattr(user, 'username', None) not in ALLOWED_USERNAMES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin privileges required"
        )
    return user

# --- Endpoints ---

@router.get("/overview", response_model=SystemOverview)
def get_system_overview(
    db: Session = Depends(get_db),
    admin: UserContext = Depends(require_super_admin)
):
    """Get high-level SaaS metrics"""
    
    # 1. Total Users
    total_users = db.query(User).count()
    
    # 2. Active Users (logged in/active in last 24h)
    yesterday = datetime.utcnow() - timedelta(days=1)
    # We approximate this using audit logs or updated_at if login tracks it
    active_users = db.query(AuditLog.user_id).filter(
        AuditLog.created_at >= yesterday
    ).distinct().count()
    
    # 3. Total Invoices
    total_invoices = db.query(Invoice).count()
    
    # 4. API Usage (Audit logs count for 24h)
    api_calls = db.query(AuditLog).filter(
        AuditLog.created_at >= yesterday
    ).count()

    return SystemOverview(
        total_users=total_users,
        active_users_24h=active_users,
        total_invoices_processed=total_invoices,
        total_api_calls_24h=api_calls,
        system_health="OPERATIONAL" # You can add real health checks here
    )

@router.get("/users", response_model=List[AdminUserList])
def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: UserContext = Depends(require_super_admin)
):
    """List all SaaS users with pagination and search"""
    query = db.query(User)
    
    if search:
        query = query.filter(User.email.ilike(f"%{search}%") | User.company_name.ilike(f"%{search}%"))
    
    users = query.offset(skip).limit(limit).all()
    
    result = []
    for u in users:
        # Count invoices per user efficiently
        inv_count = db.query(Invoice).filter(Invoice.user_id == u.id).count()
        
        result.append(AdminUserList(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            company_name=u.company_name,
            business_sector=u.business_sector,
            created_at=u.created_at,
            is_active=u.is_active,
            is_verified=u.is_verified,
            invoice_count=inv_count
        ))
    return result

@router.patch("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: str,
    db: Session = Depends(get_db),
    admin: UserContext = Depends(require_super_admin)
):
    """Ban or Unban a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent banning yourself
    if user.email == admin.email:
         raise HTTPException(status_code=400, detail="Cannot ban self")

    user.is_active = not user.is_active
    db.commit()
    
    action = "activated" if user.is_active else "deactivated"
    return {"message": f"User {user.email} has been {action}"}


# --- ETL & System Management Endpoints ---

@router.get("/etl/status")
async def get_etl_status(admin: UserContext = Depends(require_super_admin)):
    """Get ETL scheduler status and job history"""
    try:
        from src.etl_jobs import etl_scheduler
        
        return {
            "running": etl_scheduler._running,
            "job_history": etl_scheduler.get_job_history(limit=20),
            "last_check": etl_scheduler._last_check_time.isoformat() if hasattr(etl_scheduler, '_last_check_time') and etl_scheduler._last_check_time else None
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/etl/start")
async def start_etl_scheduler(admin: UserContext = Depends(require_super_admin)):
    """Start the ETL scheduler"""
    try:
        from src.etl_jobs import etl_scheduler
        etl_scheduler.start()
        return {"message": "ETL scheduler started", "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/etl/stop")
async def stop_etl_scheduler(admin: UserContext = Depends(require_super_admin)):
    """Stop the ETL scheduler"""
    try:
        from src.etl_jobs import etl_scheduler
        etl_scheduler.stop()
        return {"message": "ETL scheduler stopped", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/etl/run-job/{job_name}")
async def run_etl_job(
    job_name: str,
    admin: UserContext = Depends(require_super_admin)
):
    """Manually run a specific ETL job"""
    valid_jobs = ["scrape_subsidies", "scrape_legislative", "update_compliance", "cash_flow_predictions"]
    
    if job_name not in valid_jobs:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid job name. Valid jobs: {valid_jobs}"
        )
    
    try:
        from src.etl_jobs import etl_scheduler
        result = await etl_scheduler.run_job_manually(job_name)
        
        return {
            "job_name": result.job_name,
            "status": result.status.value,
            "records_processed": result.records_processed,
            "errors": result.errors,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/status")
async def get_llm_status(admin: UserContext = Depends(require_super_admin)):
    """Get LLM service status and statistics"""
    try:
        from src.llm_service import llm_service
        
        return {
            "available_providers": [p.value for p in llm_service.get_available_providers()],
            "statistics": llm_service.get_statistics()
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/llm/health")
async def check_llm_health(admin: UserContext = Depends(require_super_admin)):
    """Check health of all LLM providers"""
    try:
        from src.llm_service import llm_service
        health = await llm_service.health_check()
        return health
    except Exception as e:
        return {"error": str(e)}


@router.get("/cache/stats")
async def get_cache_stats(admin: UserContext = Depends(require_super_admin)):
    """Get cache statistics"""
    try:
        from src.redis_cache import cache_service
        return cache_service.stats()
    except Exception as e:
        return {"error": str(e)}


@router.post("/cache/clear")
async def clear_cache(
    namespace: Optional[str] = None,
    admin: UserContext = Depends(require_super_admin)
):
    """Clear cache (optionally by namespace)"""
    try:
        from src.redis_cache import cache_service
        
        if namespace:
            count = cache_service.invalidate_namespace(namespace)
            return {"message": f"Cleared {count} entries from namespace {namespace}"}
        else:
            result = cache_service.clear_all()
            return {"message": "Cache cleared", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/status")
async def get_config_status(admin: UserContext = Depends(require_super_admin)):
    """Get configuration and service status"""
    try:
        from src.config import config
        
        return {
            "llm_providers": config.get_llm_providers_status(),
            "services": config.get_services_status(),
            "features": {
                "agent_a": config.features.enable_agent_a,
                "agent_b": config.features.enable_agent_b,
                "agent_c": config.features.enable_agent_c,
                "agent_d": config.features.enable_agent_d,
                "telegram": config.features.enable_telegram,
                "account_aggregator": config.features.enable_account_aggregator,
                "etl_scheduler": config.features.enable_etl_scheduler
            },
            "server": {
                "debug": config.server.debug,
                "port": config.server.port
            }
        }
    except Exception as e:
        return {"error": str(e)}


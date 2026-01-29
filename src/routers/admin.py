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

from src.database import get_db
from src.models import User, UserProfile, Invoice, AuditLog
# Corrected import for get_current_user
from src.middleware.auth import get_current_user
from src.auth import UserContext 

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
    # REPLACE WITH YOUR ADMIN EMAIL for immediate safety
    ALLOWED_ADMINS = ["admin@microcfo.com", "your_email@example.com", "owner@example.com"] # Added owner@example.com for easier testing if needed
    
    if user.email not in ALLOWED_ADMINS:
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

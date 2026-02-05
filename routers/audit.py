#!/usr/bin/env python3
"""
Audit Trail API Router for MicroCFO
Provides endpoints for querying and exporting audit logs
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Request, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from src.database import get_db
from src.models import AuditLog, User
from audit_logger import AuditAction, AuditSeverity

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/audit", tags=["Audit Trail"])


# Response Models
class AuditLogResponse(BaseModel):
    """Response model for audit log entry"""
    id: str
    user_id: Optional[str]
    user_email: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: str
    severity: Optional[str] = "info"


class AuditLogListResponse(BaseModel):
    """Response model for list of audit logs"""
    total: int
    page: int
    page_size: int
    logs: List[AuditLogResponse]


class AuditStatsResponse(BaseModel):
    """Response model for audit statistics"""
    total_events: int
    unique_users: int
    actions_by_type: dict
    events_by_day: dict
    top_users: List[dict]
    recent_security_events: List[dict]


class UserActivityResponse(BaseModel):
    """Response model for user activity"""
    user_id: str
    user_email: Optional[str]
    total_actions: int
    recent_actions: List[AuditLogResponse]
    actions_by_type: dict


class ResourceHistoryResponse(BaseModel):
    """Response model for resource history"""
    resource_type: str
    resource_id: str
    total_events: int
    history: List[AuditLogResponse]


# Helper Functions
def get_current_user(request: Request):
    """Get current user from request state"""
    if hasattr(request.state, 'user'):
        return request.state.user
    return None


def check_admin_permission(request: Request):
    """Check if user has admin permission to view audit logs"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Role-based access control for audit logs
    # Admins can view all logs, regular users can only view their own
    # User roles: 'admin', 'owner', 'accountant', 'viewer'
    admin_roles = {'admin', 'owner'}
    user_role = getattr(user, 'role', 'viewer')
    is_admin = user_role in admin_roles
    
    return user, is_admin


# Endpoints
@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with filtering and pagination
    
    Requires authentication. Users can view their own logs,
    admins can view all logs.
    """
    try:
        # Check authentication
        current_user = check_admin_permission(request)
        
        # Build query
        query = db.query(AuditLog)
        
        # Apply filters
        filters = []
        
        # Non-admin users can only see their own logs
        if not getattr(current_user, 'is_admin', False):
            filters.append(AuditLog.user_id == str(current_user.user_id))
        elif user_id:
            filters.append(AuditLog.user_id == user_id)
        
        if action:
            filters.append(AuditLog.action == action)
        
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        
        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            filters.append(AuditLog.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            filters.append(AuditLog.created_at <= end_dt)
        
        if severity:
            # Filter by severity in details JSON
            filters.append(AuditLog.details['severity'].astext == severity)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Format response
        log_responses = []
        for log in logs:
            log_responses.append(AuditLogResponse(
                id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                user_email=log.details.get('user_email') if log.details else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at.isoformat(),
                severity=log.details.get('severity', 'info') if log.details else 'info'
            ))
        
        return AuditLogListResponse(
            total=total,
            page=page,
            page_size=page_size,
            logs=log_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@router.get("/user/{user_id}/activity", response_model=UserActivityResponse)
async def get_user_activity(
    user_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=500, description="Number of recent actions"),
    db: Session = Depends(get_db)
):
    """
    Get activity history for a specific user
    
    Requires authentication. Users can view their own activity,
    admins can view any user's activity.
    """
    try:
        # Check authentication
        current_user = check_admin_permission(request)
        
        # Check permission
        if not getattr(current_user, 'is_admin', False) and str(current_user.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own activity"
            )
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        user_email = user.email if user else None
        
        # Get audit logs
        logs = db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        # Count actions by type
        actions_by_type = {}
        for log in logs:
            action = log.action
            actions_by_type[action] = actions_by_type.get(action, 0) + 1
        
        # Format recent actions
        recent_actions = []
        for log in logs[:20]:  # Last 20 actions
            recent_actions.append(AuditLogResponse(
                id=str(log.id),
                user_id=str(log.user_id),
                user_email=user_email,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at.isoformat()
            ))
        
        return UserActivityResponse(
            user_id=user_id,
            user_email=user_email,
            total_actions=len(logs),
            recent_actions=recent_actions,
            actions_by_type=actions_by_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )


@router.get("/resource/{resource_type}/{resource_id}/history", response_model=ResourceHistoryResponse)
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=500, description="Number of events"),
    db: Session = Depends(get_db)
):
    """
    Get audit history for a specific resource
    
    Shows all actions performed on a resource (invoice, legal query, etc.)
    """
    try:
        # Check authentication
        check_admin_permission(request)
        
        # Get audit logs for resource
        logs = db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        # Format history
        history = []
        for log in logs:
            history.append(AuditLogResponse(
                id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                user_email=log.details.get('user_email') if log.details else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id),
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at.isoformat()
            ))
        
        return ResourceHistoryResponse(
            resource_type=resource_type,
            resource_id=resource_id,
            total_events=len(logs),
            history=history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resource history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resource history"
        )


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get audit trail statistics
    
    Provides overview of system activity, user engagement, and security events.
    Requires admin permission.
    """
    try:
        # Check authentication and admin permission
        current_user = check_admin_permission(request)
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin permission required"
            )
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get logs in date range
        logs = db.query(AuditLog).filter(
            AuditLog.created_at >= start_date
        ).all()
        
        # Calculate statistics
        total_events = len(logs)
        unique_users = len(set(str(log.user_id) for log in logs if log.user_id))
        
        # Actions by type
        actions_by_type = {}
        for log in logs:
            action = log.action
            actions_by_type[action] = actions_by_type.get(action, 0) + 1
        
        # Events by day
        events_by_day = {}
        for log in logs:
            day = log.created_at.date().isoformat()
            events_by_day[day] = events_by_day.get(day, 0) + 1
        
        # Top users
        user_counts = {}
        for log in logs:
            if log.user_id:
                user_id = str(log.user_id)
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        top_users = [
            {'user_id': user_id, 'action_count': count}
            for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Recent security events
        security_actions = [
            AuditAction.LOGIN_FAILED.value,
            AuditAction.UNAUTHORIZED_ACCESS.value,
            AuditAction.PERMISSION_DENIED.value,
            AuditAction.SUSPICIOUS_ACTIVITY.value
        ]
        
        security_logs = [log for log in logs if log.action in security_actions]
        recent_security_events = [
            {
                'action': log.action,
                'user_id': str(log.user_id) if log.user_id else None,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat()
            }
            for log in sorted(security_logs, key=lambda x: x.created_at, reverse=True)[:10]
        ]
        
        return AuditStatsResponse(
            total_events=total_events,
            unique_users=unique_users,
            actions_by_type=actions_by_type,
            events_by_day=events_by_day,
            top_users=top_users,
            recent_security_events=recent_security_events
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit statistics"
        )


@router.get("/export")
async def export_audit_logs(
    request: Request,
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Export audit logs to CSV or JSON
    
    Requires admin permission.
    """
    try:
        # Check authentication and admin permission
        current_user = check_admin_permission(request)
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin permission required"
            )
        
        # Build query
        query = db.query(AuditLog)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at <= end_dt)
        
        logs = query.order_by(AuditLog.created_at.desc()).all()
        
        if format == "csv":
            # Generate CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'User ID', 'User Email', 'Action', 'Resource Type', 
                'Resource ID', 'IP Address', 'Timestamp', 'Details'
            ])
            
            # Write data
            for log in logs:
                writer.writerow([
                    str(log.id),
                    str(log.user_id) if log.user_id else '',
                    log.details.get('user_email', '') if log.details else '',
                    log.action,
                    log.resource_type or '',
                    str(log.resource_id) if log.resource_id else '',
                    log.ip_address or '',
                    log.created_at.isoformat(),
                    str(log.details) if log.details else ''
                ])
            
            from fastapi.responses import StreamingResponse
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        
        else:  # JSON
            # Generate JSON
            import json
            from fastapi.responses import Response
            
            logs_data = [
                {
                    'id': str(log.id),
                    'user_id': str(log.user_id) if log.user_id else None,
                    'user_email': log.details.get('user_email') if log.details else None,
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'resource_id': str(log.resource_id) if log.resource_id else None,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'created_at': log.created_at.isoformat()
                }
                for log in logs
            ]
            
            return Response(
                content=json.dumps(logs_data, indent=2),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.json"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export audit logs"
        )


@router.get("/health")
async def audit_health():
    """Health check endpoint for audit trail router"""
    return {
        "status": "healthy",
        "service": "Audit Trail API",
        "endpoints": [
            "/audit/logs",
            "/audit/user/{user_id}/activity",
            "/audit/resource/{resource_type}/{resource_id}/history",
            "/audit/stats",
            "/audit/export"
        ],
        "timestamp": datetime.now().isoformat()
    }

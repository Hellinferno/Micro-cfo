#!/usr/bin/env python3
"""
Proactive Intelligence Router for MicroCFO Integration Server
Handles API endpoints for proactive alerts, law monitoring, and subsidy matching
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Request, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database import get_db
from models import (
    ProactiveNotification, UserLawSubscription, LawChangeMonitor,
    BusinessProfile, Invoice, User
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/proactive", tags=["Proactive Intelligence"])


# ============================================================================
# Request/Response Models
# ============================================================================

class NotificationResponse(BaseModel):
    """Response model for a single notification"""
    id: str
    alert_type: str
    title: str
    message: str
    priority: str
    action_url: Optional[str] = None
    related_schemes: List[str] = []
    related_sections: List[str] = []
    is_read: bool
    created_at: str

class NotificationListResponse(BaseModel):
    """Response model for notification list"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int

class MarkReadRequest(BaseModel):
    """Request to mark notifications as read"""
    notification_ids: List[str] = Field(..., description="List of notification IDs to mark as read")

class LawSubscriptionRequest(BaseModel):
    """Request to subscribe to law change alerts"""
    law_types: List[str] = Field(..., description="Law types to monitor: GST, Income Tax, Companies Act, Labour Laws")
    specific_sections: Optional[List[str]] = Field(None, description="Specific sections to monitor")
    turnover_threshold_alert: bool = Field(True, description="Alert on turnover threshold changes")
    sector_specific_alert: bool = Field(True, description="Alert on sector-specific changes")

class SubsidyAnalysisRequest(BaseModel):
    """Request for transaction history subsidy analysis"""
    months: int = Field(6, ge=1, le=24, description="Number of months to analyze")

class SubsidyAnalysisResponse(BaseModel):
    """Response for subsidy analysis"""
    total_invoices: int
    total_spend: float
    capital_goods_spend: float
    raw_material_spend: float
    service_spend: float
    monthly_average: float
    subsidy_opportunities: List[dict]

class ProactiveCheckRequest(BaseModel):
    """Request to run proactive check on an invoice"""
    invoice_id: str = Field(..., description="Invoice ID to analyze")


# ============================================================================
# Notification Endpoints
# ============================================================================

@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    request: Request,
    db: Session = Depends(get_db),
    unread_only: bool = False,
    alert_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    Get user's proactive notifications
    
    Returns list of subsidy matches, law change alerts, and compliance reminders
    """
    # Get user ID from auth context
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        # For demo, use first user
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Build query
    query = db.query(ProactiveNotification).filter(
        ProactiveNotification.user_id == user_id,
        ProactiveNotification.is_dismissed == False
    )
    
    if unread_only:
        query = query.filter(ProactiveNotification.is_read == False)
    
    if alert_type:
        query = query.filter(ProactiveNotification.alert_type == alert_type)
    
    # Get total and unread counts
    total = query.count()
    unread_count = db.query(ProactiveNotification).filter(
        ProactiveNotification.user_id == user_id,
        ProactiveNotification.is_read == False,
        ProactiveNotification.is_dismissed == False
    ).count()
    
    # Get paginated results
    notifications = query.order_by(
        ProactiveNotification.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Format response
    notification_list = []
    for n in notifications:
        related_data = n.related_data or {}
        notification_list.append(NotificationResponse(
            id=str(n.id),
            alert_type=n.alert_type,
            title=n.title,
            message=n.message,
            priority=n.priority,
            action_url=n.action_url,
            related_schemes=related_data.get('related_schemes', []),
            related_sections=related_data.get('related_sections', []),
            is_read=n.is_read,
            created_at=n.created_at.isoformat() if n.created_at else ''
        ))
    
    return NotificationListResponse(
        notifications=notification_list,
        total=total,
        unread_count=unread_count
    )


@router.post("/notifications/mark-read")
async def mark_notifications_read(
    request: Request,
    mark_request: MarkReadRequest,
    db: Session = Depends(get_db)
):
    """Mark notifications as read"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Update notifications
    updated = db.query(ProactiveNotification).filter(
        ProactiveNotification.id.in_(mark_request.notification_ids),
        ProactiveNotification.user_id == user_id
    ).update({
        'is_read': True,
        'read_at': datetime.now()
    }, synchronize_session=False)
    
    db.commit()
    
    return {"success": True, "updated_count": updated}


@router.delete("/notifications/{notification_id}")
async def dismiss_notification(
    notification_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Dismiss a notification"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    notification = db.query(ProactiveNotification).filter(
        ProactiveNotification.id == notification_id,
        ProactiveNotification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_dismissed = True
    db.commit()
    
    return {"success": True, "message": "Notification dismissed"}


# ============================================================================
# Law Subscription Endpoints
# ============================================================================

@router.get("/subscriptions")
async def get_law_subscriptions(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get user's law change subscriptions"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    subscriptions = db.query(UserLawSubscription).filter(
        UserLawSubscription.user_id == user_id,
        UserLawSubscription.is_active == True
    ).all()
    
    return {
        "subscriptions": [
            {
                "id": str(s.id),
                "law_type": s.law_type,
                "specific_sections": s.specific_sections,
                "turnover_threshold_alert": s.turnover_threshold_alert,
                "sector_specific_alert": s.sector_specific_alert
            }
            for s in subscriptions
        ]
    }


@router.post("/subscriptions")
async def create_law_subscription(
    request: Request,
    subscription: LawSubscriptionRequest,
    db: Session = Depends(get_db)
):
    """Subscribe to law change alerts"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    created = []
    for law_type in subscription.law_types:
        # Check if already subscribed
        existing = db.query(UserLawSubscription).filter(
            UserLawSubscription.user_id == user_id,
            UserLawSubscription.law_type == law_type,
            UserLawSubscription.is_active == True
        ).first()
        
        if existing:
            # Update existing
            existing.specific_sections = subscription.specific_sections
            existing.turnover_threshold_alert = subscription.turnover_threshold_alert
            existing.sector_specific_alert = subscription.sector_specific_alert
            created.append(str(existing.id))
        else:
            # Create new
            new_sub = UserLawSubscription(
                user_id=user_id,
                law_type=law_type,
                specific_sections=subscription.specific_sections,
                turnover_threshold_alert=subscription.turnover_threshold_alert,
                sector_specific_alert=subscription.sector_specific_alert
            )
            db.add(new_sub)
            db.flush()
            created.append(str(new_sub.id))
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Subscribed to {len(subscription.law_types)} law types",
        "subscription_ids": created
    }


@router.delete("/subscriptions/{law_type}")
async def unsubscribe_law(
    law_type: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Unsubscribe from a law type"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    updated = db.query(UserLawSubscription).filter(
        UserLawSubscription.user_id == user_id,
        UserLawSubscription.law_type == law_type
    ).update({'is_active': False}, synchronize_session=False)
    
    db.commit()
    
    return {"success": True, "unsubscribed": updated > 0}


# ============================================================================
# Subsidy Analysis Endpoints
# ============================================================================

@router.post("/analyze-history", response_model=SubsidyAnalysisResponse)
async def analyze_transaction_history(
    request: Request,
    analysis_request: SubsidyAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze transaction history to find subsidy opportunities
    
    Scans past invoices to identify capital goods purchases and
    match them with government subsidy schemes
    """
    from proactive_intelligence import get_proactive_engine
    
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    engine = get_proactive_engine()
    analysis = engine.analyze_transaction_history(
        db=db,
        user_id=str(user_id),
        months=analysis_request.months
    )
    
    if 'error' in analysis:
        raise HTTPException(status_code=400, detail=analysis['error'])
    
    return SubsidyAnalysisResponse(**analysis)


@router.post("/check-invoice")
async def check_invoice_for_subsidies(
    request: Request,
    check_request: ProactiveCheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run proactive subsidy check on a specific invoice
    
    Analyzes the invoice for capital goods and matches against subsidy schemes
    """
    from proactive_intelligence import get_proactive_engine
    
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get invoice
    invoice = db.query(Invoice).filter(
        Invoice.id == check_request.invoice_id,
        Invoice.user_id == user_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.extracted_data:
        raise HTTPException(status_code=400, detail="Invoice has no extracted data")
    
    # Get business profile
    business = db.query(BusinessProfile).filter(
        BusinessProfile.owner_id == user_id
    ).first()
    
    if not business:
        raise HTTPException(status_code=400, detail="No business profile found")
    
    business_profile = {
        'industry_type': business.industry_type,
        'turnover_range': business.turnover_range,
        'location_state': business.location_state
    }
    
    # Run analysis
    engine = get_proactive_engine()
    alerts = engine.analyze_invoice_for_subsidies(
        invoice_data=invoice.extracted_data,
        business_profile=business_profile
    )
    
    # Store alerts in background
    async def store_alerts():
        for alert in alerts:
            notification = ProactiveNotification(
                user_id=user_id,
                alert_type=alert.alert_type,
                title=alert.title,
                message=alert.message,
                priority=alert.priority,
                action_url=alert.action_url,
                related_data=alert.to_dict(),
                triggered_by_invoice_id=invoice.id,
                is_read=False
            )
            db.add(notification)
        db.commit()
    
    background_tasks.add_task(store_alerts)
    
    return {
        "success": True,
        "alerts_count": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }


# ============================================================================
# Law Change Monitoring Endpoints
# ============================================================================

@router.get("/law-changes")
async def get_recent_law_changes(
    request: Request,
    db: Session = Depends(get_db),
    law_type: Optional[str] = None,
    days: int = 30
):
    """Get recent law changes tracked by the system"""
    cutoff = datetime.now() - timedelta(days=days)
    
    query = db.query(LawChangeMonitor).filter(
        LawChangeMonitor.discovered_at >= cutoff
    )
    
    if law_type:
        query = query.filter(LawChangeMonitor.law_type == law_type)
    
    changes = query.order_by(LawChangeMonitor.discovered_at.desc()).limit(50).all()
    
    return {
        "law_changes": [
            {
                "id": str(c.id),
                "law_type": c.law_type,
                "section_number": c.section_number,
                "change_summary": c.change_summary,
                "source_url": c.source_url,
                "effective_date": c.effective_date.isoformat() if c.effective_date else None,
                "discovered_at": c.discovered_at.isoformat() if c.discovered_at else None
            }
            for c in changes
        ],
        "total": len(changes)
    }


@router.post("/check-law-relevance")
async def check_law_relevance_for_user(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Check for law changes relevant to the user's business
    
    Analyzes recent law changes against user's business profile
    and generates alerts for relevant changes
    """
    from proactive_intelligence import get_proactive_engine
    
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get business profile
    business = db.query(BusinessProfile).filter(
        BusinessProfile.owner_id == user_id
    ).first()
    
    if not business:
        raise HTTPException(status_code=400, detail="No business profile found")
    
    business_profile = {
        'industry_type': business.industry_type,
        'turnover_range': business.turnover_range,
        'location_state': business.location_state,
        'business_type': ''
    }
    
    # Run check
    engine = get_proactive_engine()
    alerts = await engine.check_law_changes_for_user(
        user_id=str(user_id),
        business_profile=business_profile,
        since_days=7
    )
    
    # Store alerts
    for alert in alerts:
        # Check for duplicates
        existing = db.query(ProactiveNotification).filter(
            ProactiveNotification.user_id == user_id,
            ProactiveNotification.alert_type == alert.alert_type,
            ProactiveNotification.title == alert.title,
            ProactiveNotification.created_at >= datetime.now() - timedelta(hours=24)
        ).first()
        
        if not existing:
            notification = ProactiveNotification(
                user_id=user_id,
                alert_type=alert.alert_type,
                title=alert.title,
                message=alert.message,
                priority=alert.priority,
                action_url=alert.action_url,
                related_data=alert.to_dict(),
                is_read=False
            )
            db.add(notification)
    
    db.commit()
    
    return {
        "success": True,
        "alerts_count": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }


# ============================================================================
# Dashboard Summary Endpoint
# ============================================================================

@router.get("/dashboard-summary")
async def get_proactive_dashboard_summary(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get a summary for the proactive intelligence dashboard
    
    Returns counts and highlights for notifications, subsidies, and law changes
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        user = db.query(User).first()
        user_id = user.id if user else None
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get notification counts
    unread_total = db.query(ProactiveNotification).filter(
        ProactiveNotification.user_id == user_id,
        ProactiveNotification.is_read == False,
        ProactiveNotification.is_dismissed == False
    ).count()
    
    unread_high_priority = db.query(ProactiveNotification).filter(
        ProactiveNotification.user_id == user_id,
        ProactiveNotification.is_read == False,
        ProactiveNotification.is_dismissed == False,
        ProactiveNotification.priority == 'high'
    ).count()
    
    subsidy_alerts = db.query(ProactiveNotification).filter(
        ProactiveNotification.user_id == user_id,
        ProactiveNotification.alert_type == 'subsidy_match',
        ProactiveNotification.is_dismissed == False
    ).count()
    
    law_alerts = db.query(ProactiveNotification).filter(
        ProactiveNotification.user_id == user_id,
        ProactiveNotification.alert_type == 'law_change',
        ProactiveNotification.is_dismissed == False
    ).count()
    
    # Get recent high-priority alerts
    recent_urgent = db.query(ProactiveNotification).filter(
        ProactiveNotification.user_id == user_id,
        ProactiveNotification.priority == 'high',
        ProactiveNotification.is_read == False,
        ProactiveNotification.is_dismissed == False
    ).order_by(ProactiveNotification.created_at.desc()).limit(3).all()
    
    # Get subscribed law types
    subscriptions = db.query(UserLawSubscription).filter(
        UserLawSubscription.user_id == user_id,
        UserLawSubscription.is_active == True
    ).all()
    
    return {
        "summary": {
            "unread_total": unread_total,
            "unread_high_priority": unread_high_priority,
            "subsidy_opportunities": subsidy_alerts,
            "law_change_alerts": law_alerts,
            "monitored_law_types": [s.law_type for s in subscriptions]
        },
        "urgent_alerts": [
            {
                "id": str(a.id),
                "title": a.title,
                "message": a.message[:100] + "..." if len(a.message) > 100 else a.message,
                "alert_type": a.alert_type,
                "created_at": a.created_at.isoformat() if a.created_at else ''
            }
            for a in recent_urgent
        ]
    }

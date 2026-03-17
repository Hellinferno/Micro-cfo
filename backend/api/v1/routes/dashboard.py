"""
Dashboard API - Aggregated metrics and overview data
Provides quick insights and summary statistics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, select, and_
from datetime import datetime, timedelta
from typing import Optional
import uuid

from src.database import get_db
from src.models import Invoice, SubsidyApplication, SubsidyMatch, ProactiveNotification, LegalQuery
from middleware.auth import get_current_user
from src.auth import UserContext

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics")
async def get_dashboard_metrics(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard metrics for authenticated user

    Returns aggregated statistics for invoices, compliance, subsidies, etc.
    """
    try:
        user_id = uuid.UUID(current_user.user_id)

        # Invoice metrics
        invoice_count_stmt = select(func.count(Invoice.id)).where(Invoice.user_id == user_id)
        total_invoices = db.execute(invoice_count_stmt).scalar() or 0

        invoice_amount_stmt = select(func.sum(Invoice.total_amount)).where(
            Invoice.user_id == user_id,
            Invoice.status == 'processed'
        )
        # Note: total_amount might be encrypted, handle accordingly
        total_amount = 0  # Will be populated when encryption is properly handled

        # Invoice status breakdown
        processed_count_stmt = select(func.count(Invoice.id)).where(
            Invoice.user_id == user_id,
            Invoice.status == 'processed'
        )
        processed_invoices = db.execute(processed_count_stmt).scalar() or 0

        flagged_count_stmt = select(func.count(Invoice.id)).where(
            Invoice.user_id == user_id,
            Invoice.status == 'flagged'
        )
        flagged_invoices = db.execute(flagged_count_stmt).scalar() or 0

        pending_count_stmt = select(func.count(Invoice.id)).where(
            Invoice.user_id == user_id,
            Invoice.status == 'pending'
        )
        pending_invoices = db.execute(pending_count_stmt).scalar() or 0

        # Subsidy metrics
        subsidy_count_stmt = select(func.count(SubsidyMatch.id)).join(
            Invoice, SubsidyMatch.business_id == Invoice.business_id
        ).where(Invoice.user_id == user_id)
        subsidies_found = db.execute(subsidy_count_stmt).scalar() or 0

        # Compliance score (simplified calculation)
        total_compliance_queries = 0
        if total_invoices > 0:
            # Base score on invoice processing success rate
            compliance_score = int((processed_invoices / total_invoices) * 100) if total_invoices > 0 else 0
        else:
            compliance_score = 100  # Default perfect score if no invoices

        # Calculate monthly growth (simplified - would need historical data)
        monthly_growth = 0.0  # Placeholder

        return {
            "success": True,
            "data": {
                "metrics": {
                    "totalInvoices": total_invoices,
                    "totalAmount": total_amount,
                    "complianceScore": compliance_score,
                    "subsidiesFound": subsidies_found,
                    "pendingNegotiations": 0,  # Would need Negotiation model query
                    "monthlyGrowth": monthly_growth,
                    "processedInvoices": processed_invoices,
                    "flaggedInvoices": flagged_invoices,
                    "pendingInvoices": pending_invoices
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard metrics: {str(e)}"
        )


@router.get("/recent-invoices")
async def get_recent_invoices(
    limit: int = 5,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent invoices for dashboard display
    """
    try:
        user_id = uuid.UUID(current_user.user_id)

        stmt = select(Invoice).where(Invoice.user_id == user_id).order_by(
            Invoice.created_at.desc()
        ).limit(limit)

        invoices = db.execute(stmt).scalars().all()

        invoice_list = []
        for invoice in invoices:
            invoice_list.append({
                "id": str(invoice.id),
                "vendor": "Vendor (encrypted)",  # Would decrypt in production
                "amount": 0,  # Would decrypt
                "date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "status": invoice.status,
                "category": invoice.category or "General"
            })

        return {
            "success": True,
            "data": {
                "invoices": invoice_list,
                "total": len(invoice_list)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recent invoices: {str(e)}"
        )


@router.get("/alerts")
async def get_compliance_alerts(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get compliance alerts and notifications
    """
    try:
        user_id = uuid.UUID(current_user.user_id)

        # Get proactive notifications
        stmt = select(ProactiveNotification).where(
            ProactiveNotification.user_id == user_id,
            ProactiveNotification.is_dismissed == False
        ).order_by(ProactiveNotification.created_at.desc()).limit(10)

        notifications = db.execute(stmt).scalars().all()

        alerts = []
        for notif in notifications:
            alert_type = 'info'
            if 'warning' in notif.priority.lower() or 'urgent' in notif.priority.lower():
                alert_type = 'warning'
            elif notif.alert_type == 'subsidy_match':
                alert_type = 'success'

            alerts.append({
                "id": str(notif.id),
                "type": alert_type,
                "message": notif.message,
                "date": notif.created_at.strftime("%Y-%m-%d") if notif.created_at else None
            })

        # Add default welcome alert if no notifications
        if not alerts:
            alerts.append({
                "id": "default_1",
                "type": "info",
                "message": "Welcome to MicroCFO! Upload your first invoice to get started.",
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            })

        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total": len(alerts)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch compliance alerts: {str(e)}"
        )


@router.get("/subsidy-matches")
async def get_subsidy_matches(
    limit: int = 4,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommended subsidies for dashboard
    """
    try:
        user_id = uuid.UUID(current_user.user_id)

        # Get subsidy matches through business profile
        stmt = select(SubsidyMatch).join(
            Invoice, SubsidyMatch.business_id == Invoice.business_id
        ).where(
            Invoice.user_id == user_id
        ).order_by(
            SubsidyMatch.match_score.desc(),
            SubsidyMatch.created_at.desc()
        ).limit(limit)

        matches = db.execute(stmt).scalars().all()

        subsidy_list = []
        for match in matches:
            subsidy_list.append({
                "id": str(match.id),
                "name": match.scheme_name,
                "benefit": "Government subsidy benefit",  # Would fetch from scheme details
                "matchScore": int(match.match_score * 100) if match.match_score else 0,
                "deadline": None  # Would fetch from scheme data
            })

        # Add placeholder if no matches
        if not subsidy_list:
            subsidy_list.append({
                "id": "placeholder_1",
                "name": "MSME Technology Scheme",
                "benefit": "Up to 50% subsidy on machinery",
                "matchScore": 85,
                "deadline": "2024-03-31"
            })

        return {
            "success": True,
            "data": {
                "subsidies": subsidy_list,
                "total": len(subsidy_list)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch subsidy matches: {str(e)}"
        )


@router.get("/summary")
async def get_dashboard_summary(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete dashboard summary in one call
    Combines metrics, recent invoices, alerts, and subsidies
    """
    try:
        # Get all components
        metrics_response = await get_dashboard_metrics(current_user, db)
        invoices_response = await get_recent_invoices(5, current_user, db)
        alerts_response = await get_compliance_alerts(current_user, db)
        subsidies_response = await get_subsidy_matches(4, current_user, db)

        return {
            "success": True,
            "data": {
                "metrics": metrics_response["data"]["metrics"],
                "recentInvoices": invoices_response["data"]["invoices"],
                "complianceAlerts": alerts_response["data"]["alerts"],
                "subsidyMatches": subsidies_response["data"]["subsidies"],
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard summary: {str(e)}"
        )

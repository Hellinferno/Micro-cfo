from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import WorkflowState, Invoice, VendorProfile, BusinessProfile, ProactiveNotification
from mcp_bridge import MCPBridge
from pydantic import BaseModel
import logging
from datetime import datetime
import uuid

router = APIRouter(prefix="/workflow", tags=["Orchestrator"])
logger = logging.getLogger(__name__)

class DocumentLifecycleRequest(BaseModel):
    image_url: str
    user_id: str

@router.post("/process-document-lifecycle")
async def process_document_lifecycle(
    request: Request,
    lifecycle_request: DocumentLifecycleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Orchestrates the full document lifecycle:
    1. Visual Audit (Agent A)
    2. Data Persistence
    3. Proactive Subsidy Check (NEW - auto-triggers Agent C)
    4. Negotiation Decision (The "Brain")
    5. Negotiation Draft (Agent D) if necessary
    """
    logger.info(f"Starting document lifecycle for user {lifecycle_request.user_id}")
    mcp_bridge: MCPBridge = request.app.state.mcp_bridge
    
    # 1. Visual Audit
    audit_result = await mcp_bridge.call_agent_a(image_url=lifecycle_request.image_url)
    if not audit_result.get("success"):
        raise HTTPException(status_code=500, detail="Audit failed")
    
    invoice_data = audit_result["result"]
    vendor_name = invoice_data.get("vendor_name")
    total_amount = invoice_data.get("total_amount")

    # 2. Persist State
    workflow_id = uuid.uuid4()
    workflow = WorkflowState(
        id=workflow_id,
        status="AUDIT_COMPLETE",
        current_step="evaluating_proactive_intelligence",
        context_data=invoice_data,
        history=[{"step": "audit", "timestamp": datetime.now().isoformat(), "result": "success"}]
    )
    db.add(workflow)
    db.commit()

    # 3. PROACTIVE INTELLIGENCE - Auto-trigger subsidy check
    proactive_alerts = []
    try:
        from proactive_intelligence import get_proactive_engine
        
        # Get user's business profile
        business = db.query(BusinessProfile).filter(
            BusinessProfile.owner_id == lifecycle_request.user_id
        ).first()
        
        if business:
            business_profile = {
                'industry_type': business.industry_type or 'manufacturing',
                'turnover_range': business.turnover_range or '',
                'location_state': business.location_state or ''
            }
            
            engine = get_proactive_engine()
            proactive_alerts = engine.analyze_invoice_for_subsidies(
                invoice_data=invoice_data,
                business_profile=business_profile
            )
            
            # Store alerts asynchronously
            if proactive_alerts:
                background_tasks.add_task(
                    _store_proactive_alerts,
                    db_session_factory=request.app.state.db_session_factory if hasattr(request.app.state, 'db_session_factory') else None,
                    user_id=lifecycle_request.user_id,
                    alerts=proactive_alerts,
                    workflow_id=workflow_id
                )
                
                # Update workflow
                history = list(workflow.history)
                history.append({
                    "step": "proactive_subsidy_check",
                    "timestamp": datetime.now().isoformat(),
                    "result": f"found_{len(proactive_alerts)}_opportunities"
                })
                workflow.history = history
                workflow.current_step = "subsidy_opportunities_found"
                db.commit()
                
                logger.info(f"🎯 Proactive subsidy check found {len(proactive_alerts)} opportunities!")
    except Exception as e:
        logger.warning(f"Proactive intelligence check failed: {e}")

    # 4. Decision Logic for Negotiation
    workflow.current_step = "evaluating_negotiation"
    db.commit()
    
    vendor_profile = db.query(VendorProfile).filter(VendorProfile.name == vendor_name).first()
    
    should_negotiate = False
    negotiation_draft = None
    
    if vendor_profile:
        if total_amount > (vendor_profile.average_spend_monthly * 1.2):
            should_negotiate = True
            logger.info(f"Negotiation triggered: Spending spike detected for {vendor_name}")
    else:
        if total_amount > 50000:
             should_negotiate = True

    # 5. Negotiate if needed
    if should_negotiate:
        negotiation_result = await mcp_bridge.call_agent_d(
            counterparty_name=vendor_name,
            amount=total_amount,
            transaction_type="payable",
            due_date=invoice_data.get("invoice_date", datetime.now().strftime("%Y-%m-%d")),
            current_cash_position=1000000,
            upcoming_outflows=500000,
        )
        if negotiation_result.get("success"):
            negotiation_draft = negotiation_result["result"]
            workflow.status = "NEGOTIATION_DRAFTED"
            workflow.current_step = "waiting_for_approval"
            history = list(workflow.history)
            history.append({"step": "negotiation", "timestamp": datetime.now().isoformat(), "result": "drafted"})
            workflow.history = history
            db.commit()

    return {
        "workflow_id": str(workflow_id),
        "audit_result": invoice_data,
        "proactive_alerts": [alert.to_dict() for alert in proactive_alerts],
        "proactive_message": proactive_alerts[0].message if proactive_alerts else None,
        "negotiation_needed": should_negotiate,
        "negotiation_draft": negotiation_draft
    }


async def _store_proactive_alerts(db_session_factory, user_id: str, alerts: list, workflow_id):
    """Background task to store proactive alerts in database"""
    if not db_session_factory:
        return
    
    try:
        from database import SessionLocal
        db = SessionLocal()
        
        for alert in alerts:
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
        db.close()
    except Exception as e:
        logger.error(f"Failed to store proactive alerts: {e}")

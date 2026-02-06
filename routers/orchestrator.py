from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import WorkflowState, Invoice, VendorProfile, BusinessProfile, ProactiveNotification
from mcp_bridge import MCPBridge
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import uuid

router = APIRouter(prefix="/workflow", tags=["Orchestrator"])
logger = logging.getLogger(__name__)


class DocumentLifecycleRequest(BaseModel):
    """Request for document lifecycle processing"""
    image_url: str = Field(..., description="URL or base64 encoded image of the invoice")
    user_id: str = Field(..., description="User ID for context and personalization")


class EnhancedDocumentRequest(BaseModel):
    """Enhanced request with business profile for better intelligence"""
    image_url: str = Field(..., description="URL or base64 encoded image of the invoice")
    user_id: str = Field(..., description="User ID for context")
    industry_type: Optional[str] = Field(None, description="Business industry type")
    turnover_range: Optional[str] = Field(None, description="Business turnover range")
    location_state: Optional[str] = Field(None, description="Business location state")


class WorkflowDecisionResponse(BaseModel):
    """Individual workflow decision"""
    step: str
    decision: str
    reason: str
    triggered_agent: Optional[str] = None


class EnhancedWorkflowResponse(BaseModel):
    """Enhanced workflow response with full decision trail"""
    workflow_id: str
    status: str
    invoice_data: Dict[str, Any]
    decisions: List[WorkflowDecisionResponse]
    subsidy_alerts: List[Dict[str, Any]]
    compliance_alerts: List[Dict[str, Any]]
    negotiation_draft: Optional[Dict[str, Any]] = None
    requires_review: bool
    review_reasons: List[str]
    recommendations: List[str]
    processing_time_ms: float
    confidence_score: Optional[float] = None

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
    
    # Get MCP bridge from app state (with safe access)
    mcp_bridge = getattr(request.app.state, 'mcp_bridge', None)
    if not mcp_bridge:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP bridge not initialized. Service temporarily unavailable."
        )
    
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
        from src.database import SessionLocal
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

@router.post("/process-document-v2", response_model=EnhancedWorkflowResponse)
async def process_document_v2(
    request: Request,
    lifecycle_request: EnhancedDocumentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Enhanced Document Lifecycle Processing (v2)
    
    This endpoint implements the complete PRD workflow:
    1. Visual Audit (Agent A) with confidence scoring
    2. Automatic confidence threshold check (0.7 triggers review)
    3. Auto-trigger Agent C for capital goods > ₹1 Lakh
    4. Auto-trigger Agent B for personal/entertainment items
    5. Negotiation decision based on vendor profile
    6. Draft generation (NEVER auto-send)
    7. Human approval requirement
    
    Features:
    - Full decision audit trail
    - CA-style conservative recommendations
    - Confidence scoring with component breakdown
    - Proactive intelligence integration
    
    Requirements: PRD Document Lifecycle
    """
    start_time = datetime.now()
    
    try:
        # Get MCP bridge
        mcp_bridge = getattr(request.app.state, 'mcp_bridge', None)
        if not mcp_bridge:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MCP bridge not initialized"
            )
        
        # Build business profile from request
        business_profile = {}
        if lifecycle_request.industry_type:
            business_profile["industry_type"] = lifecycle_request.industry_type
        if lifecycle_request.turnover_range:
            business_profile["turnover_range"] = lifecycle_request.turnover_range
        if lifecycle_request.location_state:
            business_profile["location_state"] = lifecycle_request.location_state
        
        # If no profile in request, try to get from database
        if not business_profile:
            business = db.query(BusinessProfile).filter(
                BusinessProfile.owner_id == lifecycle_request.user_id
            ).first()
            if business:
                business_profile = {
                    "industry_type": business.industry_type or "manufacturing",
                    "turnover_range": business.turnover_range or "",
                    "location_state": business.location_state or ""
                }
        
        # Use enhanced workflow engine
        from workflow_engine import get_workflow_engine
        
        workflow_engine = get_workflow_engine(
            mcp_bridge=mcp_bridge,
            db_session=db
        )
        
        result = await workflow_engine.process_document_lifecycle(
            image_url=lifecycle_request.image_url,
            user_id=lifecycle_request.user_id,
            business_profile=business_profile
        )
        
        # Persist workflow state
        workflow = WorkflowState(
            id=uuid.UUID(result.workflow_id),
            status=result.status.value,
            current_step="completed" if not result.requires_review else "waiting_for_review",
            context_data=result.invoice_data,
            history=[d.to_dict() for d in result.decisions]
        )
        db.add(workflow)
        
        # Store proactive alerts
        if result.subsidy_alerts:
            for alert in result.subsidy_alerts:
                notification = ProactiveNotification(
                    user_id=lifecycle_request.user_id,
                    alert_type=alert.get("type", "subsidy_match"),
                    title=alert.get("title", "Subsidy Opportunity"),
                    message=alert.get("message", ""),
                    priority=alert.get("priority", "medium"),
                    action_url=alert.get("action_url"),
                    related_data=alert,
                    is_read=False
                )
                db.add(notification)
        
        db.commit()
        
        # Convert decisions to response format
        decision_responses = [
            WorkflowDecisionResponse(
                step=d.step.value,
                decision=d.decision,
                reason=d.reason,
                triggered_agent=d.triggered_agent
            )
            for d in result.decisions
        ]
        
        return EnhancedWorkflowResponse(
            workflow_id=result.workflow_id,
            status=result.status.value,
            invoice_data=result.invoice_data,
            decisions=decision_responses,
            subsidy_alerts=result.subsidy_alerts,
            compliance_alerts=result.compliance_alerts,
            negotiation_draft=result.negotiation_draft,
            requires_review=result.requires_review,
            review_reasons=result.review_reasons,
            recommendations=result.recommendations,
            processing_time_ms=result.processing_time_ms,
            confidence_score=result.invoice_data.get("confidence_score")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced workflow error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow processing failed: {str(e)}"
        )


@router.get("/health")
async def orchestrator_health():
    """Health check for Orchestrator (The Brain)"""
    return {
        "status": "healthy",
        "component": "Orchestrator (The Brain)",
        "features": [
            "Document lifecycle management",
            "Multi-agent coordination",
            "Confidence scoring",
            "Proactive intelligence",
            "Negotiation drafting"
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/workflow/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a specific workflow"""
    try:
        workflow = db.query(WorkflowState).filter(
            WorkflowState.id == uuid.UUID(workflow_id)
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return {
            "workflow_id": str(workflow.id),
            "status": workflow.status,
            "current_step": workflow.current_step,
            "context_data": workflow.context_data,
            "history": workflow.history,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
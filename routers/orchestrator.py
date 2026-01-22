from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models import WorkflowState, Invoice, VendorProfile
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
    db: Session = Depends(get_db)
):
    """
    Orchestrates the full document lifecycle:
    1. Visual Audit (Agent A)
    2. Data Persistence
    3. Negotiation Decision (The "Brain")
    4. Negotiation Draft (Agent D) if necessary
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
    # Note: Ideally we save Invoice object first, here we simulate it
    workflow_id = uuid.uuid4()
    workflow = WorkflowState(
        id=workflow_id,
        status="AUDIT_COMPLETE",
        current_step="evaluating_negotiation",
        context_data=invoice_data,
        history=[{"step": "audit", "timestamp": datetime.now().isoformat(), "result": "success"}]
    )
    db.add(workflow)
    db.commit()

    # 3. Decision Logic
    # Check Vendor Profile
    vendor_profile = db.query(VendorProfile).filter(VendorProfile.name == vendor_name).first()
    
    should_negotiate = False
    negotiation_draft = None
    
    if vendor_profile:
        # Example logic: Negotiate if amount is > 20% of average monthly spend
        if total_amount > (vendor_profile.average_spend_monthly * 1.2):
            should_negotiate = True
            logger.info(f"Negotiation triggered: Spending spike detected for {vendor_name}")
    else:
        # New vendor or no history? Maybe negotiate if amount is large
        if total_amount > 50000: # Example threshold
             should_negotiate = True

    # 4. Negotiate if needed
    if should_negotiate:
        negotiation_result = await mcp_bridge.call_agent_d(
            counterparty_name=vendor_name,
            amount=total_amount,
            transaction_type="payable",
            due_date=invoice_data.get("invoice_date", datetime.now().strftime("%Y-%m-%d")),
            current_cash_position=1000000, # TODO: Fetch from real financial data
            upcoming_outflows=500000, # TODO: Fetch real data
        )
        if negotiation_result.get("success"):
            negotiation_draft = negotiation_result["result"]
            workflow.status = "NEGOTIATION_DRAFTED"
            workflow.current_step = "waiting_for_approval"
            # Append to history
            history = list(workflow.history)
            history.append({"step": "negotiation", "timestamp": datetime.now().isoformat(), "result": "drafted"})
            workflow.history = history
            db.commit()

    return {
        "workflow_id": str(workflow_id),
        "audit_result": invoice_data,
        "negotiation_needed": should_negotiate,
        "negotiation_draft": negotiation_draft
    }

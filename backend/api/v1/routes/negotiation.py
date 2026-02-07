"""
Negotiation API Routes
Negotiator - Agent D functionality
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.agents.negotiator import Negotiator

router = APIRouter()
negotiator = Negotiator()


class NegotiationRequest(BaseModel):
    invoice_data: Dict[str, Any]
    negotiation_context: str
    vendor_relationship: Optional[str] = "neutral"
    tone: Optional[str] = "professional"


class EmailDraftResponse(BaseModel):
    subject: str
    body: str
    strategy_explanation: str
    success: bool = True
    error: Optional[str] = None


@router.post("/generate-email", response_model=EmailDraftResponse)
async def generate_email(request: NegotiationRequest):
    """
    Generate a negotiation email based on invoice and context
    """
    try:
        # Map API request to agent request model
        # Note: We're reusing the Pydantic model structure but ensuring it matches what agent expects
        email_draft = await negotiator.generate_email(request)
        
        return EmailDraftResponse(
            subject=email_draft.subject,
            body=email_draft.body,
            strategy_explanation=email_draft.strategy_explanation,
            success=True
        )
    except Exception as e:
        return EmailDraftResponse(
            subject="",
            body="",
            strategy_explanation="",
            success=False,
            error=str(e)
        )

"""
Negotiation Email API (Agent D - Negotiator)
AI-powered vendor negotiation draft generation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/negotiation", tags=["Negotiation"])


class NegotiationIntent(str, Enum):
    """Negotiation intent types"""
    CREDIT_EXTENSION = "credit_extension"
    PAYMENT_CHASE = "payment_chase"
    EARLY_PAYMENT_OFFER = "early_payment_offer"


class VendorRelationship(str, Enum):
    """Vendor relationship status"""
    NEUTRAL = "neutral"
    GOOD = "good"
    STRAINED = "strained"


class NegotiationTone(str, Enum):
    """Communication tone"""
    PROFESSIONAL = "professional"
    FIRM = "firm"
    POLITE = "polite"
    FRIENDLY = "friendly"


class InvoiceContext(BaseModel):
    """Invoice context for negotiation"""
    vendor_name: str
    invoice_number: Optional[str] = None
    amount: float
    due_date: str
    days_overdue: Optional[int] = 0
    transaction_type: str = "payable"  # payable or receivable


class NegotiationRequest(BaseModel):
    """Negotiation draft request"""
    invoice_data: InvoiceContext
    negotiation_context: str
    vendor_relationship: VendorRelationship = VendorRelationship.NEUTRAL
    tone: NegotiationTone = NegotiationTone.PROFESSIONAL
    generate_variations: bool = True


class NegotiationDraft(BaseModel):
    """Generated negotiation email draft"""
    subject: str
    body: str
    telegram_message: Optional[str] = None
    strategy_explanation: str
    intent: NegotiationIntent
    tone: str
    variation_id: Optional[str] = None  # For A/B testing


class NegotiationResponse(BaseModel):
    """Negotiation response with A/B variations"""
    primary_draft: NegotiationDraft
    alternative_draft: Optional[NegotiationDraft] = None
    cash_flow_analysis: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


@router.post("/generate", response_model=NegotiationResponse)
async def generate_negotiation_draft(request: NegotiationRequest):
    """
    Generate negotiation email using Agent D (Negotiator)
    
    Creates context-aware negotiation drafts with:
    - Smart intent detection (credit extension, payment chase, early payment)
    - A/B variations (relationship vs transactional focus)
    - Multi-format output (email + Telegram message)
    - Cash flow-based strategy recommendations
    """
    try:
        from backend.agents.negotiator import generate_negotiation
        
        # Generate negotiation draft
        result = await generate_negotiation(
            invoice_data=request.invoice_data.dict(),
            negotiation_context=request.negotiation_context,
            vendor_relationship=request.vendor_relationship.value,
            tone=request.tone.value,
            generate_variations=request.generate_variations
        )
        
        return NegotiationResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate negotiation draft: {str(e)}"
        )


@router.post("/analyze-intent")
async def analyze_negotiation_intent(
    cash_position: float,
    upcoming_outflows: float,
    invoice_amount: float,
    due_date: str
):
    """
    Analyze financial position to determine negotiation intent
    
    Returns recommended negotiation strategy based on cash flow
    """
    try:
        from backend.agents.negotiator import determine_negotiation_intent
        
        intent = await determine_negotiation_intent(
            cash_position=cash_position,
            upcoming_outflows=upcoming_outflows,
            invoice_amount=invoice_amount,
            due_date=due_date
        )
        
        return {
            "success": True,
            "data": {
                "recommended_intent": intent,
                "cash_flow_status": "tight" if cash_position < upcoming_outflows else "healthy",
                "recommendation": get_intent_recommendation(intent)
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze intent: {str(e)}"
        )


def get_intent_recommendation(intent: NegotiationIntent) -> str:
    """Get recommendation text for intent"""
    recommendations = {
        NegotiationIntent.CREDIT_EXTENSION: "Request credit extension due to tight cash flow",
        NegotiationIntent.PAYMENT_CHASE: "Follow up on overdue payment professionally",
        NegotiationIntent.EARLY_PAYMENT_OFFER: "Offer early payment discount for better terms"
    }
    return recommendations.get(intent, "Review negotiation strategy")


@router.get("/templates")
async def get_negotiation_templates():
    """
    Get negotiation email templates
    
    Returns template library for common scenarios
    """
    templates = {
        "credit_extension": {
            "subject": "Request for Payment Extension - Invoice {invoice_number}",
            "context": "When cash flow is tight and need more time to pay"
        },
        "payment_chase": {
            "subject": "Payment Reminder - Invoice {invoice_number} Overdue",
            "context": "When customer payment is overdue"
        },
        "early_payment_offer": {
            "subject": "Early Payment Offer - Invoice {invoice_number}",
            "context": "When offering early payment for discount"
        }
    }
    
    return {
        "success": True,
        "data": {
            "templates": templates,
            "usage_guide": "Replace placeholders with actual values"
        }
    }


@router.get("/history")
async def get_negotiation_history(
    skip: int = 0,
    limit: int = 20
):
    """
    Get negotiation draft history
    
    Returns previously generated negotiation drafts
    """
    # TODO: Implement database query
    return {
        "success": True,
        "data": {
            "negotiations": [],
            "total": 0,
            "skip": skip,
            "limit": limit
        }
    }

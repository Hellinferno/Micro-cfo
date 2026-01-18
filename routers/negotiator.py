#!/usr/bin/env python3
"""
Negotiator Router for MicroCFO Integration Server
Handles Agent D (Negotiator) REST endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from datetime import datetime

from mcp_bridge import MCPBridge, MCPBridgeError
from legal_disclaimers import (
    LegalDisclaimers, DisclaimerType, Guardrails,
    get_negotiator_disclaimer, check_can_send_email
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agents/negotiator", tags=["Negotiator"])

# Request/Response Models
class GenerateDraftRequest(BaseModel):
    """Request model for negotiation email generation"""
    counterparty_name: str = Field(..., description="Name of vendor/customer", min_length=1, max_length=200)
    amount: float = Field(..., description="Transaction amount in rupees", gt=0)
    transaction_type: str = Field(..., description="Transaction type: 'payable' or 'receivable'")
    due_date: str = Field(..., description="Due date in YYYY-MM-DD format")
    current_cash_position: float = Field(..., description="Current cash balance in rupees", ge=0)
    upcoming_outflows: float = Field(0, description="Predicted outflows in next 30 days", ge=0)
    invoice_id: Optional[str] = Field(None, description="Invoice number for reference", max_length=100)
    
    @validator('counterparty_name')
    def validate_counterparty_name(cls, v):
        """Validate counterparty name"""
        if not v or not v.strip():
            raise ValueError('Counterparty name cannot be empty')
        return v.strip()
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        """Validate transaction type"""
        if v.lower() not in ['payable', 'receivable']:
            raise ValueError('Transaction type must be either "payable" or "receivable"')
        return v.lower()
    
    @validator('due_date')
    def validate_due_date(cls, v):
        """Validate due date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Due date must be in YYYY-MM-DD format')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount"""
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 100000000000:  # 10,000 crores limit
            raise ValueError('Amount exceeds maximum limit')
        return v

class GenerateDraftResponse(BaseModel):
    """Response model for negotiation email generation"""
    intent: str = Field(..., description="Negotiation strategy intent")
    strategy_explanation: str = Field(..., description="Explanation of the chosen strategy")
    whatsapp_message: str = Field(..., description="Brief WhatsApp message")
    formal_email: str = Field(..., description="Formal email content")
    option_a: str = Field(..., description="Relationship-focused option")
    option_b: str = Field(..., description="Transactional-focused option")
    processing_time: float = Field(..., description="Processing time in seconds")
    disclaimer: str = Field(..., description="Legal disclaimer for negotiation drafts")
    disclaimer_short: str = Field(..., description="Short disclaimer for UI")
    draft_only: bool = Field(default=True, description="Indicates this is a draft only, not sent")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str

@router.post("/generate-draft", response_model=GenerateDraftResponse)
async def generate_draft(request: Request, draft_request: GenerateDraftRequest):
    """
    Generate negotiation email draft using Agent D (Negotiator)
    
    This endpoint handles negotiation email generation with:
    - Router logic to determine negotiation strategy based on financial context
    - AI-powered content generation using Gemini Flash
    - A/B testing options (relationship-focused vs transactional)
    - Context-aware messaging for WhatsApp and formal email
    
    IMPORTANT: This endpoint ONLY generates drafts. It will NEVER automatically send emails.
    All generated content must be reviewed and approved by the user before sending.
    
    Args:
        draft_request: The negotiation parameters including counterparty, amount, and financial context
    
    Returns:
        GenerateDraftResponse: Negotiation strategy and generated content with A/B options
    
    Requirements: 1.3
    """
    start_time = datetime.now()
    
    # Enforce guardrails - check if email sending is allowed (it's not)
    can_send, reason = check_can_send_email()
    if not can_send:
        logger.info(f"Guardrail enforced: {reason}")
    
    try:
        logger.info(
            f"Processing negotiation draft request - "
            f"counterparty: {draft_request.counterparty_name}, "
            f"amount: ₹{draft_request.amount:,.0f}, "
            f"type: {draft_request.transaction_type}"
        )
        
        # Get MCP bridge from app state
        mcp_bridge: MCPBridge = request.app.state.mcp_bridge
        
        # Call Agent D via MCP bridge
        result = await mcp_bridge.call_agent_d(
            counterparty_name=draft_request.counterparty_name,
            amount=draft_request.amount,
            transaction_type=draft_request.transaction_type,
            due_date=draft_request.due_date,
            current_cash_position=draft_request.current_cash_position,
            upcoming_outflows=draft_request.upcoming_outflows,
            invoice_id=draft_request.invoice_id
        )
        
        # Extract the negotiation draft data from MCP result
        if not result.get("success"):
            error_msg = result.get("error", "MCP tool execution failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCP tool execution failed: {error_msg}"
            )
        
        negotiation_data = result["result"]
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Get disclaimer for negotiation
        disclaimer_data = get_negotiator_disclaimer()
        
        # Create response with disclaimer
        response = GenerateDraftResponse(
            intent=negotiation_data["intent"],
            strategy_explanation=negotiation_data["strategy_explanation"],
            whatsapp_message=negotiation_data["whatsapp_message"],
            formal_email=negotiation_data["formal_email"],
            option_a=negotiation_data["option_a"],
            option_b=negotiation_data["option_b"],
            processing_time=processing_time,
            disclaimer=disclaimer_data["disclaimer"],
            disclaimer_short=disclaimer_data["disclaimer_short"],
            draft_only=True  # Always true - enforced by guardrails
        )
        
        logger.info(
            f"Negotiation draft completed successfully in {processing_time:.2f}s - "
            f"Intent: {negotiation_data['intent']} (DRAFT ONLY - user approval required)"
        )
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions to avoid being caught by general handler
        raise
    except MCPBridgeError as e:
        logger.error(f"MCP Bridge error in generate_draft: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Negotiation draft generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in generate_draft: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during negotiation draft generation"
        )

@router.get("/health")
async def negotiator_health():
    """Health check endpoint for Negotiator router"""
    return {
        "status": "healthy",
        "agent": "Negotiator (Agent D)",
        "endpoints": ["/generate-draft"],
        "timestamp": datetime.now().isoformat()
    }

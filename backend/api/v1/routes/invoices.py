"""
Invoice Analysis API (Agent A - Visual Auditor)
Handles invoice upload, analysis, and fraud detection
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import base64
import io

router = APIRouter(prefix="/invoices", tags=["Invoices"])


class LineItem(BaseModel):
    """Invoice line item"""
    description: str
    amount: float
    category: str  # Capital Goods, Raw Material, Personal/Entertainment, Service


class InvoiceAnalysisResponse(BaseModel):
    """Invoice analysis response"""
    vendor_name: str
    invoice_date: Optional[str]
    total_amount: float
    tax_amount: float
    gstin: Optional[str]
    line_items: List[LineItem]
    is_handwritten: bool
    tampering_detected: bool
    compliance_flags: List[str]
    confidence_score: float
    is_valid_business_expense: bool
    summary: Optional[str]
    subsidy_alerts: Optional[List[str]] = None
    compliance_warnings: Optional[List[str]] = None


class InvoiceURLRequest(BaseModel):
    """Request for analyzing invoice from URL"""
    image_url: str


@router.post("/analyze", response_model=InvoiceAnalysisResponse)
async def analyze_invoice(
    file: UploadFile = File(..., description="Invoice image (PNG, JPG, PDF)")
):
    """
    Analyze uploaded invoice document
    
    Agent A (Visual Auditor) processes the invoice to:
    - Extract structured data (vendor, amounts, dates, GSTIN)
    - Categorize line items
    - Detect fraud indicators (tampering, handwriting)
    - Check compliance (ITC eligibility)
    - Trigger subsidy alerts for capital goods >₹1L
    """
    try:
        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Read file content
        contents = await file.read()
        
        # Process with Agent A
        from backend.agents.visual_auditor import analyze_invoice_content
        result = await analyze_invoice_content(contents, file.content_type)
        
        return InvoiceAnalysisResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze invoice: {str(e)}"
        )


@router.post("/analyze-url", response_model=InvoiceAnalysisResponse)
async def analyze_invoice_url(request: InvoiceURLRequest):
    """
    Analyze invoice from URL
    
    Processes invoice image from a publicly accessible URL
    """
    try:
        from backend.agents.visual_auditor import analyze_invoice_from_url
        result = await analyze_invoice_from_url(request.image_url)
        
        return InvoiceAnalysisResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze invoice from URL: {str(e)}"
        )


@router.post("/analyze-base64", response_model=InvoiceAnalysisResponse)
async def analyze_invoice_base64(
    image_data: str = Form(..., description="Base64 encoded image data"),
    content_type: str = Form("image/png", description="Image content type")
):
    """
    Analyze invoice from base64 encoded data
    
    Accepts base64 encoded image data for processing
    """
    try:
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        
        # Process with Agent A
        from backend.agents.visual_auditor import analyze_invoice_content
        result = await analyze_invoice_content(image_bytes, content_type)
        
        return InvoiceAnalysisResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze invoice: {str(e)}"
        )


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str):
    """
    Get invoice details by ID
    
    Retrieves stored invoice analysis results
    """
    # TODO: Implement database retrieval
    return {
        "success": True,
        "data": {
            "id": invoice_id,
            "status": "processed",
            "message": "Invoice retrieval not yet implemented"
        }
    }


@router.get("")
async def list_invoices(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None
):
    """
    List user invoices with pagination
    
    Optional status filter: pending, processed, flagged
    """
    # TODO: Implement database query
    return {
        "success": True,
        "data": {
            "invoices": [],
            "total": 0,
            "skip": skip,
            "limit": limit
        }
    }

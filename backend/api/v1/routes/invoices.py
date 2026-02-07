"""
Invoice API Routes
Visual Auditor - Agent A functionality
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from backend.agents.visual_auditor import VisualAuditor


router = APIRouter()
auditor = VisualAuditor()


# --- Schemas ---
class LineItem(BaseModel):
    description: str
    amount: float
    category: str


class InvoiceAnalysis(BaseModel):
    vendor_name: str
    invoice_date: Optional[str] = None
    total_amount: float
    tax_amount: float
    gstin: Optional[str] = None
    line_items: List[LineItem] = []
    is_handwritten: bool = False
    tampering_detected: bool = False
    confidence_score: float = 1.0
    compliance_flags: List[str] = []
    is_valid_business_expense: bool = True
    summary: Optional[str] = None


class InvoiceResponse(BaseModel):
    success: bool
    data: Optional[InvoiceAnalysis] = None
    error: Optional[str] = None


# --- Routes ---
@router.get("/")
async def list_invoices():
    """Get all invoices for current user"""
    # TODO: Implement with database
    return {"invoices": [], "total": 0}


@router.post("/analyze", response_model=InvoiceResponse)
async def analyze_invoice(file: UploadFile = File(...)):
    """
    Analyze an uploaded invoice using AI Vision
    Supports: PNG, JPG, PDF
    """
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Use PNG, JPG, or PDF."
        )
    
    try:
        # Read file contents
        contents = await file.read()
        
        # Analyze with Visual Auditor
        result = await auditor.analyze(contents, file.content_type)
        
        return InvoiceResponse(success=True, data=result)
    
    except Exception as e:
        return InvoiceResponse(success=False, error=str(e))


@router.post("/analyze-url")
async def analyze_invoice_url(image_url: str):
    """Analyze invoice from URL or base64 string"""
    try:
        result = await auditor.analyze_from_url(image_url)
        return InvoiceResponse(success=True, data=result)
    except Exception as e:
        return InvoiceResponse(success=False, error=str(e))


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str):
    """Get a specific invoice by ID"""
    # TODO: Implement with database
    return {"invoice_id": invoice_id, "status": "not_found"}

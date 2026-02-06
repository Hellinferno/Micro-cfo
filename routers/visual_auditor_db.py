"""
Visual Auditor Router with Database Integration
Handles Agent A (Visual Auditor) with PostgreSQL persistence
"""

import logging
import os
import uuid
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, date

from src.database import get_db
from src.models import Invoice
from crud import create_invoice, get_invoice, get_user_invoices, update_invoice
from middleware.authorization import get_current_user
from mcp_bridge import MCPBridge, MCPBridgeError
from src.file_validator import ComprehensiveFileValidator, FileValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/visual-auditor-db", tags=["Visual Auditor DB"])

# Request/Response Models
class InvoiceResponse(BaseModel):
    """Response model for invoice"""
    id: str
    invoice_number: Optional[str]
    vendor_name: Optional[str]
    invoice_date: Optional[date]
    due_date: Optional[date]
    total_amount: Optional[float]
    tax_amount: Optional[float]
    currency: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/scan", response_model=InvoiceResponse)
async def scan_and_save_invoice(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Scan invoice and save to database
    Combines Agent A processing with database persistence
    """
    try:
        # Validate file
        validator = ComprehensiveFileValidator()
        file_content = await file.read()
        
        try:
            validator.validate_file(
                file_content=file_content,
                filename=file.filename,
                content_type=file.content_type
            )
        except FileValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Save file
        file_id = str(uuid.uuid4())
        file_path = f"temp_uploads/{file_id}_{file.filename}"
        os.makedirs("temp_uploads", exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Process with MCP Bridge (async method with kwargs)
        import asyncio
        import base64
        bridge = MCPBridge()
        # Convert file content to base64 data URL for image_url parameter
        base64_content = base64.b64encode(file_content).decode('utf-8')
        image_url = f"data:application/octet-stream;base64,{base64_content}"
        result = asyncio.run(bridge.call_tool(
            'scan_invoice_document',
            image_url=image_url,
            use_mock=False
        ))
        
        invoice_data = result.get('invoice', {})
        
        # Parse dates
        invoice_date = None
        if invoice_data.get('invoice_date'):
            try:
                invoice_date = datetime.strptime(
                    invoice_data['invoice_date'], '%Y-%m-%d'
                ).date()
            except:
                pass
        
        # Create invoice in database
        invoice = create_invoice(
            db=db,
            user_id=uuid.UUID(current_user['user_id']),
            invoice_number=invoice_data.get('invoice_number'),
            vendor_name=invoice_data.get('vendor_name'),
            invoice_date=invoice_date,
            total_amount=invoice_data.get('total_amount'),
            tax_amount=invoice_data.get('tax_amount'),
            currency=invoice_data.get('currency', 'INR'),
            status='processed',
            file_path=file_path,
            extracted_data=invoice_data
        )
        
        return InvoiceResponse(
            id=str(invoice.id),
            invoice_number=invoice.invoice_number,
            vendor_name=invoice.vendor_name,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            total_amount=float(invoice.total_amount) if invoice.total_amount else None,
            tax_amount=float(invoice.tax_amount) if invoice.tax_amount else None,
            currency=invoice.currency,
            status=invoice.status,
            created_at=invoice.created_at
        )
        
    except MCPBridgeError as e:
        logger.error(f"MCP Bridge error: {e}")
        raise HTTPException(status_code=500, detail=f"Invoice processing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's invoices with optional filtering"""
    invoices = get_user_invoices(
        db=db,
        user_id=uuid.UUID(current_user['user_id']),
        status=status,
        limit=limit,
        offset=offset
    )
    
    return [
        InvoiceResponse(
            id=str(inv.id),
            invoice_number=inv.invoice_number,
            vendor_name=inv.vendor_name,
            invoice_date=inv.invoice_date,
            due_date=inv.due_date,
            total_amount=float(inv.total_amount) if inv.total_amount else None,
            tax_amount=float(inv.tax_amount) if inv.tax_amount else None,
            currency=inv.currency,
            status=inv.status,
            created_at=inv.created_at
        )
        for inv in invoices
    ]

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice_detail(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoice details"""
    invoice = get_invoice(db, uuid.UUID(invoice_id))
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if str(invoice.user_id) != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        vendor_name=invoice.vendor_name,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        total_amount=float(invoice.total_amount) if invoice.total_amount else None,
        tax_amount=float(invoice.tax_amount) if invoice.tax_amount else None,
        currency=invoice.currency,
        status=invoice.status,
        created_at=invoice.created_at
    )

@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice_status(
    invoice_id: str,
    status: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update invoice status"""
    invoice = get_invoice(db, uuid.UUID(invoice_id))
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if str(invoice.user_id) != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    invoice = update_invoice(db, uuid.UUID(invoice_id), status=status)
    
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        vendor_name=invoice.vendor_name,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        total_amount=float(invoice.total_amount) if invoice.total_amount else None,
        tax_amount=float(invoice.tax_amount) if invoice.tax_amount else None,
        currency=invoice.currency,
        status=invoice.status,
        created_at=invoice.created_at
    )

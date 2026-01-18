#!/usr/bin/env python3
"""
ERP Export Router for MicroCFO Integration Server
Handles invoice export to various ERP systems
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
from io import BytesIO

from erp_adapters import (
    InvoiceExportData,
    ERPExportManager,
    export_to_tally_xml,
    export_to_tally_csv,
    export_to_zoho_books,
    export_to_csv
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/erp-export", tags=["ERP Export"])


# Request/Response Models
class ExportRequest(BaseModel):
    """Request model for invoice export"""
    invoice_ids: List[str] = Field(..., description="List of invoice IDs to export", min_items=1)
    format: str = Field(..., description="Export format: tally_xml, tally_csv, zoho_books, csv, json")
    include_line_items: bool = Field(default=False, description="Include line item details (CSV only)")


class ExportResponse(BaseModel):
    """Response model for export operation"""
    success: bool
    message: str
    format: str
    file_name: str
    download_url: Optional[str] = None


class FormatInfoResponse(BaseModel):
    """Response model for format information"""
    format: str
    name: str
    description: str
    file_extension: str
    mime_type: str
    supports_batch: bool
    notes: str


@router.post("/export", response_model=ExportResponse)
async def export_invoices(request: Request, export_request: ExportRequest):
    """
    Export invoices to specified ERP format
    
    This endpoint exports processed invoices to various ERP systems:
    - Tally ERP 9 / Tally Prime (XML or CSV)
    - Zoho Books (JSON API payload)
    - Standard CSV/JSON for other systems
    
    Args:
        export_request: Export parameters including invoice IDs and format
    
    Returns:
        ExportResponse with download information
    
    Requirements: Phase 4 - API-First Design for ERPs
    """
    try:
        logger.info(
            f"Processing export request - "
            f"format: {export_request.format}, "
            f"invoices: {len(export_request.invoice_ids)}"
        )
        
        # Validate format
        if export_request.format not in ERPExportManager.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {export_request.format}. "
                       f"Supported: {', '.join(ERPExportManager.SUPPORTED_FORMATS)}"
            )
        
        # TODO: Fetch invoices from database
        # For now, create sample data
        invoices = []
        for inv_id in export_request.invoice_ids:
            # This would normally fetch from database
            invoice = InvoiceExportData(
                invoice_number=f"INV-{inv_id}",
                invoice_date=datetime.now().strftime("%Y-%m-%d"),
                vendor_name="Sample Vendor",
                vendor_gstin="27AABCU9603R1ZM",
                total_amount=11800.00,
                tax_amount=1800.00,
                taxable_amount=10000.00,
                line_items=[
                    {"description": "Sample Item", "amount": 10000.00, "category": "Materials"}
                ],
                payment_terms="Net 30",
                due_date=datetime.now().strftime("%Y-%m-%d")
            )
            invoices.append(invoice)
        
        # Validate batch support
        if len(invoices) > 1:
            format_info = ERPExportManager.get_format_info(export_request.format)
            if not format_info.get("supports_batch", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Format {export_request.format} does not support batch export"
                )
        
        # Generate export
        export_data = ERPExportManager.export(
            invoices,
            export_request.format,
            include_line_items=export_request.include_line_items
        )
        
        # Get format info for file naming
        format_info = ERPExportManager.get_format_info(export_request.format)
        file_extension = format_info.get("file_extension", ".txt")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"microcfo_export_{timestamp}{file_extension}"
        
        # Store export data temporarily (in production, use S3 or temp storage)
        # For now, return success with file info
        
        logger.info(f"Export completed successfully - {file_name}")
        
        return ExportResponse(
            success=True,
            message=f"Successfully exported {len(invoices)} invoice(s)",
            format=export_request.format,
            file_name=file_name,
            download_url=f"/api/v1/erp-export/download/{file_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/export/download")
async def download_export(request: Request, export_request: ExportRequest):
    """
    Export and immediately download invoices
    
    This endpoint exports invoices and returns the file for immediate download.
    
    Args:
        export_request: Export parameters
    
    Returns:
        StreamingResponse with exported file
    """
    try:
        logger.info(f"Processing download request - format: {export_request.format}")
        
        # Validate format
        if export_request.format not in ERPExportManager.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {export_request.format}"
            )
        
        # TODO: Fetch invoices from database
        invoices = []
        for inv_id in export_request.invoice_ids:
            invoice = InvoiceExportData(
                invoice_number=f"INV-{inv_id}",
                invoice_date=datetime.now().strftime("%Y-%m-%d"),
                vendor_name="Sample Vendor",
                vendor_gstin="27AABCU9603R1ZM",
                total_amount=11800.00,
                tax_amount=1800.00,
                taxable_amount=10000.00,
                line_items=[
                    {"description": "Sample Item", "amount": 10000.00, "category": "Materials"}
                ],
                payment_terms="Net 30",
                due_date=datetime.now().strftime("%Y-%m-%d")
            )
            invoices.append(invoice)
        
        # Generate export
        export_data = ERPExportManager.export(
            invoices,
            export_request.format,
            include_line_items=export_request.include_line_items
        )
        
        # Get format info
        format_info = ERPExportManager.get_format_info(export_request.format)
        file_extension = format_info.get("file_extension", ".txt")
        mime_type = format_info.get("mime_type", "text/plain")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"microcfo_export_{timestamp}{file_extension}"
        
        # Create file stream
        file_stream = BytesIO(export_data.encode('utf-8'))
        
        logger.info(f"Download ready - {file_name}")
        
        return StreamingResponse(
            file_stream,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


@router.get("/formats", response_model=List[FormatInfoResponse])
async def get_supported_formats():
    """
    Get list of supported export formats
    
    Returns information about all supported ERP export formats including:
    - Format name and description
    - File extension and MIME type
    - Batch support capability
    - Usage notes
    
    Returns:
        List of format information
    """
    formats = []
    
    for format_key in ERPExportManager.SUPPORTED_FORMATS:
        info = ERPExportManager.get_format_info(format_key)
        if info:
            formats.append(FormatInfoResponse(
                format=format_key,
                name=info["name"],
                description=info["description"],
                file_extension=info["file_extension"],
                mime_type=info["mime_type"],
                supports_batch=info["supports_batch"],
                notes=info["notes"]
            ))
    
    logger.info(f"Returned {len(formats)} supported formats")
    return formats


@router.get("/formats/{format}")
async def get_format_info(format: str):
    """
    Get detailed information about specific export format
    
    Args:
        format: Format identifier
    
    Returns:
        Format information dictionary
    """
    if format not in ERPExportManager.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Format not found: {format}"
        )
    
    info = ERPExportManager.get_format_info(format)
    return {
        "format": format,
        **info
    }


@router.get("/health")
async def erp_export_health():
    """Health check endpoint for ERP Export router"""
    return {
        "status": "healthy",
        "service": "ERP Export",
        "supported_formats": ERPExportManager.SUPPORTED_FORMATS,
        "timestamp": datetime.now().isoformat()
    }

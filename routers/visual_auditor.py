#!/usr/bin/env python3
"""
Visual Auditor Router for MicroCFO Integration Server
Handles Agent A (Visual Auditor) REST endpoints with S3 storage
"""

import logging
import os
import uuid
import base64
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Request, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db
from models import Invoice as InvoiceModel, WorkflowState

from mcp_bridge import MCPBridge, MCPBridgeError
from file_validator import (
    ComprehensiveFileValidator,
    FileValidationError,
    FileFormat
)
from s3_storage import get_s3_manager, is_s3_enabled
from legal_disclaimers import LegalDisclaimers, DisclaimerType, get_invoice_disclaimer

logger = logging.getLogger(__name__)

# Configuration for file uploads
TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (increased for large documents)
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png", 
    "image/jpeg",
    "image/jpg"
}
# Timeout settings for large file processing
UPLOAD_TIMEOUT = 300  # 5 minutes for large uploads
PROCESSING_TIMEOUT = 600  # 10 minutes for processing

# Check if S3 is enabled
USE_S3_STORAGE = is_s3_enabled()
if USE_S3_STORAGE:
    logger.info("✅ S3 storage enabled for file uploads")
else:
    logger.warning("S3 storage not configured, using local filesystem (NOT RECOMMENDED FOR PRODUCTION)")

# Create router
router = APIRouter(prefix="/agents/visual-auditor", tags=["Visual Auditor"])

# Request/Response Models
class ScanInvoiceRequest(BaseModel):
    """Request model for invoice scanning"""
    image_url: Optional[str] = Field(None, description="URL or base64 encoded image of the invoice")
    use_mock: bool = Field(False, description="Use mock data for testing")

class LineItemResponse(BaseModel):
    """Response model for invoice line items"""
    description: str
    amount: float
    category: str

class ScanInvoiceResponse(BaseModel):
    """Response model for invoice scanning"""
    vendor_name: str
    invoice_date: str
    total_amount: float
    tax_amount: float
    line_items: list[LineItemResponse]
    gstin: Optional[str] = None
    is_handwritten: bool = False
    tampering_detected: bool = False
    compliance_flags: list[str] = []
    confidence_score: float = 1.0
    processing_time: float = 0.0
    disclaimer: Optional[str] = None
    disclaimer_short: Optional[str] = None

class UploadDocumentResponse(BaseModel):
    """Response model for document upload"""
    success: bool
    message: str
    file_id: str
    filename: str
    file_size: int
    file_type: str
    invoice_data: Optional[ScanInvoiceResponse] = None

def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file type and size (basic checks before saving)
    
    This performs initial validation based on extension and MIME type.
    Comprehensive content-based validation is performed after file is saved.
    
    Args:
        file: The uploaded file
        
    Raises:
        HTTPException: If file validation fails
        
    Requirements: 1.4, 4.1, 4.5
    """
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file.size} bytes exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )
    
    # Check file extension
    if file.filename:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{file_ext}' not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type '{file.content_type}' not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )


def validate_file_content(file_path: Path, filename: Optional[str] = None) -> FileFormat:
    """
    Perform comprehensive content-based file validation.
    
    This validates the file based on its actual content (magic bytes) rather than
    just extension or MIME type, and performs format-specific structure validation.
    
    Args:
        file_path: Path to the saved file
        filename: Original filename for logging
        
    Returns:
        Detected FileFormat
        
    Raises:
        HTTPException: If validation fails
        
    Requirements: 4.5
    """
    try:
        detected_format = ComprehensiveFileValidator.validate_uploaded_file(
            file_path, filename
        )
        logger.info(f"File content validated: {filename} is {detected_format.value}")
        return detected_format
    except FileValidationError as e:
        logger.error(f"File validation failed for {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {str(e)}"
        )

def save_uploaded_file(file: UploadFile, report_progress=None) -> tuple[str, Path]:
    """
    Save uploaded file with secure UUID filename using streaming
    
    Implements streaming file upload for large documents with optional progress tracking.
    
    Args:
        file: The uploaded file
        report_progress: Optional async callback for progress updates (bytes_written, total_bytes)
        
    Returns:
        Tuple of (file_id, file_path)
        
    Requirements: 4.1, 4.2, 4.3, 6.4, 6.5
    """
    # Generate secure UUID filename
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    secure_filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / secure_filename
    
    # Stream file in chunks for large uploads
    bytes_written = 0
    with open(file_path, "wb") as buffer:
        while True:
            chunk = file.file.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer.write(chunk)
            bytes_written += len(chunk)
            
            # Report progress if callback provided
            if report_progress and callable(report_progress):
                # Note: This is synchronous, but we'll handle async in the caller
                pass
    
    logger.info(f"File saved: {secure_filename} ({bytes_written} bytes)")
    return file_id, file_path

def cleanup_temp_file(file_path: Path) -> None:
    """
    Clean up temporary file after processing
    
    Args:
        file_path: Path to the temporary file
        
    Requirements: 4.4
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary file {file_path}: {str(e)}")

def file_to_base64_url(file_path: Path) -> str:
    """
    Convert file to base64 data URL for MCP processing
    
    Args:
        file_path: Path to the file
        
    Returns:
        Base64 data URL string
    """
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # Determine MIME type based on extension
    file_ext = file_path.suffix.lower()
    if file_ext == ".pdf":
        mime_type = "application/pdf"
    elif file_ext in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif file_ext == ".png":
        mime_type = "image/png"
    else:
        mime_type = "application/octet-stream"
    
    # Create base64 data URL
    base64_content = base64.b64encode(file_content).decode('utf-8')
    return f"data:{mime_type};base64,{base64_content}"

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str

@router.post("/scan-invoice", response_model=ScanInvoiceResponse)
async def scan_invoice(request: Request, scan_request: ScanInvoiceRequest):
    """
    Scan invoice document using Agent A (Visual Auditor)
    
    This endpoint handles both image_url and use_mock scenarios:
    - image_url: URL or base64 encoded image of the invoice
    - use_mock: Returns mock data for testing purposes
    
    Requirements: 1.3, 4.1
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing invoice scan request - use_mock: {scan_request.use_mock}")
        
        # Get MCP bridge from app state
        mcp_bridge: MCPBridge = request.app.state.mcp_bridge
        
        # Call Agent A via MCP bridge
        result = await mcp_bridge.call_agent_a(
            image_url=scan_request.image_url or "",
            use_mock=scan_request.use_mock
        )
        
        # Extract the invoice data from MCP result
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MCP tool execution failed"
            )
        
        invoice_data = result["result"]
        
        # Self-Correction / Verification Loop
        # If confidence is low, we flag it for manual review (Simulated self-correction)
        confidence = invoice_data.get("confidence_score", 1.0)
        if confidence < 0.8:
            logger.warning(f"Low confidence score ({confidence}). Flagging for review.")
            if "compliance_flags" not in invoice_data:
                invoice_data["compliance_flags"] = []
            invoice_data["compliance_flags"].append("⚠️ Low Confidence - Manual Review Recommended")
        
        # --- Persistence Layer (The Memory) ---
        try:
            # Get DB session
            db: Session = request.state.db
            
            # 1. Create Invoice Record
            new_invoice = InvoiceModel(
                user_id=request.state.user.user_id if hasattr(request.state, "user") and request.state.user else None, # Handle anonymous for now
                vendor_name=invoice_data["vendor_name"],
                invoice_date=datetime.strptime(invoice_data["invoice_date"], "%Y-%m-%d").date() if invoice_data["invoice_date"] else None,
                total_amount=invoice_data["total_amount"],
                tax_amount=invoice_data["tax_amount"],
                status="processed",
                extracted_data=invoice_data # Store full JSON
            )
            
            # Handle anonymous user case (if auth not enforced yet)
            # In a real app, this would be strictly enforced.
            # For now, we skip saving if no user.
            if new_invoice.user_id:
                db.add(new_invoice)
                db.flush() # Get ID
                
                # 2. Update Workflow State (The Brain)
                workflow = WorkflowState(
                    invoice_id=new_invoice.id,
                    status="AUDIT_COMPLETE",
                    current_step="risk_analysis",
                    history=[{
                        "step": "visual_audit",
                        "timestamp": datetime.now().isoformat(),
                        "confidence": confidence,
                        "flags": invoice_data.get("compliance_flags", [])
                    }]
                )
                db.add(workflow)
                db.commit()
                logger.info(f"Persisted invoice {new_invoice.id} and workflow state")
                
        except Exception as db_err:
            logger.error(f"Failed to persist invoice data: {db_err}")
            # Don't block the response, just log error
        
        # Convert line items to response format
        line_items = []
        for item in invoice_data.get("line_items", []):
            line_items.append(LineItemResponse(
                description=item["description"],
                amount=item["amount"],
                category=item["category"]
            ))
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Get disclaimer for invoice processing
        disclaimer_data = get_invoice_disclaimer()
        
        # Create response with disclaimer
        response = ScanInvoiceResponse(
            vendor_name=invoice_data["vendor_name"],
            invoice_date=invoice_data["invoice_date"],
            total_amount=invoice_data["total_amount"],
            tax_amount=invoice_data["tax_amount"],
            line_items=line_items,
            gstin=invoice_data.get("gstin"),
            is_handwritten=invoice_data.get("is_handwritten", False),
            tampering_detected=invoice_data.get("tampering_detected", False),
            compliance_flags=invoice_data.get("compliance_flags", []),
            confidence_score=invoice_data.get("confidence_score", 1.0),
            processing_time=processing_time,
            disclaimer=disclaimer_data["disclaimer"],
            disclaimer_short=disclaimer_data["disclaimer_short"]
        )
        
        logger.info(f"Invoice scan completed successfully in {processing_time:.2f}s")
        return response
        
    except MCPBridgeError as e:
        logger.error(f"MCP Bridge error in scan_invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invoice processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in scan_invoice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during invoice processing"
        )

@router.post("/upload-document", response_model=UploadDocumentResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    process_immediately: bool = Form(True)
):
    """
    Upload and optionally process document using Agent A (Visual Auditor)
    
    This endpoint handles multipart form data for document uploads with:
    - Secure temporary file storage with UUID filenames
    - File type and size validation (PDF, PNG, JPG, JPEG)
    - Optional immediate processing via scan_invoice_document
    - Real-time progress updates via WebSocket
    
    Args:
        file: The uploaded document file
        process_immediately: Whether to process the document immediately (default: True)
    
    Requirements: 1.4, 4.1, 4.5, 3.2
    """
    file_path = None
    operation_id = None
    
    try:
        logger.info(f"Processing file upload: {file.filename} ({file.content_type})")
        
        # Get user context from request
        user_context = getattr(request.state, "user", None)
        user_id = user_context.user_id if user_context else "anonymous"
        
        # Create operation tracking if processing immediately
        if process_immediately:
            from operation_tracker import operation_tracker
            operation_id = operation_tracker.create_operation(
                user_id=user_id,
                operation_type="invoice_scan",
                initial_message="Starting document upload and processing"
            )
        
        # Validate file (basic checks)
        if operation_id:
            await operation_tracker.update_progress(
                operation_id, 10, "Validating file format and size"
            )
        validate_file(file)
        
        # Save file securely
        if operation_id:
            await operation_tracker.update_progress(
                operation_id, 20, "Saving file securely"
            )
        file_id, file_path = save_uploaded_file(file)
        
        # Perform comprehensive content-based validation
        if operation_id:
            await operation_tracker.update_progress(
                operation_id, 30, "Validating file content and structure"
            )
        detected_format = validate_file_content(file_path, file.filename)
        
        # Get file stats
        file_stats = file_path.stat()
        
        response_data = {
            "success": True,
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": file.filename or "unknown",
            "file_size": file_stats.st_size,
            "file_type": file.content_type or "unknown"
        }
        
        # Process immediately if requested
        if process_immediately:
            try:
                # Convert file to base64 data URL
                if operation_id:
                    await operation_tracker.update_progress(
                        operation_id, 40, "Converting file for processing"
                    )
                image_url = file_to_base64_url(file_path)
                
                # Get MCP bridge from app state
                mcp_bridge: MCPBridge = request.app.state.mcp_bridge
                
                # Call Agent A via MCP bridge
                if operation_id:
                    await operation_tracker.update_progress(
                        operation_id, 60, "Processing invoice with AI"
                    )
                result = await mcp_bridge.call_agent_a(
                    image_url=image_url,
                    use_mock=False
                )
                
                if result.get("success"):
                    invoice_data = result["result"]
                    
                    # Convert line items to response format
                    if operation_id:
                        await operation_tracker.update_progress(
                            operation_id, 80, "Formatting results"
                        )
                    line_items = []
                    for item in invoice_data.get("line_items", []):
                        line_items.append(LineItemResponse(
                            description=item["description"],
                            amount=item["amount"],
                            category=item["category"]
                        ))
                    
                    # Get disclaimer for invoice processing
                    disclaimer_data = get_invoice_disclaimer()
                    
                    # Add invoice data to response
                    response_data["invoice_data"] = ScanInvoiceResponse(
                        vendor_name=invoice_data["vendor_name"],
                        invoice_date=invoice_data["invoice_date"],
                        total_amount=invoice_data["total_amount"],
                        tax_amount=invoice_data["tax_amount"],
                        line_items=line_items,
                        gstin=invoice_data.get("gstin"),
                        is_handwritten=invoice_data.get("is_handwritten", False),
                        tampering_detected=invoice_data.get("tampering_detected", False),
                        compliance_flags=invoice_data.get("compliance_flags", []),
                        confidence_score=invoice_data.get("confidence_score", 1.0),
                        processing_time=0.0,  # Will be calculated by the MCP tool
                        disclaimer=disclaimer_data["disclaimer"],
                        disclaimer_short=disclaimer_data["disclaimer_short"]
                    )
                    
                    response_data["message"] = "File uploaded and processed successfully"
                    logger.info(f"File {file_id} processed successfully")
                    
                    # Complete operation
                    if operation_id:
                        await operation_tracker.complete_operation(
                            operation_id,
                            result={"file_id": file_id, "vendor": invoice_data["vendor_name"]},
                            message="Invoice processed successfully"
                        )
                else:
                    logger.warning(f"MCP processing failed for file {file_id}")
                    response_data["message"] = "File uploaded but processing failed"
                    
                    if operation_id:
                        await operation_tracker.fail_operation(
                            operation_id,
                            error="MCP processing returned unsuccessful result",
                            message="Processing failed"
                        )
                    
            except Exception as e:
                logger.error(f"Error processing uploaded file {file_id}: {str(e)}")
                response_data["message"] = f"File uploaded but processing failed: {str(e)}"
                
                if operation_id:
                    await operation_tracker.fail_operation(
                        operation_id,
                        error=str(e),
                        message="Processing failed with error"
                    )
        
        return UploadDocumentResponse(**response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        if file_path:
            cleanup_temp_file(file_path)
        if operation_id:
            from operation_tracker import operation_tracker
            await operation_tracker.fail_operation(
                operation_id,
                error="File validation failed",
                message="Upload failed"
            )
        raise
    except Exception as e:
        # Clean up file on unexpected errors
        if file_path:
            cleanup_temp_file(file_path)
        if operation_id:
            from operation_tracker import operation_tracker
            await operation_tracker.fail_operation(
                operation_id,
                error=str(e),
                message="Upload failed with unexpected error"
            )
        logger.error(f"Unexpected error in upload_document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during file upload"
        )
    finally:
        # Always clean up temporary file after processing
        if file_path and process_immediately:
            cleanup_temp_file(file_path)

@router.get("/health")
async def visual_auditor_health():
    """Health check endpoint for Visual Auditor router"""
    return {
        "status": "healthy",
        "agent": "Visual Auditor (Agent A)",
        "endpoints": ["/scan-invoice", "/upload-document"],
        "timestamp": datetime.now().isoformat()
    }
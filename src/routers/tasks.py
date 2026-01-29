"""
Task Management Router
Handles async task submission, status checking, and result retrieval
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any
from celery.result import AsyncResult
from src.celery_app import celery_app
from src.tasks import (
    scan_invoice_async,
    search_legal_compliance_async,
    search_subsidies_async,
    generate_negotiation_email_async
)
from src.middleware.auth import get_current_user, UserContext
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Request/Response Models
class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    submitted_at: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class LegalSearchRequest(BaseModel):
    query: str
    user_profile: Optional[Dict[str, Any]] = None

class SubsidySearchRequest(BaseModel):
    query: str
    user_profile: Optional[Dict[str, Any]] = None

class NegotiationEmailRequest(BaseModel):
    invoice_data: Dict[str, Any]
    negotiation_context: Dict[str, Any]

# Helper function to get task status
def get_task_info(task_id: str) -> TaskStatusResponse:
    """Get detailed task status and result"""
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = TaskStatusResponse(
        task_id=task_id,
        status=task_result.state,
        meta=task_result.info if isinstance(task_result.info, dict) else None
    )
    
    if task_result.state == 'PENDING':
        response.status = 'pending'
        response.meta = {'status': 'Task is waiting to be processed'}
    
    elif task_result.state == 'PROCESSING':
        response.status = 'processing'
        if isinstance(task_result.info, dict):
            response.progress = task_result.info.get('progress', 0)
            response.meta = task_result.info
    
    elif task_result.state == 'SUCCESS':
        response.status = 'success'
        response.progress = 100
        response.result = task_result.result
    
    elif task_result.state == 'FAILURE':
        response.status = 'failed'
        response.error = str(task_result.info)
    
    elif task_result.state == 'RETRY':
        response.status = 'retrying'
        response.meta = {'status': 'Task is being retried after failure'}
    
    return response

# Endpoints

@router.post("/invoice/scan", response_model=TaskResponse)
async def submit_invoice_scan(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit invoice for async scanning
    Returns task ID for status tracking
    """
    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = f"temp_uploads/{file_id}_{file.filename}"
        
        os.makedirs("temp_uploads", exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Submit task to Celery
        task = scan_invoice_async.apply_async(
            args=[file_path, current_user.get('user_id')],
            task_id=file_id
        )
        
        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message="Invoice scan submitted for processing",
            submitted_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")

@router.post("/legal/search", response_model=TaskResponse)
async def submit_legal_search(
    request: LegalSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit legal compliance search
    Returns task ID for status tracking
    """
    try:
        task = search_legal_compliance_async.apply_async(
            args=[request.query, request.user_profile]
        )
        
        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message="Legal search submitted for processing",
            submitted_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")

@router.post("/subsidy/search", response_model=TaskResponse)
async def submit_subsidy_search(
    request: SubsidySearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit subsidy search
    Returns task ID for status tracking
    """
    try:
        task = search_subsidies_async.apply_async(
            args=[request.query, request.user_profile]
        )
        
        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message="Subsidy search submitted for processing",
            submitted_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")

@router.post("/negotiation/email", response_model=TaskResponse)
async def submit_negotiation_email(
    request: NegotiationEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit negotiation email generation
    Returns task ID for status tracking
    """
    try:
        task = generate_negotiation_email_async.apply_async(
            args=[request.invoice_data, request.negotiation_context]
        )
        
        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message="Email generation submitted for processing",
            submitted_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of a submitted task
    Poll this endpoint to check task progress
    """
    try:
        return get_task_info(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.get("/result/{task_id}")
async def get_task_result(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get result of a completed task
    Returns 404 if task is not complete
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "status": "success",
                "result": task_result.result
            }
        elif task_result.state == 'FAILURE':
            raise HTTPException(status_code=500, detail=f"Task failed: {task_result.info}")
        else:
            raise HTTPException(status_code=404, detail=f"Task not complete. Current status: {task_result.state}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task result: {str(e)}")

@router.delete("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a running task
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancellation requested"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")

@router.get("/queue/stats")
async def get_queue_stats(current_user: dict = Depends(get_current_user)):
    """
    Get statistics about task queues
    Admin endpoint for monitoring
    """
    try:
        inspect = celery_app.control.inspect()
        
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        return {
            "active_tasks": active_tasks or {},
            "scheduled_tasks": scheduled_tasks or {},
            "reserved_tasks": reserved_tasks or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")

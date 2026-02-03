"""
Celery tasks for Visual Auditor (Agent A)
Handles async invoice scanning and document processing
"""

from celery_app import celery_app
from mcp_bridge import MCPBridge
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    name='tasks.visual_auditor_tasks.scan_invoice_async',
    max_retries=3,
    default_retry_delay=60
)
def scan_invoice_async(self, file_path: str, user_id: str = None):
    """
    Async task to scan invoice document
    
    Args:
        file_path: Path to uploaded invoice file
        user_id: Optional user ID for tracking
        
    Returns:
        dict: Extracted invoice data
    """
    try:
        logger.info(f"Starting invoice scan for file: {file_path}")
        
        # Update task state to PROCESSING
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Analyzing invoice document...',
                'progress': 10,
                'started_at': datetime.utcnow().isoformat()
            }
        )
        
        # Initialize MCP Bridge
        bridge = MCPBridge()
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Extracting text from document...',
                'progress': 30
            }
        )
        
        # Call MCP tool for invoice scanning (async method with kwargs)
        import asyncio
        # Convert file content to base64 data URL for image_url parameter
        import base64
        base64_content = base64.b64encode(file_content).decode('utf-8')
        image_url = f"data:application/octet-stream;base64,{base64_content}"
        result = asyncio.run(bridge.call_tool(
            'scan_invoice_document',
            image_url=image_url,
            use_mock=False
        ))
        
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Validating extracted data...',
                'progress': 70
            }
        )
        
        # Parse and validate result
        invoice_data = result.get('invoice', {})
        
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Finalizing results...',
                'progress': 90
            }
        )
        
        logger.info(f"Invoice scan completed successfully for file: {file_path}")
        
        return {
            'status': 'success',
            'invoice': invoice_data,
            'file_path': file_path,
            'user_id': user_id,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except FileNotFoundError as exc:
        logger.error(f"File not found: {file_path}")
        # Don't retry for missing files
        return {
            'status': 'error',
            'error': f'File not found: {file_path}',
            'file_path': file_path,
            'user_id': user_id,
            'failed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Invoice scan failed: {exc}")
        
        # Retry on failure
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        # Final failure
        return {
            'status': 'error',
            'error': str(exc),
            'file_path': file_path,
            'user_id': user_id,
            'failed_at': datetime.utcnow().isoformat()
        }

@celery_app.task(
    bind=True,
    name='tasks.visual_auditor_tasks.batch_scan_invoices',
    max_retries=2
)
def batch_scan_invoices(self, file_paths: list, user_id: str = None):
    """
    Async task to scan multiple invoices in batch
    
    Args:
        file_paths: List of file paths to scan
        user_id: Optional user ID for tracking
        
    Returns:
        dict: Results for all scanned invoices
    """
    try:
        logger.info(f"Starting batch scan for {len(file_paths)} invoices")
        
        results = []
        total = len(file_paths)
        
        for idx, file_path in enumerate(file_paths):
            # Update progress
            progress = int((idx / total) * 100)
            self.update_state(
                state='PROCESSING',
                meta={
                    'status': f'Processing invoice {idx + 1} of {total}',
                    'progress': progress,
                    'completed': idx,
                    'total': total
                }
            )
            
            # Scan individual invoice
            result = scan_invoice_async.apply_async(
                args=[file_path, user_id],
                countdown=idx * 2  # Stagger requests
            )
            
            results.append({
                'file_path': file_path,
                'task_id': result.id
            })
        
        return {
            'status': 'success',
            'total_invoices': total,
            'results': results,
            'user_id': user_id
        }
        
    except Exception as exc:
        logger.error(f"Batch scan failed: {exc}")
        return {
            'status': 'error',
            'error': str(exc),
            'user_id': user_id
        }

"""
Celery tasks for Negotiator (Agent D)
Handles async email generation for vendor negotiations
"""

from celery_app import celery_app
from mcp_bridge import MCPBridge
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    name='tasks.negotiator_tasks.generate_negotiation_email_async',
    max_retries=2,
    default_retry_delay=20
)
def generate_negotiation_email_async(self, invoice_data: dict, negotiation_context: dict):
    """
    Async task to generate professional negotiation email
    
    Args:
        invoice_data: Invoice information
        negotiation_context: Context for negotiation (reason, tone, etc.)
        
    Returns:
        dict: Generated email content
    """
    try:
        logger.info(f"Generating negotiation email for invoice: {invoice_data.get('invoice_number')}")
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Analyzing invoice details...',
                'progress': 25
            }
        )
        
        bridge = MCPBridge()
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Generating email content...',
                'progress': 50
            }
        )
        
        # Call MCP tool for email generation (async method with kwargs)
        # Tool name is 'generate_negotiation_draft'
        import asyncio
        result = asyncio.run(bridge.call_tool(
            'generate_negotiation_draft',
            counterparty_name=invoice_data.get('vendor_name', 'Vendor'),
            amount=invoice_data.get('total_amount', 0),
            transaction_type=negotiation_context.get('transaction_type', 'payable'),
            due_date=negotiation_context.get('due_date', '2026-03-01'),
            current_cash_position=negotiation_context.get('cash_position', 100000),
            upcoming_outflows=negotiation_context.get('upcoming_outflows', 0),
            invoice_id=invoice_data.get('invoice_number')
        ))
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Finalizing email...',
                'progress': 90
            }
        )
        
        email_content = result.get('email', '')
        
        logger.info("Negotiation email generated successfully")
        
        return {
            'status': 'success',
            'email': email_content,
            'invoice_number': invoice_data.get('invoice_number'),
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Email generation failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'status': 'error',
            'error': str(exc),
            'invoice_number': invoice_data.get('invoice_number'),
            'failed_at': datetime.utcnow().isoformat()
        }

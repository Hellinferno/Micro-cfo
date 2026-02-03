"""
Celery tasks for Legal Sentinel (Agent B)
Handles async legal compliance searches and monitoring
"""

from celery_app import celery_app
from mcp_bridge import MCPBridge
from sentinel_monitor import LegalSentinel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    name='tasks.legal_sentinel_tasks.search_legal_compliance_async',
    max_retries=3,
    default_retry_delay=30
)
def search_legal_compliance_async(self, query: str, user_profile: dict = None):
    """
    Async task to search legal compliance information
    
    Args:
        query: Legal compliance query
        user_profile: User business profile for filtering
        
    Returns:
        dict: Legal compliance search results
    """
    try:
        logger.info(f"Starting legal compliance search: {query}")
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Searching legal database...',
                'progress': 20
            }
        )
        
        # Initialize MCP Bridge
        bridge = MCPBridge()
        
        # Call MCP tool for legal search (async method with kwargs)
        # Tool name is 'check_compliance_law', args are 'query' and 'user_context'
        import asyncio
        result = asyncio.run(bridge.call_tool(
            'check_compliance_law',
            query=query,
            user_context=str(user_profile) if user_profile else ""
        ))
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Analyzing legal provisions...',
                'progress': 60
            }
        )
        
        # Extract and format results
        legal_info = result.get('legal_info', [])
        risk_level = result.get('risk_level', 'UNKNOWN')
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Generating compliance report...',
                'progress': 90
            }
        )
        
        logger.info(f"Legal search completed: {len(legal_info)} results found")
        
        return {
            'status': 'success',
            'query': query,
            'legal_info': legal_info,
            'risk_level': risk_level,
            'result_count': len(legal_info),
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Legal search failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'status': 'error',
            'error': str(exc),
            'query': query,
            'failed_at': datetime.utcnow().isoformat()
        }

@celery_app.task(
    bind=True,
    name='tasks.legal_sentinel_tasks.monitor_legal_updates',
    max_retries=2
)
def monitor_legal_updates(self):
    """
    Periodic task to monitor government websites for legal updates
    Runs every 6 hours via Celery Beat
    
    Returns:
        dict: Monitoring results with new notifications
    """
    try:
        logger.info("Starting legal updates monitoring")
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Checking government websites...',
                'progress': 10
            }
        )
        
        # Initialize Legal Sentinel
        sentinel = LegalSentinel()
        
        # Check for updates
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Scraping CBIC website...',
                'progress': 30
            }
        )
        
        notifications = sentinel.check_for_updates()
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Processing notifications...',
                'progress': 70
            }
        )
        
        # Send notifications to relevant users
        sent_count = 0
        for notification in notifications:
            # Here you would send WhatsApp/email notifications
            # For now, just log
            logger.info(f"New legal update: {notification.get('title')}")
            sent_count += 1
        
        logger.info(f"Monitoring completed: {sent_count} notifications sent")
        
        return {
            'status': 'success',
            'notifications_found': len(notifications),
            'notifications_sent': sent_count,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Legal monitoring failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'status': 'error',
            'error': str(exc),
            'failed_at': datetime.utcnow().isoformat()
        }

@celery_app.task(
    bind=True,
    name='tasks.legal_sentinel_tasks.analyze_compliance_risk',
    max_retries=2
)
def analyze_compliance_risk(self, invoice_data: dict, user_profile: dict):
    """
    Async task to analyze compliance risk for an invoice
    
    Args:
        invoice_data: Extracted invoice information
        user_profile: User business profile
        
    Returns:
        dict: Risk analysis results
    """
    try:
        logger.info("Starting compliance risk analysis")
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Analyzing invoice compliance...',
                'progress': 25
            }
        )
        
        bridge = MCPBridge()
        
        # Analyze GST compliance
        gst_result = bridge.call_tool(
            'search_legal_compliance',
            {
                'query': f"GST compliance for {invoice_data.get('vendor_name')} invoice amount {invoice_data.get('total_amount')}",
                'user_profile': user_profile
            }
        )
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Checking tax implications...',
                'progress': 75
            }
        )
        
        return {
            'status': 'success',
            'invoice_id': invoice_data.get('invoice_number'),
            'risk_level': gst_result.get('risk_level', 'UNKNOWN'),
            'compliance_issues': gst_result.get('legal_info', []),
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Risk analysis failed: {exc}")
        return {
            'status': 'error',
            'error': str(exc),
            'failed_at': datetime.utcnow().isoformat()
        }

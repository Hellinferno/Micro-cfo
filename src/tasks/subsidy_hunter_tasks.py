"""
Celery tasks for Subsidy Hunter (Agent C)
Handles async subsidy and scheme searches
"""

from src.celery_app import celery_app
from src.mcp_bridge import MCPBridge
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    name='tasks.subsidy_hunter_tasks.search_subsidies_async',
    max_retries=3,
    default_retry_delay=30
)
def search_subsidies_async(self, query: str, user_profile: dict = None):
    """
    Async task to search for government subsidies and schemes
    
    Args:
        query: Subsidy search query
        user_profile: User business profile for filtering
        
    Returns:
        dict: Subsidy search results
    """
    try:
        logger.info(f"Starting subsidy search: {query}")
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Searching subsidy database...',
                'progress': 20
            }
        )
        
        bridge = MCPBridge()
        
        result = bridge.call_tool(
            'search_subsidies',
            {
                'query': query,
                'user_profile': user_profile or {}
            }
        )
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Filtering relevant schemes...',
                'progress': 60
            }
        )
        
        schemes = result.get('schemes', [])
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Calculating eligibility...',
                'progress': 90
            }
        )
        
        logger.info(f"Subsidy search completed: {len(schemes)} schemes found")
        
        return {
            'status': 'success',
            'query': query,
            'schemes': schemes,
            'result_count': len(schemes),
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Subsidy search failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'status': 'error',
            'error': str(exc),
            'query': query,
            'failed_at': datetime.utcnow().isoformat()
        }

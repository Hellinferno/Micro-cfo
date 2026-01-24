"""
Celery Application Configuration for MicroCFO
Handles async task processing for heavy AI operations
"""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Queue
import logging
import os
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis configuration
# Redis configuration
# Fallback to memory broker if Redis is not configured (for development without Redis)
REDIS_URL = os.getenv('REDIS_URL', 'memory://')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'rpc://')

# Create Celery app
celery_app = Celery(
    'microcfo',
    broker=REDIS_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        'tasks.visual_auditor_tasks',
        'tasks.legal_sentinel_tasks',
        'tasks.subsidy_hunter_tasks',
        'tasks.negotiator_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'tasks.visual_auditor_tasks.*': {'queue': 'visual_auditor'},
        'tasks.legal_sentinel_tasks.*': {'queue': 'legal_sentinel'},
        'tasks.subsidy_hunter_tasks.*': {'queue': 'subsidy_hunter'},
        'tasks.negotiator_tasks.*': {'queue': 'negotiator'},
    },
    
    # Task queues
    task_queues=(
        Queue('visual_auditor', routing_key='visual_auditor'),
        Queue('legal_sentinel', routing_key='legal_sentinel'),
        Queue('subsidy_hunter', routing_key='subsidy_hunter'),
        Queue('negotiator', routing_key='negotiator'),
        Queue('default', routing_key='default'),
    ),
    
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Task execution limits
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    
    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'monitor-legal-updates': {
            'task': 'tasks.legal_sentinel_tasks.monitor_legal_updates',
            'schedule': timedelta(hours=6),  # Every 6 hours
        },
        'cleanup-old-tasks': {
            'task': 'tasks.maintenance_tasks.cleanup_old_results',
            'schedule': timedelta(hours=24),  # Daily
        },
    },
)

# Task lifecycle hooks
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log when task starts"""
    logger.info(f"Task {task.name} [{task_id}] started")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra):
    """Log when task completes"""
    logger.info(f"Task {task.name} [{task_id}] completed successfully")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, **extra):
    """Log when task fails"""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}")

if __name__ == '__main__':
    celery_app.start()

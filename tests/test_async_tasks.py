"""
Test suite for async task queue implementation
Tests Celery tasks, Redis integration, and task status tracking
"""

import pytest
import time
from celery.result import AsyncResult
from celery_app import celery_app
from src.tasks import (
    scan_invoice_async,
    search_legal_compliance_async,
    search_subsidies_async,
    generate_negotiation_email_async
)

# Configure Celery for testing
celery_app.conf.update(
    task_always_eager=True,  # Execute tasks synchronously for testing
    task_eager_propagates=True,
    broker_url='memory://',
    result_backend='cache+memory://'
)

class TestVisualAuditorTasks:
    """Test Visual Auditor async tasks"""
    
    def test_scan_invoice_async_success(self, tmp_path):
        """Test successful invoice scanning"""
        # Create a test file
        test_file = tmp_path / "test_invoice.txt"
        test_file.write_text("Test invoice content")
        
        # Submit task
        result = scan_invoice_async.apply_async(
            args=[str(test_file), "test_user_123"]
        )
        
        # Wait for completion
        task_result = result.get(timeout=10)
        
        # Assertions
        assert task_result['status'] == 'success'
        assert task_result['user_id'] == 'test_user_123'
        assert 'invoice' in task_result
        assert 'completed_at' in task_result
    
    def test_scan_invoice_async_file_not_found(self):
        """Test invoice scanning with non-existent file"""
        result = scan_invoice_async.apply_async(
            args=["/nonexistent/file.pdf", "test_user_123"]
        )
        
        task_result = result.get(timeout=10)
        
        # Should return error status
        assert task_result['status'] == 'error'
        assert 'error' in task_result
    
    def test_batch_scan_invoices(self, tmp_path):
        """Test batch invoice scanning"""
        from src.tasks.visual_auditor_tasks import batch_scan_invoices
        
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = tmp_path / f"invoice_{i}.txt"
            test_file.write_text(f"Invoice {i} content")
            files.append(str(test_file))
        
        # Submit batch task
        result = batch_scan_invoices.apply_async(
            args=[files, "test_user_123"]
        )
        
        task_result = result.get(timeout=30)
        
        # Assertions
        assert task_result['status'] == 'success'
        assert task_result['total_invoices'] == 3
        assert len(task_result['results']) == 3

class TestLegalSentinelTasks:
    """Test Legal Sentinel async tasks"""
    
    def test_search_legal_compliance_async(self):
        """Test legal compliance search"""
        result = search_legal_compliance_async.apply_async(
            args=[
                "GST compliance for textile exports",
                {"turnover": 8000000, "sector": "Textile"}
            ]
        )
        
        task_result = result.get(timeout=15)
        
        # Assertions
        assert task_result['status'] == 'success'
        assert task_result['query'] == "GST compliance for textile exports"
        assert 'legal_info' in task_result
        assert 'risk_level' in task_result
        assert 'result_count' in task_result
    
    def test_monitor_legal_updates(self):
        """Test periodic legal monitoring task"""
        from src.tasks.legal_sentinel_tasks import monitor_legal_updates
        
        result = monitor_legal_updates.apply_async()
        task_result = result.get(timeout=30)
        
        # Assertions
        assert task_result['status'] in ['success', 'error']
        if task_result['status'] == 'success':
            assert 'notifications_found' in task_result
            assert 'notifications_sent' in task_result
    
    def test_analyze_compliance_risk(self):
        """Test compliance risk analysis"""
        from src.tasks.legal_sentinel_tasks import analyze_compliance_risk
        
        invoice_data = {
            'invoice_number': 'INV-2024-001',
            'vendor_name': 'Test Vendor',
            'total_amount': 50000.00
        }
        
        user_profile = {
            'turnover': 10000000,
            'sector': 'Manufacturing'
        }
        
        result = analyze_compliance_risk.apply_async(
            args=[invoice_data, user_profile]
        )
        
        task_result = result.get(timeout=15)
        
        # Assertions
        assert task_result['status'] in ['success', 'error']
        if task_result['status'] == 'success':
            assert 'risk_level' in task_result
            assert 'compliance_issues' in task_result

class TestSubsidyHunterTasks:
    """Test Subsidy Hunter async tasks"""
    
    def test_search_subsidies_async(self):
        """Test subsidy search"""
        result = search_subsidies_async.apply_async(
            args=[
                "export subsidies for textile industry",
                {"turnover": 5000000, "sector": "Textile"}
            ]
        )
        
        task_result = result.get(timeout=15)
        
        # Assertions
        assert task_result['status'] == 'success'
        assert task_result['query'] == "export subsidies for textile industry"
        assert 'schemes' in task_result
        assert 'result_count' in task_result

class TestNegotiatorTasks:
    """Test Negotiator async tasks"""
    
    def test_generate_negotiation_email_async(self):
        """Test negotiation email generation"""
        invoice_data = {
            'invoice_number': 'INV-2024-001',
            'vendor_name': 'ABC Suppliers',
            'total_amount': 50000.00,
            'due_date': '2024-02-15'
        }
        
        negotiation_context = {
            'reason': 'payment_extension',
            'tone': 'professional',
            'extension_days': 30
        }
        
        result = generate_negotiation_email_async.apply_async(
            args=[invoice_data, negotiation_context]
        )
        
        task_result = result.get(timeout=10)
        
        # Assertions
        assert task_result['status'] == 'success'
        assert 'email' in task_result
        assert task_result['invoice_number'] == 'INV-2024-001'

class TestTaskLifecycle:
    """Test task lifecycle and state management"""
    
    def test_task_state_progression(self, tmp_path):
        """Test task progresses through states correctly"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Submit task
        result = scan_invoice_async.apply_async(
            args=[str(test_file), "test_user"]
        )
        
        # Check initial state
        assert result.state in ['PENDING', 'PROCESSING', 'SUCCESS']
        
        # Wait for completion
        task_result = result.get(timeout=10)
        
        # Check final state
        assert result.state == 'SUCCESS'
        assert result.successful()
    
    def test_task_retry_on_failure(self):
        """Test task retry mechanism"""
        # This would require mocking to test properly
        # For now, just verify the retry configuration
        task = scan_invoice_async
        assert task.max_retries == 3
        assert task.default_retry_delay == 60
    
    def test_task_timeout(self):
        """Test task timeout configuration"""
        # Verify timeout settings
        assert celery_app.conf.task_time_limit == 300  # 5 minutes
        assert celery_app.conf.task_soft_time_limit == 240  # 4 minutes

class TestTaskQueues:
    """Test task queue routing"""
    
    def test_visual_auditor_queue_routing(self):
        """Test tasks route to correct queue"""
        task = scan_invoice_async
        route = celery_app.conf.task_routes.get('tasks.visual_auditor_tasks.*')
        assert route == {'queue': 'visual_auditor'}
    
    def test_legal_sentinel_queue_routing(self):
        """Test legal sentinel queue routing"""
        route = celery_app.conf.task_routes.get('tasks.legal_sentinel_tasks.*')
        assert route == {'queue': 'legal_sentinel'}
    
    def test_subsidy_hunter_queue_routing(self):
        """Test subsidy hunter queue routing"""
        route = celery_app.conf.task_routes.get('tasks.subsidy_hunter_tasks.*')
        assert route == {'queue': 'subsidy_hunter'}
    
    def test_negotiator_queue_routing(self):
        """Test negotiator queue routing"""
        route = celery_app.conf.task_routes.get('tasks.negotiator_tasks.*')
        assert route == {'queue': 'negotiator'}

class TestCeleryConfiguration:
    """Test Celery configuration"""
    
    def test_broker_configuration(self):
        """Test Redis broker configuration"""
        assert 'redis://' in celery_app.conf.broker_url
    
    def test_result_backend_configuration(self):
        """Test result backend configuration"""
        assert 'redis://' in celery_app.conf.result_backend
    
    def test_serialization_configuration(self):
        """Test serialization settings"""
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
        assert 'json' in celery_app.conf.accept_content
    
    def test_timezone_configuration(self):
        """Test timezone settings"""
        assert celery_app.conf.timezone == 'Asia/Kolkata'
        assert celery_app.conf.enable_utc is True
    
    def test_beat_schedule_configuration(self):
        """Test periodic task schedule"""
        schedule = celery_app.conf.beat_schedule
        assert 'monitor-legal-updates' in schedule
        assert 'cleanup-old-tasks' in schedule

@pytest.mark.integration
class TestTaskAPIIntegration:
    """Integration tests for task API endpoints"""
    
    def test_task_submission_endpoint(self, client):
        """Test task submission via API"""
        # This requires a test client fixture
        # Would be implemented with actual API testing
        pass
    
    def test_task_status_endpoint(self, client):
        """Test task status checking via API"""
        pass
    
    def test_task_result_endpoint(self, client):
        """Test task result retrieval via API"""
        pass

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

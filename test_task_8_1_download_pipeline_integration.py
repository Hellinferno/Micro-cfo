"""
Integration Test for Complete Download Pipeline (Task 8.1)

This test validates the complete download pipeline from start to finish,
including idempotency and file validation.

Validates Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.seed_downloader import (
    SeedDownloader,
    LegalDocumentSource,
    LEGAL_SOURCES
)


class TestDownloadPipelineIntegration:
    """Integration tests for complete download pipeline"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test downloads"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_pdf_content(self):
        """Mock PDF content for testing"""
        # Minimal valid PDF structure
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
    
    @pytest.fixture
    def downloader(self, temp_dir):
        """Create downloader instance with temp directory"""
        return SeedDownloader(output_dir=temp_dir)
    
    def test_complete_download_pipeline_with_mocks(self, downloader, temp_dir, mock_pdf_content):
        """
        Test complete download pipeline with all 5 configured documents.
        
        This test validates:
        - All 5 documents are attempted for download
        - Files are saved to correct location
        - Files are valid PDFs
        - Success/failure tracking works
        
        Validates Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8
        """
        # Mock successful responses for all sources
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            # Download all configured sources
            results = downloader.download_all(LEGAL_SOURCES)
            
            # Verify all 5 documents were attempted
            assert len(results) == 5, "Should attempt to download all 5 configured documents"
            
            # Verify all downloads succeeded
            assert all(results.values()), "All downloads should succeed with mocked responses"
            
            # Verify files exist in correct location
            for source in LEGAL_SOURCES:
                file_path = Path(temp_dir) / source.filename
                assert file_path.exists(), f"File should exist: {source.filename}"
                
                # Verify file is not empty
                assert file_path.stat().st_size > 0, f"File should not be empty: {source.filename}"
                
                # Verify file starts with PDF header
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    assert header == b'%PDF', f"File should be valid PDF: {source.filename}"
    
    def test_download_idempotency(self, downloader, temp_dir, mock_pdf_content):
        """
        Test that re-running download doesn't re-download existing files.
        
        This test validates:
        - Files already present are skipped
        - Existing files are not modified
        - Idempotency works correctly
        
        Validates Requirements: 1.7, 8.1
        """
        # Create a test source
        test_source = LegalDocumentSource(
            url="https://example.gov.in/test.pdf",
            filename="test_document.pdf",
            description="Test Document",
            law_type="GST"
        )
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            # First download
            result1 = downloader.download_document(test_source)
            assert result1 is True, "First download should succeed"
            
            # Verify file exists
            file_path = Path(temp_dir) / test_source.filename
            assert file_path.exists(), "File should exist after first download"
            
            # Get file modification time
            first_mtime = file_path.stat().st_mtime
            
            # Reset mock call count
            mock_get.reset_mock()
            
            # Second download (should skip)
            result2 = downloader.download_document(test_source)
            assert result2 is True, "Second download should succeed (skip)"
            
            # Verify no network request was made
            mock_get.assert_not_called()
            
            # Verify file was not modified
            second_mtime = file_path.stat().st_mtime
            assert first_mtime == second_mtime, "File should not be modified on second download"
    
    def test_download_location_consistency(self, downloader, temp_dir, mock_pdf_content):
        """
        Test that all downloads go to the configured output directory.
        
        Validates Requirement: 1.6
        """
        test_sources = [
            LegalDocumentSource(
                url=f"https://example.gov.in/doc{i}.pdf",
                filename=f"document_{i}.pdf",
                description=f"Test Document {i}",
                law_type="GST"
            )
            for i in range(3)
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            results = downloader.download_all(test_sources)
            
            # Verify all files are in the correct directory
            for source in test_sources:
                file_path = Path(temp_dir) / source.filename
                assert file_path.exists(), f"File should be in output directory: {source.filename}"
                assert file_path.parent == Path(temp_dir), "File should be directly in output directory"
    
    def test_download_logging_completeness(self, downloader, temp_dir, mock_pdf_content, caplog):
        """
        Test that successful downloads are logged with filename and size.
        
        Validates Requirement: 1.8
        """
        import logging
        caplog.set_level(logging.INFO)
        
        test_source = LegalDocumentSource(
            url="https://example.gov.in/test.pdf",
            filename="test_document.pdf",
            description="Test Document",
            law_type="GST"
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            result = downloader.download_document(test_source)
            assert result is True
            
            # Check that log contains filename
            assert any(test_source.filename in record.message for record in caplog.records), \
                "Log should contain filename"
            
            # Check that log contains file size
            file_size = len(mock_pdf_content)
            assert any(str(file_size) in record.message for record in caplog.records), \
                "Log should contain file size"
    
    def test_batch_download_summary(self, downloader, temp_dir, mock_pdf_content, caplog):
        """
        Test that batch download provides summary of successful and failed downloads.
        
        Validates Requirement: 2.5
        """
        import logging
        caplog.set_level(logging.INFO)
        
        # Create mix of sources (some will succeed, some will fail)
        test_sources = [
            LegalDocumentSource(
                url="https://example.gov.in/success.pdf",
                filename="success.pdf",
                description="Success Document",
                law_type="GST"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/fail.pdf",
                filename="fail.pdf",
                description="Fail Document",
                law_type="GST"
            )
        ]
        
        def mock_get_side_effect(url, **kwargs):
            if "success" in url:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = mock_pdf_content
                mock_response.raise_for_status = Mock()
                return mock_response
            else:
                raise requests.exceptions.RequestException("Network error")
        
        with patch('requests.get', side_effect=mock_get_side_effect):
            results = downloader.download_all(test_sources)
            
            # Verify summary is logged
            summary_logs = [record.message for record in caplog.records if "Summary" in record.message]
            assert len(summary_logs) > 0, "Should log summary"
            
            # Verify counts are in logs
            assert any("Successful" in record.message for record in caplog.records), \
                "Should log successful count"
            assert any("Failed" in record.message for record in caplog.records), \
                "Should log failed count"
    
    def test_directory_creation(self, temp_dir):
        """
        Test that downloader creates output directory if it doesn't exist.
        
        Validates Requirement: 10.1
        """
        # Create path to non-existent directory
        new_dir = os.path.join(temp_dir, "new_subdir", "downloads")
        assert not os.path.exists(new_dir), "Directory should not exist initially"
        
        # Create downloader (should create directory)
        downloader = SeedDownloader(output_dir=new_dir)
        
        # Verify directory was created
        assert os.path.exists(new_dir), "Directory should be created"
        assert os.path.isdir(new_dir), "Path should be a directory"
    
    def test_file_validation(self, downloader, temp_dir, mock_pdf_content):
        """
        Test that downloaded files are valid PDFs.
        
        This is an integration test that verifies the complete pipeline
        produces valid output files.
        """
        test_source = LegalDocumentSource(
            url="https://example.gov.in/test.pdf",
            filename="test_document.pdf",
            description="Test Document",
            law_type="GST"
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            result = downloader.download_document(test_source)
            assert result is True
            
            # Verify file is valid PDF
            file_path = Path(temp_dir) / test_source.filename
            with open(file_path, 'rb') as f:
                content = f.read()
                
                # Check PDF header
                assert content.startswith(b'%PDF'), "File should start with PDF header"
                
                # Check PDF footer
                assert b'%%EOF' in content, "File should contain PDF EOF marker"


class TestDownloadPipelineErrorHandling:
    """Integration tests for error handling in download pipeline"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test downloads"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def downloader(self, temp_dir):
        """Create downloader instance with temp directory"""
        return SeedDownloader(output_dir=temp_dir)
    
    def test_ssl_error_recovery(self, downloader, temp_dir):
        """
        Test that SSL errors trigger retry without verification.
        
        Validates Requirement: 2.1
        """
        test_source = LegalDocumentSource(
            url="https://example.gov.in/test.pdf",
            filename="test_document.pdf",
            description="Test Document",
            law_type="GST"
        )
        
        mock_pdf = b"%PDF-1.4\ntest\n%%EOF"
        
        # First call raises SSLError, second succeeds
        call_count = [0]
        
        def mock_get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and kwargs.get('verify', True):
                raise requests.exceptions.SSLError("SSL verification failed")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = mock_pdf
                mock_response.raise_for_status = Mock()
                return mock_response
        
        with patch('requests.get', side_effect=mock_get_side_effect) as mock_get:
            result = downloader.download_document(test_source)
            
            # Should succeed after retry
            assert result is True, "Should succeed after SSL fallback"
            
            # Should have made 2 calls (first with verify=True, second with verify=False)
            assert mock_get.call_count == 2, "Should retry with SSL verification disabled"
    
    def test_timeout_retry_with_backoff(self, downloader, temp_dir):
        """
        Test that timeouts trigger retry with exponential backoff.
        
        Validates Requirement: 2.2
        """
        test_source = LegalDocumentSource(
            url="https://example.gov.in/test.pdf",
            filename="test_document.pdf",
            description="Test Document",
            law_type="GST"
        )
        
        mock_pdf = b"%PDF-1.4\ntest\n%%EOF"
        
        # First 2 calls timeout, third succeeds
        call_count = [0]
        
        def mock_get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise requests.exceptions.Timeout("Connection timeout")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = mock_pdf
                mock_response.raise_for_status = Mock()
                return mock_response
        
        with patch('requests.get', side_effect=mock_get_side_effect) as mock_get:
            with patch('time.sleep') as mock_sleep:  # Mock sleep to speed up test
                result = downloader.download_document(test_source)
                
                # Should succeed after retries
                assert result is True, "Should succeed after retries"
                
                # Should have made 3 calls
                assert mock_get.call_count == 3, "Should retry up to 3 times"
                
                # Should have called sleep with exponential backoff (1s, 2s)
                assert mock_sleep.call_count == 2, "Should sleep between retries"
    
    def test_graceful_failure_continuation(self, downloader, temp_dir):
        """
        Test that failed downloads don't stop processing of remaining downloads.
        
        Validates Requirement: 2.3
        """
        test_sources = [
            LegalDocumentSource(
                url="https://example.gov.in/fail.pdf",
                filename="fail.pdf",
                description="Fail Document",
                law_type="GST"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/success.pdf",
                filename="success.pdf",
                description="Success Document",
                law_type="GST"
            )
        ]
        
        mock_pdf = b"%PDF-1.4\ntest\n%%EOF"
        
        def mock_get_side_effect(url, **kwargs):
            if "fail" in url:
                raise requests.exceptions.RequestException("Network error")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = mock_pdf
                mock_response.raise_for_status = Mock()
                return mock_response
        
        with patch('requests.get', side_effect=mock_get_side_effect):
            results = downloader.download_all(test_sources)
            
            # First should fail, second should succeed
            assert results["fail.pdf"] is False, "First download should fail"
            assert results["success.pdf"] is True, "Second download should succeed"
            
            # Verify success file exists
            success_path = Path(temp_dir) / "success.pdf"
            assert success_path.exists(), "Successful download should create file"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

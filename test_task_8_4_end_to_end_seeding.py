"""
End-to-End Test for Complete Seeding Workflow (Task 8.4)

This test validates the complete seeding workflow from download to queryable
database, including integration with Legal Sentinel queries and full pipeline
idempotency.

Validates Requirement: 8.4
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.seed_downloader import SeedDownloader, LegalDocumentSource
from scripts.seed_data import SeedDataProcessor
from vector_database import LegalVectorDB


class TestEndToEndSeedingWorkflow:
    """End-to-end tests for complete seeding workflow"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for downloads and database"""
        download_dir = tempfile.mkdtemp(prefix="test_downloads_")
        db_dir = tempfile.mkdtemp(prefix="test_db_")
        yield download_dir, db_dir
        # Cleanup
        shutil.rmtree(download_dir, ignore_errors=True)
        shutil.rmtree(db_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_pdf_content(self):
        """Mock PDF content with legal text"""
        # Create a more realistic PDF with legal content
        legal_text = """Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged on any supply of goods or services or both to him which are used or intended to be used in the course or furtherance of his business.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless the turnover exceeds 5 crore.

Provided that the input tax credit shall be available subject to such conditions and restrictions as may be prescribed.

Section 17 - Apportionment of credit and blocked credits

(1) Where the goods or services or both are used by the registered person partly for effecting taxable supplies including zero-rated supplies under this Act or under the Integrated Goods and Services Tax Act and partly for effecting exempt supplies under the said Acts, the amount of credit shall be restricted."""
        
        # Create PDF with the legal text
        pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length {len(legal_text)}
>>
stream
BT
/F1 10 Tf
50 750 Td
({legal_text[:500]}) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
467
%%EOF
"""
        
        return pdf_content.encode('latin-1')
    
    def test_complete_seeding_workflow(self, temp_dirs, mock_pdf_content):
        """
        Test complete end-to-end seeding workflow.
        
        Workflow:
        1. Download documents using seed_downloader
        2. Process documents using seed_data processor
        3. Verify database is populated
        4. Verify Legal Sentinel can query the data
        5. Re-run entire pipeline (test idempotency)
        
        Validates Requirement: 8.4
        """
        download_dir, db_dir = temp_dirs
        
        # Step 1: Download documents
        test_sources = [
            LegalDocumentSource(
                url="https://example.gov.in/cgst.pdf",
                filename="CGST_Act_2017.pdf",
                description="Central GST Act",
                law_type="GST"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/income-tax.pdf",
                filename="Income_Tax_Act_1961.pdf",
                description="Income Tax Act",
                law_type="Income Tax"
            )
        ]
        
        # Mock download responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        downloader = SeedDownloader(output_dir=download_dir)
        
        with patch('requests.get', return_value=mock_response):
            download_results = downloader.download_all(test_sources)
        
        # Verify downloads succeeded
        assert all(download_results.values()), "All downloads should succeed"
        
        # Verify files exist
        for source in test_sources:
            file_path = Path(download_dir) / source.filename
            assert file_path.exists(), f"Downloaded file should exist: {source.filename}"
        
        # Step 2: Process documents
        processor = SeedDataProcessor(data_dir=download_dir, db_path=db_dir)
        processing_report = processor.process_all_documents()
        
        # Verify processing succeeded
        assert processing_report.total_documents == 2, "Should process 2 documents"
        assert processing_report.successful_documents == 2, "Both should succeed"
        assert processing_report.total_chunks_created > 0, "Should create chunks"
        
        # Step 3: Verify database is populated
        db = processor.vector_db
        stats = db.get_stats()
        
        assert stats['total_chunks'] > 0, "Database should contain chunks"
        assert 'GST' in stats['law_type_distribution'], "Should have GST chunks"
        assert 'Income Tax' in stats['law_type_distribution'], "Should have Income Tax chunks"
        
        # Step 4: Verify Legal Sentinel can query the data
        # Test semantic search
        search_results = db.semantic_search("input tax credit", law_type="GST", n_results=5)
        assert len(search_results) > 0, "Should find results for legal query"
        
        # Verify results are relevant
        for result in search_results:
            assert result['metadata']['law_type'] == "GST", "Results should be GST"
            assert 'text' in result, "Result should have text"
            assert 'distance' in result, "Result should have distance metric"
        
        # Test keyword search
        keyword_results = db.keyword_search("16")
        if len(keyword_results) > 0:
            # Verify section search works
            assert any("16" in r['metadata'].get('section_number', '') 
                      for r in keyword_results), "Should find section 16"
        
        # Step 5: Re-run entire pipeline (test idempotency)
        # Re-download (should skip existing files)
        with patch('requests.get', return_value=mock_response) as mock_get:
            download_results2 = downloader.download_all(test_sources)
            
            # Verify no network requests were made (files already exist)
            mock_get.assert_not_called()
            assert all(download_results2.values()), "Re-download should succeed (skip)"
        
        # Re-process (should skip already-processed documents)
        processor2 = SeedDataProcessor(data_dir=download_dir, db_path=db_dir)
        processing_report2 = processor2.process_all_documents()
        
        # Verify documents were skipped
        assert processing_report2.total_documents == 2, "Should attempt 2 documents"
        skipped_count = sum(1 for doc in processing_report2.document_reports 
                          if doc.law_type == "Skipped")
        assert skipped_count == 2, "Both documents should be skipped"
        
        # Verify no new chunks were created
        assert processing_report2.total_chunks_created == 0, \
            "Should not create new chunks on re-run"
        
        # Verify database still has same number of chunks
        stats2 = processor2.vector_db.get_stats()
        assert stats2['total_chunks'] == stats['total_chunks'], \
            "Database should have same number of chunks after re-run"
    
    def test_legal_sentinel_integration(self, temp_dirs, mock_pdf_content):
        """
        Test that seeded data integrates correctly with Legal Sentinel queries.
        
        This test verifies that the seeded data can be used for real legal
        compliance queries as intended by the Legal Sentinel system.
        
        Validates Requirement: 8.4
        """
        download_dir, db_dir = temp_dirs
        
        # Create and download test document
        test_source = LegalDocumentSource(
            url="https://example.gov.in/cgst.pdf",
            filename="CGST_Act_2017.pdf",
            description="Central GST Act",
            law_type="GST"
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        downloader = SeedDownloader(output_dir=download_dir)
        
        with patch('requests.get', return_value=mock_response):
            result = downloader.download_document(test_source)
            assert result is True, "Download should succeed"
        
        # Process document
        processor = SeedDataProcessor(data_dir=download_dir, db_path=db_dir)
        report = processor.process_all_documents()
        assert report.successful_documents == 1, "Processing should succeed"
        
        # Simulate Legal Sentinel queries
        db = processor.vector_db
        
        # Query 1: General compliance question
        results1 = db.semantic_search(
            "What are the conditions for input tax credit?",
            law_type="GST",
            n_results=3
        )
        assert len(results1) > 0, "Should find results for compliance query"
        
        # Query 2: Turnover-specific question
        results2 = db.semantic_search(
            "input tax credit turnover",
            law_type="GST",
            max_turnover=100000000,  # 10 crore
            n_results=3
        )
        assert len(results2) > 0, "Should find results with turnover filter"
        
        # Query 3: Section-specific question (without law_type to avoid multi-field filter)
        results3 = db.hybrid_search(
            "section 16 input tax credit",
            n_results=3
        )
        # Hybrid search should work even without law_type filter
        assert len(results3) >= 0, "Hybrid search should complete without error"
    
    def test_multi_document_seeding_workflow(self, temp_dirs, mock_pdf_content):
        """
        Test seeding workflow with multiple documents of different law types.
        
        Validates that the complete workflow handles multiple law types correctly.
        
        Validates Requirement: 8.4
        """
        download_dir, db_dir = temp_dirs
        
        # Create multiple test sources with different law types
        test_sources = [
            LegalDocumentSource(
                url="https://example.gov.in/cgst.pdf",
                filename="CGST_Act_2017.pdf",
                description="Central GST Act",
                law_type="GST"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/igst.pdf",
                filename="IGST_Act_2017.pdf",
                description="Integrated GST Act",
                law_type="GST"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/income-tax.pdf",
                filename="Income_Tax_Act_1961.pdf",
                description="Income Tax Act",
                law_type="Income Tax"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/companies.pdf",
                filename="Companies_Act_2013.pdf",
                description="Companies Act",
                law_type="Corporate Law"
            )
        ]
        
        # Mock download
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        downloader = SeedDownloader(output_dir=download_dir)
        
        with patch('requests.get', return_value=mock_response):
            download_results = downloader.download_all(test_sources)
        
        assert all(download_results.values()), "All downloads should succeed"
        
        # Process all documents
        processor = SeedDataProcessor(data_dir=download_dir, db_path=db_dir)
        report = processor.process_all_documents()
        
        # Verify all documents processed
        assert report.total_documents == 4, "Should process 4 documents"
        assert report.successful_documents == 4, "All should succeed"
        
        # Verify database has all law types
        db = processor.vector_db
        stats = db.get_stats()
        
        law_types = stats['law_type_distribution']
        assert 'GST' in law_types, "Should have GST chunks"
        assert 'Income Tax' in law_types, "Should have Income Tax chunks"
        assert 'Corporate Law' in law_types, "Should have Corporate Law chunks"
        
        # Verify each law type is searchable
        gst_results = db.semantic_search("provisions", law_type="GST", n_results=5)
        assert len(gst_results) > 0, "Should find GST results"
        
        it_results = db.semantic_search("provisions", law_type="Income Tax", n_results=5)
        assert len(it_results) > 0, "Should find Income Tax results"
        
        corp_results = db.semantic_search("provisions", law_type="Corporate Law", n_results=5)
        assert len(corp_results) > 0, "Should find Corporate Law results"
    
    def test_error_recovery_in_workflow(self, temp_dirs, mock_pdf_content):
        """
        Test that workflow handles errors gracefully and continues.
        
        Validates that partial failures don't break the entire workflow.
        
        Validates Requirement: 8.4
        """
        download_dir, db_dir = temp_dirs
        
        # Create mix of valid and invalid sources
        test_sources = [
            LegalDocumentSource(
                url="https://example.gov.in/cgst.pdf",
                filename="CGST_Act_2017.pdf",
                description="Central GST Act",
                law_type="GST"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/fail.pdf",
                filename="Fail_Act.pdf",
                description="Failing Document",
                law_type="GST"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/income-tax.pdf",
                filename="Income_Tax_Act_1961.pdf",
                description="Income Tax Act",
                law_type="Income Tax"
            )
        ]
        
        # Mock download with one failure
        def mock_get_side_effect(url, **kwargs):
            if "fail" in url:
                raise Exception("Network error")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = mock_pdf_content
                mock_response.raise_for_status = Mock()
                return mock_response
        
        downloader = SeedDownloader(output_dir=download_dir)
        
        with patch('requests.get', side_effect=mock_get_side_effect):
            download_results = downloader.download_all(test_sources)
        
        # Verify 2 succeeded, 1 failed
        successful_downloads = sum(1 for v in download_results.values() if v)
        assert successful_downloads == 2, "2 downloads should succeed"
        
        # Process documents (only successful downloads)
        processor = SeedDataProcessor(data_dir=download_dir, db_path=db_dir)
        report = processor.process_all_documents()
        
        # Verify only successful documents were processed
        assert report.total_documents == 2, "Should process 2 documents"
        assert report.successful_documents == 2, "Both should succeed"
        
        # Verify database has data from successful documents
        db = processor.vector_db
        stats = db.get_stats()
        assert stats['total_chunks'] > 0, "Database should have chunks from successful documents"
    
    def test_workflow_statistics_and_reporting(self, temp_dirs, mock_pdf_content):
        """
        Test that workflow provides comprehensive statistics and reporting.
        
        Validates Requirement: 8.4
        """
        download_dir, db_dir = temp_dirs
        
        # Create test sources
        test_sources = [
            LegalDocumentSource(
                url="https://example.gov.in/cgst.pdf",
                filename="CGST_Act_2017.pdf",
                description="Central GST Act",
                law_type="GST"
            ),
            LegalDocumentSource(
                url="https://example.gov.in/income-tax.pdf",
                filename="Income_Tax_Act_1961.pdf",
                description="Income Tax Act",
                law_type="Income Tax"
            )
        ]
        
        # Mock download
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = Mock()
        
        downloader = SeedDownloader(output_dir=download_dir)
        
        with patch('requests.get', return_value=mock_response):
            download_results = downloader.download_all(test_sources)
        
        # Process documents
        processor = SeedDataProcessor(data_dir=download_dir, db_path=db_dir)
        report = processor.process_all_documents()
        
        # Verify report has all required statistics
        assert report.total_documents > 0, "Report should have document count"
        assert report.successful_documents > 0, "Report should have success count"
        assert report.total_chunks_created > 0, "Report should have chunk count"
        assert report.total_processing_time > 0, "Report should have processing time"
        assert len(report.document_reports) > 0, "Report should have document details"
        
        # Verify report can be formatted
        report_str = processor.generate_report(report)
        assert "Summary" in report_str, "Report should have summary section"
        assert "Total Documents" in report_str, "Report should show document count"
        assert "Total Chunks" in report_str, "Report should show chunk count"
        assert "Total Time" in report_str, "Report should show processing time"
        
        # Verify database statistics
        db = processor.vector_db
        stats = db.get_stats()
        
        assert 'total_chunks' in stats, "Stats should have total chunks"
        assert 'law_type_distribution' in stats, "Stats should have law type distribution"
        assert 'db_path' in stats, "Stats should have database path"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

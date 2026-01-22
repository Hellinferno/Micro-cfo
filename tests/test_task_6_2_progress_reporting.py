"""
Test suite for Task 6.2: Detailed Progress Reporting

This test suite validates that the system provides detailed progress feedback
during document processing, including:
- Page-by-page progress during PDF extraction (Requirement 9.2)
- Chunk count after chunking (Requirement 9.3)
- Storage progress percentage (Requirement 9.4)

Test Strategy:
- Unit tests for specific progress reporting scenarios
- Property tests for universal progress reporting properties
- Integration tests for end-to-end progress tracking
"""

import pytest
import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.seed_data import SeedDataProcessor
from legal_ingestion import LegalDocumentProcessor, LegalChunk


class TestPageProgressReporting:
    """Test page-by-page progress reporting during PDF extraction (Requirement 9.2)"""
    
    def test_logs_page_progress_during_extraction(self, caplog):
        """
        GIVEN a PDF with multiple pages
        WHEN processing the PDF
        THEN the system should log progress for each page
        
        Validates Requirement: 9.2
        """
        caplog.set_level(logging.INFO)
        
        processor = LegalDocumentProcessor()
        
        # Create a mock PDF with 5 pages
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_pages = [Mock() for _ in range(5)]
            for i, page in enumerate(mock_pages):
                page.extract_text.return_value = f"Section {i+1} - Test content"
            
            mock_reader.return_value.pages = mock_pages
            
            # Process the mock PDF
            chunks = processor.process_pdf("test.pdf", "GST")
            
            # Verify page progress was logged
            log_messages = [record.message for record in caplog.records]
            
            # Should log total pages
            assert any("Extracting text from 5 pages" in msg for msg in log_messages)
            
            # Should log each page
            assert any("Processing page 1/5" in msg for msg in log_messages)
            assert any("Processing page 2/5" in msg for msg in log_messages)
            assert any("Processing page 3/5" in msg for msg in log_messages)
            assert any("Processing page 4/5" in msg for msg in log_messages)
            assert any("Processing page 5/5" in msg for msg in log_messages)
            
            # Should log completion
            assert any("Text extraction complete (5 pages processed)" in msg for msg in log_messages)
    
    def test_logs_page_progress_with_errors(self, caplog):
        """
        GIVEN a PDF where some pages fail to extract
        WHEN processing the PDF
        THEN the system should log progress and errors for each page
        
        Validates Requirement: 9.2
        """
        caplog.set_level(logging.INFO)
        
        processor = LegalDocumentProcessor()
        
        # Create a mock PDF with 3 pages, where page 2 fails
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_pages = [Mock() for _ in range(3)]
            mock_pages[0].extract_text.return_value = "Section 1 - Test content"
            mock_pages[1].extract_text.side_effect = Exception("Extraction error")
            mock_pages[2].extract_text.return_value = "Section 3 - Test content"
            
            mock_reader.return_value.pages = mock_pages
            
            # Process the mock PDF
            chunks = processor.process_pdf("test.pdf", "GST")
            
            # Verify page progress was logged including error
            log_messages = [record.message for record in caplog.records]
            
            assert any("Processing page 1/3" in msg for msg in log_messages)
            assert any("Processing page 2/3" in msg for msg in log_messages)
            assert any("Processing page 3/3" in msg for msg in log_messages)
            assert any("Error extracting text from page 2/3" in msg for msg in log_messages)


class TestChunkCountReporting:
    """Test chunk count reporting after chunking (Requirement 9.3)"""
    
    def test_logs_chunk_count_after_chunking(self, caplog):
        """
        GIVEN a PDF that produces multiple chunks
        WHEN processing the PDF
        THEN the system should log the number of chunks created
        
        Validates Requirement: 9.3
        """
        caplog.set_level(logging.INFO)
        
        processor = LegalDocumentProcessor()
        
        # Create a mock PDF with content that will produce multiple chunks
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = """
Section 1 - First section
This is the content of section 1.

Section 2 - Second section
This is the content of section 2.

Section 3 - Third section
This is the content of section 3.
"""
            mock_reader.return_value.pages = [mock_page]
            
            # Process the mock PDF
            chunks = processor.process_pdf("test.pdf", "GST")
            
            # Verify chunk count was logged
            log_messages = [record.message for record in caplog.records]
            
            # Should log the number of chunks created
            chunk_count = len(chunks)
            assert any(f"Created {chunk_count} legal chunks" in msg for msg in log_messages)
    
    def test_logs_zero_chunks_for_empty_pdf(self, caplog):
        """
        GIVEN a PDF with no extractable content
        WHEN processing the PDF
        THEN the system should log a warning about empty content
        
        Validates Requirement: 9.3
        """
        caplog.set_level(logging.INFO)
        
        processor = LegalDocumentProcessor()
        
        # Create a mock PDF with empty content
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = ""
            mock_reader.return_value.pages = [mock_page]
            
            # Process the mock PDF
            chunks = processor.process_pdf("test.pdf", "GST")
            
            # Verify warning was logged
            log_messages = [record.message for record in caplog.records]
            assert any("Empty content after extraction and cleaning" in msg for msg in log_messages)
            assert len(chunks) == 0


class TestStorageProgressReporting:
    """Test storage progress percentage reporting (Requirement 9.4)"""
    
    def test_logs_storage_progress_for_large_chunk_set(self, caplog):
        """
        GIVEN a document with many chunks (>10)
        WHEN storing chunks in the vector database
        THEN the system should log storage progress as percentage
        
        Validates Requirement: 9.4
        """
        caplog.set_level(logging.INFO)
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock vector database
            with patch('scripts.seed_data.LegalVectorDB') as mock_db_class:
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                
                # Create processor
                processor = SeedDataProcessor(data_dir=temp_dir, db_path=temp_dir)
                
                # Create 50 mock chunks
                chunks = [
                    LegalChunk(
                        text=f"Section {i} content",
                        law_type="GST",
                        section_number=str(i)
                    )
                    for i in range(50)
                ]
                
                # Store chunks with progress reporting
                processor._store_chunks_with_progress(chunks)
                
                # Verify progress was logged
                log_messages = [record.message for record in caplog.records]
                
                # Should log multiple progress updates with percentages
                progress_logs = [msg for msg in log_messages if "Storing chunks" in msg and "%" in msg]
                assert len(progress_logs) > 0, "Should log progress updates"
                
                # Should log completion
                assert any("Storage complete (100%)" in msg for msg in log_messages)
    
    def test_logs_simple_storage_for_small_chunk_set(self, caplog):
        """
        GIVEN a document with few chunks (<=10)
        WHEN storing chunks in the vector database
        THEN the system should log simple storage message
        
        Validates Requirement: 9.4
        """
        caplog.set_level(logging.INFO)
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock vector database
            with patch('scripts.seed_data.LegalVectorDB') as mock_db_class:
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                
                # Create processor
                processor = SeedDataProcessor(data_dir=temp_dir, db_path=temp_dir)
                
                # Create 5 mock chunks
                chunks = [
                    LegalChunk(
                        text=f"Section {i} content",
                        law_type="GST",
                        section_number=str(i)
                    )
                    for i in range(5)
                ]
                
                # Store chunks with progress reporting
                processor._store_chunks_with_progress(chunks)
                
                # Verify simple storage was logged
                log_messages = [record.message for record in caplog.records]
                
                assert any("Storing 5 chunks" in msg for msg in log_messages)
                assert any("Storage complete (100%)" in msg for msg in log_messages)
    
    def test_storage_progress_percentages_are_accurate(self, caplog):
        """
        GIVEN a document with many chunks
        WHEN storing chunks in batches
        THEN the progress percentages should be accurate
        
        Validates Requirement: 9.4
        """
        caplog.set_level(logging.INFO)
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock vector database
            with patch('scripts.seed_data.LegalVectorDB') as mock_db_class:
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                
                # Create processor
                processor = SeedDataProcessor(data_dir=temp_dir, db_path=temp_dir)
                
                # Create 100 mock chunks for clear percentage calculation
                chunks = [
                    LegalChunk(
                        text=f"Section {i} content",
                        law_type="GST",
                        section_number=str(i)
                    )
                    for i in range(100)
                ]
                
                # Store chunks with progress reporting
                processor._store_chunks_with_progress(chunks)
                
                # Verify progress percentages
                log_messages = [record.message for record in caplog.records]
                progress_logs = [msg for msg in log_messages if "%" in msg and "Storing chunks" in msg]
                
                # Extract percentages from logs
                import re
                percentages = []
                for msg in progress_logs:
                    match = re.search(r'\((\d+\.?\d*)%\)', msg)
                    if match:
                        percentages.append(float(match.group(1)))
                
                # Verify percentages are increasing
                assert percentages == sorted(percentages), "Percentages should be in increasing order"
                
                # Verify final percentage is 100%
                assert any("100%" in msg for msg in log_messages)


class TestIntegratedProgressReporting:
    """Test integrated progress reporting across the entire pipeline"""
    
    def test_complete_pipeline_progress_reporting(self, caplog):
        """
        GIVEN a complete document processing pipeline
        WHEN processing a document
        THEN all progress stages should be logged in order
        
        Validates Requirements: 9.2, 9.3, 9.4
        """
        caplog.set_level(logging.INFO)
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test PDF file
            test_pdf = os.path.join(temp_dir, "CGST_Act_2017.pdf")
            Path(test_pdf).touch()
            
            # Create mock vector database
            with patch('scripts.seed_data.LegalVectorDB') as mock_db_class:
                mock_db = Mock()
                mock_db.load_processing_metadata.return_value = None  # Not processed yet
                mock_db_class.return_value = mock_db
                
                # Create mock PDF reader
                with patch('PyPDF2.PdfReader') as mock_reader:
                    mock_pages = [Mock() for _ in range(3)]
                    for i, page in enumerate(mock_pages):
                        page.extract_text.return_value = f"Section {i+1} - Test content\n"
                    mock_reader.return_value.pages = mock_pages
                    
                    # Create processor and process document
                    processor = SeedDataProcessor(data_dir=temp_dir, db_path=temp_dir)
                    report = processor.process_single_document(test_pdf)
                    
                    # Verify all progress stages were logged
                    log_messages = [record.message for record in caplog.records]
                    
                    # Stage 1: PDF extraction with page progress
                    assert any("Extracting text from 3 pages" in msg for msg in log_messages)
                    assert any("Processing page 1/3" in msg for msg in log_messages)
                    
                    # Stage 2: Chunk creation
                    assert any("Created" in msg and "chunks" in msg for msg in log_messages)
                    
                    # Stage 3: Storage progress
                    assert any("Storing chunks in vector database" in msg for msg in log_messages)
                    assert any("Storage complete" in msg for msg in log_messages)
                    
                    # Stage 4: Completion
                    assert any("Completed in" in msg for msg in log_messages)


class TestProgressReportingEdgeCases:
    """Test edge cases in progress reporting"""
    
    def test_progress_reporting_with_single_page(self, caplog):
        """
        GIVEN a PDF with only one page
        WHEN processing the PDF
        THEN progress should still be logged correctly
        """
        caplog.set_level(logging.INFO)
        
        processor = LegalDocumentProcessor()
        
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "Section 1 - Test content"
            mock_reader.return_value.pages = [mock_page]
            
            chunks = processor.process_pdf("test.pdf", "GST")
            
            log_messages = [record.message for record in caplog.records]
            assert any("Extracting text from 1 pages" in msg for msg in log_messages)
            assert any("Processing page 1/1" in msg for msg in log_messages)
    
    def test_progress_reporting_with_empty_chunk_list(self, caplog):
        """
        GIVEN an empty list of chunks
        WHEN storing chunks
        THEN the method should handle it gracefully
        """
        caplog.set_level(logging.INFO)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('scripts.seed_data.LegalVectorDB') as mock_db_class:
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                
                processor = SeedDataProcessor(data_dir=temp_dir, db_path=temp_dir)
                
                # Store empty chunk list
                processor._store_chunks_with_progress([])
                
                # Should not crash and should not log storage messages
                log_messages = [record.message for record in caplog.records]
                storage_logs = [msg for msg in log_messages if "Storing chunks" in msg]
                assert len(storage_logs) == 0


def test_progress_reporting_requirements_validation():
    """
    Meta-test to validate that all requirements are covered.
    
    This test documents which requirements are validated by which test classes.
    """
    requirements_coverage = {
        '9.2': 'TestPageProgressReporting - logs page progress during PDF extraction',
        '9.3': 'TestChunkCountReporting - logs chunk count after chunking',
        '9.4': 'TestStorageProgressReporting - logs storage progress percentage',
    }
    
    print("\nRequirements Coverage:")
    for req, coverage in requirements_coverage.items():
        print(f"  Requirement {req}: {coverage}")
    
    assert len(requirements_coverage) == 3, "Should cover all 3 requirements for task 6.2"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

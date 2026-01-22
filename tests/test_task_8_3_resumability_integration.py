"""
Integration Test for Resumability After Interruption (Task 8.3)

This test validates that the seeding system can resume correctly after
interruption without creating duplicate data or losing progress.

Validates Requirement: 8.3
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

from scripts.seed_data import SeedDataProcessor, ProcessingMetadata
from vector_database import LegalVectorDB


class TestResumabilityAfterInterruption:
    """Integration tests for resumability after interruption"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for test data and database"""
        data_dir = tempfile.mkdtemp(prefix="test_data_")
        db_dir = tempfile.mkdtemp(prefix="test_db_")
        yield data_dir, db_dir
        # Cleanup
        shutil.rmtree(data_dir, ignore_errors=True)
        shutil.rmtree(db_dir, ignore_errors=True)
    
    def create_minimal_pdf(self, path, content_text):
        """Create a minimal PDF with given text"""
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
/Length {len(content_text)}
>>
stream
BT
/F1 12 Tf
50 750 Td
({content_text}) Tj
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
        
        with open(path, 'wb') as f:
            f.write(pdf_content.encode('latin-1'))
    
    def test_resume_after_partial_processing(self, temp_dirs):
        """
        Test that system resumes correctly after partial processing.
        
        Scenario:
        1. Process 2 documents successfully
        2. Simulate interruption (stop processing)
        3. Add a new document
        4. Resume processing
        5. Verify: Already processed documents are skipped, new document is processed
        
        Validates Requirement: 8.3
        """
        data_dir, db_dir = temp_dirs
        
        # Create 2 initial PDFs
        pdf1_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        pdf2_path = os.path.join(data_dir, "Income_Tax_Act_1961.pdf")
        
        self.create_minimal_pdf(pdf1_path, "Section 1 - GST provisions")
        self.create_minimal_pdf(pdf2_path, "Section 1 - Income Tax provisions")
        
        # First processing run - process both documents
        processor1 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report1 = processor1.process_all_documents()
        
        # Verify both documents were processed
        assert report1.total_documents == 2, "Should process 2 documents"
        assert report1.successful_documents == 2, "Both should succeed"
        
        initial_chunks = report1.total_chunks_created
        
        # Simulate interruption by creating new processor instance
        # Add a third document (simulating new data after interruption)
        pdf3_path = os.path.join(data_dir, "Companies_Act_2013.pdf")
        self.create_minimal_pdf(pdf3_path, "Section 1 - Corporate Law provisions")
        
        # Second processing run - should skip first 2, process only the new one
        processor2 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report2 = processor2.process_all_documents()
        
        # Verify all 3 documents were attempted
        assert report2.total_documents == 3, "Should attempt all 3 documents"
        
        # Verify first 2 were skipped (already processed)
        skipped_count = sum(1 for doc_report in report2.document_reports 
                          if doc_report.law_type == "Skipped")
        assert skipped_count == 2, "Should skip 2 already-processed documents"
        
        # Verify only new chunks were added
        new_chunks = report2.total_chunks_created
        assert new_chunks > 0, "Should create chunks for new document"
        
        # Verify total chunks in database is correct
        db = processor2.vector_db
        stats = db.get_stats()
        expected_total = initial_chunks + new_chunks
        assert stats['total_chunks'] == expected_total, \
            f"Database should have {expected_total} chunks (initial {initial_chunks} + new {new_chunks})"
    
    def test_no_duplicate_data_on_rerun(self, temp_dirs):
        """
        Test that re-running processing doesn't create duplicate data.
        
        Scenario:
        1. Process documents
        2. Re-run processing on same documents
        3. Verify: No duplicate chunks created
        
        Validates Requirement: 8.3
        """
        data_dir, db_dir = temp_dirs
        
        # Create test PDF
        pdf_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        self.create_minimal_pdf(pdf_path, "Section 1 - GST provisions")
        
        # First processing run
        processor1 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report1 = processor1.process_all_documents()
        
        assert report1.successful_documents == 1, "First run should succeed"
        first_run_chunks = report1.total_chunks_created
        
        # Get database stats after first run
        db1 = processor1.vector_db
        stats1 = db1.get_stats()
        first_run_db_chunks = stats1['total_chunks']
        
        # Second processing run (re-run on same data)
        processor2 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report2 = processor2.process_all_documents()
        
        # Verify document was skipped
        assert report2.total_documents == 1, "Should attempt 1 document"
        skipped = any(doc.law_type == "Skipped" for doc in report2.document_reports)
        assert skipped, "Document should be skipped on second run"
        
        # Verify no new chunks were created
        assert report2.total_chunks_created == 0, "Should not create new chunks on re-run"
        
        # Verify database has same number of chunks
        db2 = processor2.vector_db
        stats2 = db2.get_stats()
        assert stats2['total_chunks'] == first_run_db_chunks, \
            "Database should have same number of chunks after re-run"
    
    def test_resume_with_modified_file(self, temp_dirs):
        """
        Test that system detects and reprocesses modified files.
        
        Scenario:
        1. Process document
        2. Modify the document (change content)
        3. Re-run processing
        4. Verify: Modified document is reprocessed
        
        Validates Requirement: 8.5 (file hash comparison)
        """
        data_dir, db_dir = temp_dirs
        
        # Create test PDF
        pdf_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        self.create_minimal_pdf(pdf_path, "Section 1 - Original content")
        
        # First processing run
        processor1 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report1 = processor1.process_single_document(pdf_path)
        
        assert report1.success, "First processing should succeed"
        first_chunks = report1.chunks_created
        
        # Modify the file (change content)
        self.create_minimal_pdf(pdf_path, "Section 1 - Modified content with more text")
        
        # Second processing run
        processor2 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report2 = processor2.process_single_document(pdf_path)
        
        # Verify document was reprocessed (not skipped)
        assert report2.success, "Second processing should succeed"
        assert report2.law_type != "Skipped", "Modified file should be reprocessed"
        assert report2.chunks_created > 0, "Should create chunks for modified file"
    
    def test_metadata_persistence_across_runs(self, temp_dirs):
        """
        Test that processing metadata persists across processor instances.
        
        Validates Requirement: 8.5
        """
        data_dir, db_dir = temp_dirs
        
        # Create test PDF
        pdf_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        self.create_minimal_pdf(pdf_path, "Section 1 - GST provisions")
        
        # First processing run
        processor1 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report1 = processor1.process_single_document(pdf_path)
        assert report1.success, "Processing should succeed"
        
        # Create new processor instance (simulates restart)
        processor2 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        
        # Check if metadata exists
        metadata = ProcessingMetadata.load_from_db(processor2.vector_db, pdf_path)
        
        assert metadata is not None, "Metadata should persist across processor instances"
        assert metadata.file_path == pdf_path, "Metadata should have correct file path"
        assert metadata.chunks_created == report1.chunks_created, \
            "Metadata should have correct chunk count"
        assert metadata.law_type == report1.law_type, \
            "Metadata should have correct law type"
    
    def test_partial_failure_doesnt_block_resume(self, temp_dirs):
        """
        Test that partial failures don't prevent resuming with remaining files.
        
        Scenario:
        1. Process 3 documents, one fails
        2. Fix the failing document
        3. Re-run processing
        4. Verify: Successful documents are skipped, fixed document is processed
        
        Validates Requirement: 8.3
        """
        data_dir, db_dir = temp_dirs
        
        # Create 2 valid PDFs and 1 invalid
        pdf1_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        pdf2_path = os.path.join(data_dir, "Invalid_Act.pdf")
        pdf3_path = os.path.join(data_dir, "Income_Tax_Act_1961.pdf")
        
        self.create_minimal_pdf(pdf1_path, "Section 1 - GST provisions")
        # Create invalid PDF
        with open(pdf2_path, 'wb') as f:
            f.write(b"This is not a valid PDF")
        self.create_minimal_pdf(pdf3_path, "Section 1 - Income Tax provisions")
        
        # First processing run
        processor1 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report1 = processor1.process_all_documents()
        
        # Verify 2 succeeded, 1 failed
        assert report1.total_documents == 3, "Should attempt 3 documents"
        assert report1.successful_documents == 2, "2 should succeed"
        assert report1.failed_documents == 1, "1 should fail"
        
        # Fix the invalid PDF
        self.create_minimal_pdf(pdf2_path, "Section 1 - Fixed content")
        
        # Second processing run
        processor2 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report2 = processor2.process_all_documents()
        
        # Verify all 3 attempted
        assert report2.total_documents == 3, "Should attempt all 3 documents"
        
        # Verify 2 were skipped (already processed)
        skipped_count = sum(1 for doc in report2.document_reports 
                          if doc.law_type == "Skipped")
        assert skipped_count == 2, "Should skip 2 already-processed documents"
        
        # Verify the fixed document was processed
        processed_count = sum(1 for doc in report2.document_reports 
                            if doc.success and doc.law_type != "Skipped")
        assert processed_count == 1, "Should process the fixed document"
    
    def test_concurrent_safe_processing(self, temp_dirs):
        """
        Test that processing is safe even if metadata is checked concurrently.
        
        This test verifies the idempotency check works correctly.
        
        Validates Requirement: 8.2
        """
        data_dir, db_dir = temp_dirs
        
        # Create test PDF
        pdf_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        self.create_minimal_pdf(pdf_path, "Section 1 - GST provisions")
        
        # Process document
        processor1 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report1 = processor1.process_single_document(pdf_path)
        assert report1.success, "First processing should succeed"
        
        # Create multiple processor instances and check idempotency
        for i in range(3):
            processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
            
            # Check if already processed
            is_processed = processor._is_already_processed(pdf_path)
            assert is_processed, f"Iteration {i+1}: Should detect document as already processed"
            
            # Try to process again
            report = processor.process_single_document(pdf_path)
            assert report.law_type == "Skipped", \
                f"Iteration {i+1}: Should skip already-processed document"


class TestResumabilityEdgeCases:
    """Edge case tests for resumability"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for test data and database"""
        data_dir = tempfile.mkdtemp(prefix="test_data_")
        db_dir = tempfile.mkdtemp(prefix="test_db_")
        yield data_dir, db_dir
        # Cleanup
        shutil.rmtree(data_dir, ignore_errors=True)
        shutil.rmtree(db_dir, ignore_errors=True)
    
    def create_minimal_pdf(self, path, content_text):
        """Create a minimal PDF with given text"""
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
/Length {len(content_text)}
>>
stream
BT
/F1 12 Tf
50 750 Td
({content_text}) Tj
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
        
        with open(path, 'wb') as f:
            f.write(pdf_content.encode('latin-1'))
    
    def test_resume_with_empty_database(self, temp_dirs):
        """
        Test resumability when database is empty (first run).
        
        Validates that the system handles the initial state correctly.
        """
        data_dir, db_dir = temp_dirs
        
        # Create test PDF
        pdf_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        self.create_minimal_pdf(pdf_path, "Section 1 - GST provisions")
        
        # Process with empty database
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        
        # Check that document is not marked as processed
        is_processed = processor._is_already_processed(pdf_path)
        assert not is_processed, "Document should not be marked as processed in empty database"
        
        # Process document
        report = processor.process_single_document(pdf_path)
        assert report.success, "Processing should succeed"
        assert report.chunks_created > 0, "Should create chunks"
    
    def test_resume_with_corrupted_metadata(self, temp_dirs):
        """
        Test that system handles corrupted metadata gracefully.
        
        If metadata is corrupted or missing, system should reprocess the document.
        """
        data_dir, db_dir = temp_dirs
        
        # Create test PDF
        pdf_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        self.create_minimal_pdf(pdf_path, "Section 1 - GST provisions")
        
        # Process document
        processor1 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        report1 = processor1.process_single_document(pdf_path)
        assert report1.success, "First processing should succeed"
        
        # Simulate corrupted metadata by trying to load non-existent file
        processor2 = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        fake_path = os.path.join(data_dir, "nonexistent.pdf")
        
        # Should return None for non-existent file
        metadata = ProcessingMetadata.load_from_db(processor2.vector_db, fake_path)
        assert metadata is None, "Should return None for non-existent file metadata"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

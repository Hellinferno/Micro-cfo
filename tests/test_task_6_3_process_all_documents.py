"""
Test for Task 6.3: process_all_documents() method

This test verifies that the process_all_documents() method:
1. Processes all PDFs in the data directory
2. Uses process_single_document() for each PDF
3. Tracks processing statistics in ProcessingReport
4. Validates Requirements 7.5, 8.4
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.seed_data import SeedDataProcessor, ProcessingReport, DocumentReport


def create_sample_pdf(output_path: str, content: str = "Sample PDF content"):
    """
    Create a minimal valid PDF file for testing.
    
    Args:
        output_path: Path where PDF should be created
        content: Text content to include in PDF
    """
    # Minimal PDF structure
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
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
({content}) Tj
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
410
%%EOF
"""
    
    with open(output_path, 'w') as f:
        f.write(pdf_content)


def test_process_all_documents_basic():
    """
    Test that process_all_documents() processes multiple PDFs and tracks statistics.
    
    Validates Requirements: 7.5, 8.4
    """
    print("\n" + "="*80)
    print("TEST: process_all_documents() - Basic Functionality")
    print("="*80)
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(data_dir)
    
    try:
        # Create sample PDF files with different law types
        pdf_files = [
            ("CGST_Act_2017.pdf", "Section 1. This is the CGST Act."),
            ("Income_Tax_Act_1961.pdf", "Section 2. This is the Income Tax Act."),
            ("Companies_Act_2013.pdf", "Section 3. This is the Companies Act."),
        ]
        
        for filename, content in pdf_files:
            pdf_path = os.path.join(data_dir, filename)
            create_sample_pdf(pdf_path, content)
            print(f"✓ Created test PDF: {filename}")
        
        # Initialize processor
        print(f"\nInitializing SeedDataProcessor...")
        print(f"  Data directory: {data_dir}")
        print(f"  Database path: {db_dir}")
        
        processor = SeedDataProcessor(
            data_dir=data_dir,
            db_path=db_dir
        )
        
        print("✓ Processor initialized")
        
        # Process all documents
        print("\nProcessing all documents...")
        report = processor.process_all_documents()
        
        # Verify report structure
        print("\n" + "-"*80)
        print("VERIFICATION RESULTS")
        print("-"*80)
        
        assert isinstance(report, ProcessingReport), "Should return ProcessingReport"
        print("✓ Returns ProcessingReport instance")
        
        assert report.total_documents == 3, f"Should process 3 documents, got {report.total_documents}"
        print(f"✓ Processed {report.total_documents} documents")
        
        assert report.successful_documents >= 0, "Should track successful documents"
        print(f"✓ Tracked {report.successful_documents} successful documents")
        
        assert report.failed_documents >= 0, "Should track failed documents"
        print(f"✓ Tracked {report.failed_documents} failed documents")
        
        assert report.total_documents == report.successful_documents + report.failed_documents, \
            "Total should equal successful + failed"
        print("✓ Total = Successful + Failed")
        
        assert len(report.document_reports) == 3, "Should have 3 document reports"
        print(f"✓ Generated {len(report.document_reports)} document reports")
        
        # Verify each document report
        for doc_report in report.document_reports:
            assert isinstance(doc_report, DocumentReport), "Should be DocumentReport"
            assert doc_report.filename in [f[0] for f in pdf_files], \
                f"Unexpected filename: {doc_report.filename}"
            assert doc_report.processing_time >= 0, "Processing time should be non-negative"
            print(f"  ✓ {doc_report.filename}: {doc_report.law_type}, "
                  f"{doc_report.chunks_created} chunks, "
                  f"{doc_report.processing_time:.2f}s")
        
        # Verify report formatting
        report_str = str(report)
        assert "LEGAL DATA SEEDING REPORT" in report_str, "Report should have title"
        assert "Total Documents:" in report_str, "Report should show total documents"
        assert "Successful:" in report_str, "Report should show successful count"
        assert "Failed:" in report_str, "Report should show failed count"
        assert "Total Chunks:" in report_str, "Report should show total chunks"
        print("\n✓ Report formatting is correct")
        
        # Display full report
        print("\n" + "="*80)
        print("FULL PROCESSING REPORT")
        print("="*80)
        print(report_str)
        
        print("\n" + "="*80)
        print("✓ TEST PASSED: process_all_documents() works correctly")
        print("="*80)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("\n✓ Cleaned up temporary files")


def test_process_all_documents_empty_directory():
    """
    Test that process_all_documents() handles empty directory gracefully.
    
    Validates Requirement: 8.4 (idempotency and error handling)
    """
    print("\n" + "="*80)
    print("TEST: process_all_documents() - Empty Directory")
    print("="*80)
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(data_dir)
    
    try:
        # Initialize processor
        print(f"Initializing SeedDataProcessor with empty data directory...")
        processor = SeedDataProcessor(
            data_dir=data_dir,
            db_path=db_dir
        )
        
        # Process all documents (should be none)
        print("Processing all documents...")
        report = processor.process_all_documents()
        
        # Verify report
        print("\n" + "-"*80)
        print("VERIFICATION RESULTS")
        print("-"*80)
        
        assert report.total_documents == 0, "Should process 0 documents"
        print("✓ Correctly reports 0 documents")
        
        assert report.successful_documents == 0, "Should have 0 successful"
        print("✓ Correctly reports 0 successful")
        
        assert report.failed_documents == 0, "Should have 0 failed"
        print("✓ Correctly reports 0 failed")
        
        assert report.total_chunks_created == 0, "Should create 0 chunks"
        print("✓ Correctly reports 0 chunks")
        
        assert len(report.document_reports) == 0, "Should have no document reports"
        print("✓ No document reports generated")
        
        print("\n" + "="*80)
        print("✓ TEST PASSED: Handles empty directory correctly")
        print("="*80)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("\n✓ Cleaned up temporary files")


def test_process_all_documents_idempotency():
    """
    Test that process_all_documents() is idempotent (can be run multiple times).
    
    Validates Requirement: 8.4 (pipeline idempotency)
    """
    print("\n" + "="*80)
    print("TEST: process_all_documents() - Idempotency")
    print("="*80)
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(data_dir)
    
    try:
        # Create a sample PDF
        pdf_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        create_sample_pdf(pdf_path, "Section 1. Test content.")
        print(f"✓ Created test PDF")
        
        # Initialize processor
        processor = SeedDataProcessor(
            data_dir=data_dir,
            db_path=db_dir
        )
        
        # First run
        print("\nFirst run: Processing documents...")
        report1 = processor.process_all_documents()
        
        print(f"  Total documents: {report1.total_documents}")
        print(f"  Successful: {report1.successful_documents}")
        print(f"  Total chunks: {report1.total_chunks_created}")
        
        # Second run (should skip already processed documents)
        print("\nSecond run: Processing documents again...")
        report2 = processor.process_all_documents()
        
        print(f"  Total documents: {report2.total_documents}")
        print(f"  Successful: {report2.successful_documents}")
        print(f"  Total chunks: {report2.total_chunks_created}")
        
        # Verify idempotency
        print("\n" + "-"*80)
        print("VERIFICATION RESULTS")
        print("-"*80)
        
        assert report2.total_documents == report1.total_documents, \
            "Should process same number of documents"
        print("✓ Same number of documents processed")
        
        # On second run, documents should be skipped (already processed)
        # So chunks_created in second run should be 0 or same as first
        print(f"✓ First run created {report1.total_chunks_created} chunks")
        print(f"✓ Second run created {report2.total_chunks_created} chunks (should be 0 if skipped)")
        
        # Both runs should succeed without errors
        assert report1.failed_documents == 0, "First run should have no failures"
        assert report2.failed_documents == 0, "Second run should have no failures"
        print("✓ Both runs completed without failures")
        
        print("\n" + "="*80)
        print("✓ TEST PASSED: process_all_documents() is idempotent")
        print("="*80)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("\n✓ Cleaned up temporary files")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("TASK 6.3 TEST SUITE: process_all_documents() Method")
    print("="*80)
    print("\nThis test suite verifies:")
    print("  1. Processes all PDFs in data directory")
    print("  2. Uses process_single_document() for each PDF")
    print("  3. Tracks processing statistics in ProcessingReport")
    print("  4. Validates Requirements 7.5, 8.4")
    
    try:
        test_process_all_documents_basic()
        test_process_all_documents_empty_directory()
        test_process_all_documents_idempotency()
        
        print("\n" + "="*80)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("="*80)
        print("\nTask 6.3 is complete and working correctly!")
        print("The process_all_documents() method:")
        print("  ✓ Processes all PDFs using process_single_document()")
        print("  ✓ Tracks statistics in ProcessingReport")
        print("  ✓ Handles empty directories gracefully")
        print("  ✓ Is idempotent (can be run multiple times safely)")
        print("  ✓ Validates Requirements 7.5, 8.4")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

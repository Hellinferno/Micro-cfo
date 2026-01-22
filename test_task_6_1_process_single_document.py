"""
Test suite for Task 6.1: process_single_document() method

This test suite validates the complete document processing pipeline including:
- Duplicate detection and idempotency
- Law type detection from filename
- PDF processing with legal ingestion
- Chunk creation and storage
- Metadata storage for duplicate detection
- Error handling

Validates Requirements: 7.1, 7.2, 7.3, 7.4, 8.2
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.seed_data import SeedDataProcessor, DocumentReport, ProcessingMetadata


def create_test_pdf(content: str, output_path: str) -> None:
    """
    Create a simple test PDF with the given content.
    
    Args:
        content: Text content to include in PDF
        output_path: Path where PDF should be created
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(output_path, pagesize=letter)
        c.drawString(100, 750, content)
        c.save()
    except ImportError:
        # If reportlab not available, create a minimal PDF manually
        # This is a very basic PDF structure that PyPDF2 can read
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
100 750 Td
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
%%EOF"""
        with open(output_path, 'w') as f:
            f.write(pdf_content)


def test_process_single_document_success():
    """
    Test successful processing of a single document.
    
    Validates:
    - Document is processed successfully
    - Law type is detected from filename
    - Chunks are created and stored
    - Processing metadata is saved
    - Report contains correct statistics
    """
    print("\n" + "="*80)
    print("TEST: Process Single Document - Success Case")
    print("="*80)
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Create a test PDF with legal content
        pdf_path = os.path.join(data_dir, "CGST_Act_2017.pdf")
        legal_content = """
        Section 5: Levy and Collection
        
        The Central Goods and Services Tax on the supply of goods or services or both,
        except on the supply of alcoholic liquor for human consumption, shall be levied
        at such rates not exceeding twenty per cent, as may be notified by the Government
        on the recommendations of the Council and collected in such manner as may be prescribed.
        
        Provided that the rate of tax shall not exceed fourteen per cent with effect from
        such date as may be notified by the Government on the recommendations of the Council.
        """
        create_test_pdf(legal_content, pdf_path)
        
        print(f"\n✓ Created test PDF: {pdf_path}")
        
        # Initialize processor
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        print("✓ Initialized SeedDataProcessor")
        
        # Process the document
        print("\nProcessing document...")
        report = processor.process_single_document(pdf_path)
        
        # Validate report
        print(f"\nReport: {report}")
        
        assert report.success, f"Processing should succeed, but got error: {report.error_message}"
        assert report.filename == "CGST_Act_2017.pdf", f"Expected filename 'CGST_Act_2017.pdf', got '{report.filename}'"
        assert report.law_type == "GST", f"Expected law_type 'GST', got '{report.law_type}'"
        assert report.chunks_created > 0, f"Expected chunks > 0, got {report.chunks_created}"
        assert report.processing_time > 0, f"Expected processing_time > 0, got {report.processing_time}"
        assert report.error_message is None, f"Expected no error message, got '{report.error_message}'"
        
        print("\n✓ All assertions passed")
        print(f"  - Filename: {report.filename}")
        print(f"  - Law Type: {report.law_type}")
        print(f"  - Chunks Created: {report.chunks_created}")
        print(f"  - Processing Time: {report.processing_time:.2f}s")
        
        # Verify metadata was saved
        metadata = ProcessingMetadata.load_from_db(processor.vector_db, pdf_path)
        assert metadata is not None, "Processing metadata should be saved"
        assert metadata.file_path == pdf_path, f"Expected file_path '{pdf_path}', got '{metadata.file_path}'"
        assert metadata.law_type == "GST", f"Expected law_type 'GST', got '{metadata.law_type}'"
        assert metadata.chunks_created == report.chunks_created, f"Metadata chunks ({metadata.chunks_created}) should match report ({report.chunks_created})"
        
        print("\n✓ Processing metadata verified")
        print(f"  - File Hash: {metadata.file_hash[:16]}...")
        print(f"  - Timestamp: {metadata.processing_timestamp}")
        
        print("\n" + "="*80)
        print("TEST PASSED: Process Single Document - Success Case")
        print("="*80)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_process_single_document_idempotency():
    """
    Test that processing the same document twice is idempotent.
    
    Validates:
    - First processing succeeds and creates chunks
    - Second processing detects duplicate and skips
    - No duplicate chunks are created
    
    Validates Requirements: 8.2
    """
    print("\n" + "="*80)
    print("TEST: Process Single Document - Idempotency")
    print("="*80)
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Create a test PDF
        pdf_path = os.path.join(data_dir, "Income_Tax_Act_1961.pdf")
        legal_content = "Section 10: Exemptions - Income not included in total income"
        create_test_pdf(legal_content, pdf_path)
        
        print(f"\n✓ Created test PDF: {pdf_path}")
        
        # Initialize processor
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        print("✓ Initialized SeedDataProcessor")
        
        # First processing
        print("\nFirst processing...")
        report1 = processor.process_single_document(pdf_path)
        
        assert report1.success, f"First processing should succeed, but got error: {report1.error_message}"
        assert report1.chunks_created > 0, f"First processing should create chunks, got {report1.chunks_created}"
        
        print(f"✓ First processing succeeded")
        print(f"  - Chunks Created: {report1.chunks_created}")
        
        # Second processing (should be skipped)
        print("\nSecond processing (should skip)...")
        report2 = processor.process_single_document(pdf_path)
        
        assert report2.success, f"Second processing should succeed (skip), but got error: {report2.error_message}"
        assert report2.chunks_created == 0, f"Second processing should create 0 chunks (skipped), got {report2.chunks_created}"
        assert report2.law_type == "Skipped", f"Expected law_type 'Skipped', got '{report2.law_type}'"
        
        print(f"✓ Second processing correctly skipped")
        print(f"  - Chunks Created: {report2.chunks_created}")
        print(f"  - Law Type: {report2.law_type}")
        
        print("\n" + "="*80)
        print("TEST PASSED: Process Single Document - Idempotency")
        print("="*80)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_process_single_document_empty_pdf():
    """
    Test handling of empty or invalid PDF.
    
    Validates:
    - Empty PDFs are detected
    - Processing fails gracefully with appropriate error message
    - No chunks are created
    
    Validates Requirement: 4.5
    """
    print("\n" + "="*80)
    print("TEST: Process Single Document - Empty PDF")
    print("="*80)
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Create an empty PDF
        pdf_path = os.path.join(data_dir, "Empty_Document.pdf")
        create_test_pdf("", pdf_path)  # Empty content
        
        print(f"\n✓ Created empty test PDF: {pdf_path}")
        
        # Initialize processor
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        print("✓ Initialized SeedDataProcessor")
        
        # Process the empty document
        print("\nProcessing empty document...")
        report = processor.process_single_document(pdf_path)
        
        print(f"\nReport: {report}")
        
        # Empty PDFs should fail gracefully
        assert not report.success, "Processing empty PDF should fail"
        assert report.chunks_created == 0, f"Empty PDF should create 0 chunks, got {report.chunks_created}"
        assert report.error_message is not None, "Error message should be provided"
        assert "empty" in report.error_message.lower() or "invalid" in report.error_message.lower(), \
            f"Error message should mention 'empty' or 'invalid', got: {report.error_message}"
        
        print("\n✓ Empty PDF handled correctly")
        print(f"  - Success: {report.success}")
        print(f"  - Chunks Created: {report.chunks_created}")
        print(f"  - Error Message: {report.error_message}")
        
        print("\n" + "="*80)
        print("TEST PASSED: Process Single Document - Empty PDF")
        print("="*80)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_process_single_document_file_not_found():
    """
    Test handling of non-existent file.
    
    Validates:
    - FileNotFoundError is caught
    - Processing fails gracefully with appropriate error message
    """
    print("\n" + "="*80)
    print("TEST: Process Single Document - File Not Found")
    print("="*80)
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Initialize processor
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        print("✓ Initialized SeedDataProcessor")
        
        # Try to process non-existent file
        pdf_path = os.path.join(data_dir, "NonExistent.pdf")
        print(f"\nProcessing non-existent file: {pdf_path}")
        report = processor.process_single_document(pdf_path)
        
        print(f"\nReport: {report}")
        
        # Should fail gracefully
        assert not report.success, "Processing non-existent file should fail"
        assert report.chunks_created == 0, f"Non-existent file should create 0 chunks, got {report.chunks_created}"
        assert report.error_message is not None, "Error message should be provided"
        assert "not found" in report.error_message.lower(), \
            f"Error message should mention 'not found', got: {report.error_message}"
        
        print("\n✓ File not found handled correctly")
        print(f"  - Success: {report.success}")
        print(f"  - Error Message: {report.error_message}")
        
        print("\n" + "="*80)
        print("TEST PASSED: Process Single Document - File Not Found")
        print("="*80)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_law_type_detection():
    """
    Test that law type is correctly detected from various filenames.
    
    Validates Requirement: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    print("\n" + "="*80)
    print("TEST: Law Type Detection from Filenames")
    print("="*80)
    
    from legal_ingestion import detect_law_type_from_filename
    
    test_cases = [
        ("CGST_Act_2017.pdf", "GST"),
        ("IGST_Act_2017.pdf", "GST"),
        ("Income_Tax_Act_1961.pdf", "Income Tax"),
        ("IT_Act_Amendments.pdf", "Income Tax"),
        ("Companies_Act_2013.pdf", "Corporate Law"),
        ("MCA_Guidelines.pdf", "Corporate Law"),
        ("PLI_Textiles_Guidelines.pdf", "Subsidy Scheme"),
        ("Scheme_Document.pdf", "Subsidy Scheme"),
        ("Random_Document.pdf", "General"),
    ]
    
    print("\nTesting law type detection:")
    for filename, expected_law_type in test_cases:
        detected = detect_law_type_from_filename(filename)
        status = "✓" if detected == expected_law_type else "✗"
        print(f"  {status} {filename:40s} -> {detected:20s} (expected: {expected_law_type})")
        assert detected == expected_law_type, f"Expected '{expected_law_type}' for '{filename}', got '{detected}'"
    
    print("\n" + "="*80)
    print("TEST PASSED: Law Type Detection from Filenames")
    print("="*80)


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*80)
    print("RUNNING ALL TESTS FOR TASK 6.1")
    print("="*80)
    
    tests = [
        ("Law Type Detection", test_law_type_detection),
        ("Process Single Document - Success", test_process_single_document_success),
        ("Process Single Document - Idempotency", test_process_single_document_idempotency),
        ("Process Single Document - Empty PDF", test_process_single_document_empty_pdf),
        ("Process Single Document - File Not Found", test_process_single_document_file_not_found),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"  Error: {e}")
        except Exception as e:
            failed += 1
            print(f"\n✗ TEST ERROR: {test_name}")
            print(f"  Exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
    
    print("="*80)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

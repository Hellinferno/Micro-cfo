"""
Verification test for Task 1: Create project structure and data models

This test verifies that:
1. The scripts/ directory exists
2. The data/initial_acts/ directory exists
3. LegalDocumentSource dataclass is properly defined
4. DocumentReport dataclass is properly defined
5. ProcessingReport dataclass is properly defined
6. All dataclasses have the expected attributes and methods
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from scripts.seed_downloader import LegalDocumentSource, LEGAL_SOURCES
from scripts.seed_data import DocumentReport, ProcessingReport, ProcessingMetadata, ProgressTracker


def test_directory_structure():
    """Test that required directories exist."""
    print("Testing directory structure...")
    
    # Check scripts directory
    assert os.path.exists("scripts"), "scripts/ directory should exist"
    assert os.path.isdir("scripts"), "scripts/ should be a directory"
    print("  ✓ scripts/ directory exists")
    
    # Check data/initial_acts directory
    assert os.path.exists("data/initial_acts"), "data/initial_acts/ directory should exist"
    assert os.path.isdir("data/initial_acts"), "data/initial_acts/ should be a directory"
    print("  ✓ data/initial_acts/ directory exists")
    
    # Check that seed_downloader.py exists
    assert os.path.exists("scripts/seed_downloader.py"), "seed_downloader.py should exist"
    print("  ✓ scripts/seed_downloader.py exists")
    
    # Check that seed_data.py exists
    assert os.path.exists("scripts/seed_data.py"), "seed_data.py should exist"
    print("  ✓ scripts/seed_data.py exists")
    
    print("✓ Directory structure test passed\n")


def test_legal_document_source():
    """Test LegalDocumentSource dataclass."""
    print("Testing LegalDocumentSource dataclass...")
    
    # Create instance
    source = LegalDocumentSource(
        url="https://example.gov.in/test.pdf",
        filename="test.pdf",
        description="Test Document",
        law_type="GST"
    )
    
    # Check attributes
    assert source.url == "https://example.gov.in/test.pdf"
    assert source.filename == "test.pdf"
    assert source.description == "Test Document"
    assert source.law_type == "GST"
    print("  ✓ All attributes accessible")
    
    # Check validate_url method
    assert source.validate_url() == True, "HTTPS URL should be valid"
    print("  ✓ validate_url() method works")
    
    # Check get_local_path method
    local_path = source.get_local_path("./data/initial_acts/")
    assert str(local_path).endswith("test.pdf"), "Local path should end with filename"
    print("  ✓ get_local_path() method works")
    
    # Check that LEGAL_SOURCES is defined and has 5 documents
    assert len(LEGAL_SOURCES) == 5, "Should have 5 legal sources configured"
    print(f"  ✓ LEGAL_SOURCES configured with {len(LEGAL_SOURCES)} documents")
    
    print("✓ LegalDocumentSource test passed\n")


def test_document_report():
    """Test DocumentReport dataclass."""
    print("Testing DocumentReport dataclass...")
    
    # Create successful report
    report = DocumentReport(
        filename="test.pdf",
        law_type="GST",
        chunks_created=42,
        processing_time=1.5,
        success=True
    )
    
    # Check attributes
    assert report.filename == "test.pdf"
    assert report.law_type == "GST"
    assert report.chunks_created == 42
    assert report.processing_time == 1.5
    assert report.success == True
    assert report.error_message is None
    print("  ✓ All attributes accessible")
    
    # Check __str__ method
    report_str = str(report)
    assert "SUCCESS" in report_str
    assert "test.pdf" in report_str
    assert "42 chunks" in report_str
    print("  ✓ __str__() method works for successful report")
    
    # Create failed report
    failed_report = DocumentReport(
        filename="bad.pdf",
        law_type="Unknown",
        chunks_created=0,
        processing_time=0.1,
        success=False,
        error_message="File not found"
    )
    
    failed_str = str(failed_report)
    assert "FAILED" in failed_str
    assert "File not found" in failed_str
    print("  ✓ __str__() method works for failed report")
    
    print("✓ DocumentReport test passed\n")


def test_processing_report():
    """Test ProcessingReport dataclass."""
    print("Testing ProcessingReport dataclass...")
    
    # Create empty report
    report = ProcessingReport()
    
    # Check initial values
    assert report.total_documents == 0
    assert report.successful_documents == 0
    assert report.failed_documents == 0
    assert report.total_chunks_created == 0
    assert report.total_processing_time == 0.0
    assert len(report.document_reports) == 0
    print("  ✓ Initial values correct")
    
    # Add successful document report
    doc_report1 = DocumentReport(
        filename="doc1.pdf",
        law_type="GST",
        chunks_created=10,
        processing_time=1.0,
        success=True
    )
    report.add_document_report(doc_report1)
    
    assert report.total_documents == 1
    assert report.successful_documents == 1
    assert report.failed_documents == 0
    assert report.total_chunks_created == 10
    assert report.total_processing_time == 1.0
    print("  ✓ add_document_report() works for successful report")
    
    # Add failed document report
    doc_report2 = DocumentReport(
        filename="doc2.pdf",
        law_type="Unknown",
        chunks_created=0,
        processing_time=0.5,
        success=False,
        error_message="Error"
    )
    report.add_document_report(doc_report2)
    
    assert report.total_documents == 2
    assert report.successful_documents == 1
    assert report.failed_documents == 1
    assert report.total_chunks_created == 10  # Should not increase for failed docs
    assert report.total_processing_time == 1.5
    print("  ✓ add_document_report() works for failed report")
    
    # Check __str__ method
    report_str = str(report)
    assert "LEGAL DATA SEEDING REPORT" in report_str
    assert "Total Documents:     2" in report_str
    assert "Successful:          1" in report_str
    assert "Failed:              1" in report_str
    print("  ✓ __str__() method generates report")
    
    print("✓ ProcessingReport test passed\n")


def test_processing_metadata():
    """Test ProcessingMetadata dataclass."""
    print("Testing ProcessingMetadata dataclass...")
    
    # Create metadata
    metadata = ProcessingMetadata(
        file_path="./data/test.pdf",
        file_hash="abc123",
        processing_timestamp="2024-01-01T00:00:00",
        chunks_created=15,
        law_type="GST"
    )
    
    # Check attributes
    assert metadata.file_path == "./data/test.pdf"
    assert metadata.file_hash == "abc123"
    assert metadata.processing_timestamp == "2024-01-01T00:00:00"
    assert metadata.chunks_created == 15
    assert metadata.law_type == "GST"
    print("  ✓ All attributes accessible")
    
    # Check to_dict method
    metadata_dict = metadata.to_dict()
    assert metadata_dict['file_path'] == "./data/test.pdf"
    assert metadata_dict['file_hash'] == "abc123"
    assert metadata_dict['chunks_created'] == 15
    print("  ✓ to_dict() method works")
    
    # Check from_dict method
    restored = ProcessingMetadata.from_dict(metadata_dict)
    assert restored.file_path == metadata.file_path
    assert restored.file_hash == metadata.file_hash
    assert restored.chunks_created == metadata.chunks_created
    print("  ✓ from_dict() method works")
    
    print("✓ ProcessingMetadata test passed\n")


def test_progress_tracker():
    """Test ProgressTracker class."""
    print("Testing ProgressTracker class...")
    
    # Create tracker
    tracker = ProgressTracker(total_items=5, operation_name="Test Operation")
    
    # Check attributes
    assert tracker.total_items == 5
    assert tracker.operation_name == "Test Operation"
    assert tracker.current_item == 0
    print("  ✓ Initialization works")
    
    # Test update method (should not raise exception)
    try:
        tracker.update(1, "Processing item 1")
        tracker.update(2, "Processing item 2")
        print("  ✓ update() method works")
    except Exception as e:
        raise AssertionError(f"update() method failed: {e}")
    
    # Test complete method (should not raise exception)
    try:
        tracker.complete("All done")
        print("  ✓ complete() method works")
    except Exception as e:
        raise AssertionError(f"complete() method failed: {e}")
    
    print("✓ ProgressTracker test passed\n")


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("Task 1 Verification: Create project structure and data models")
    print("=" * 70)
    print()
    
    try:
        test_directory_structure()
        test_legal_document_source()
        test_document_report()
        test_processing_report()
        test_processing_metadata()
        test_progress_tracker()
        
        print("=" * 70)
        print("✓ ALL TESTS PASSED - Task 1 Complete!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ scripts/ directory created")
        print("  ✓ data/initial_acts/ directory created")
        print("  ✓ LegalDocumentSource dataclass defined and working")
        print("  ✓ DocumentReport dataclass defined and working")
        print("  ✓ ProcessingReport dataclass defined and working")
        print("  ✓ ProcessingMetadata dataclass defined and working")
        print("  ✓ ProgressTracker class defined and working")
        print()
        print("Requirements validated: 10.1, 10.2")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())

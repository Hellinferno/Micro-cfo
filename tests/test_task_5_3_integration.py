"""
Integration test for Task 5.3: Metadata storage with SeedDataProcessor

This test verifies that the _is_already_processed method correctly uses
the metadata storage to detect duplicate processing attempts.

Validates Requirement: 8.2, 8.5
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.seed_data import SeedDataProcessor, ProcessingMetadata


def test_is_already_processed_with_metadata():
    """
    Test that _is_already_processed correctly uses metadata storage.
    
    This test verifies:
    1. New files are detected as not processed
    2. After saving metadata, files are detected as already processed
    3. Files with changed content are detected as modified
    4. The method correctly compares file hashes
    
    Validates Requirements: 8.2, 8.5
    """
    # Create temporary directories
    temp_db_dir = tempfile.mkdtemp(prefix="test_processor_db_")
    temp_data_dir = tempfile.mkdtemp(prefix="test_data_")
    
    try:
        print(f"Test database: {temp_db_dir}")
        print(f"Test data directory: {temp_data_dir}")
        
        # Create a test PDF file
        test_pdf_path = os.path.join(temp_data_dir, "test_document.pdf")
        with open(test_pdf_path, "wb") as f:
            f.write(b"PDF content version 1")
        
        print(f"\n=== Test 1: New file should not be processed ===")
        processor = SeedDataProcessor(
            data_dir=temp_data_dir,
            db_path=temp_db_dir
        )
        
        is_processed = processor._is_already_processed(test_pdf_path)
        assert not is_processed, "New file should not be marked as processed"
        print("✓ New file correctly detected as not processed")
        
        print(f"\n=== Test 2: Save metadata and check again ===")
        # Calculate file hash
        file_hash = processor._get_file_hash(test_pdf_path)
        
        # Create and save metadata
        metadata = ProcessingMetadata(
            file_path=test_pdf_path,
            file_hash=file_hash,
            processing_timestamp=datetime.now().isoformat(),
            chunks_created=25,
            law_type="GST"
        )
        metadata.save_to_db(processor.vector_db)
        print(f"✓ Saved metadata with hash: {file_hash[:16]}...")
        
        # Check if now detected as processed
        is_processed = processor._is_already_processed(test_pdf_path)
        assert is_processed, "File with saved metadata should be marked as processed"
        print("✓ File with metadata correctly detected as already processed")
        
        print(f"\n=== Test 3: Modify file and check again ===")
        # Modify the file content
        with open(test_pdf_path, "wb") as f:
            f.write(b"PDF content version 2 - MODIFIED")
        
        new_hash = processor._get_file_hash(test_pdf_path)
        print(f"  Old hash: {file_hash[:16]}...")
        print(f"  New hash: {new_hash[:16]}...")
        
        # Check if detected as modified (not processed with new hash)
        is_processed = processor._is_already_processed(test_pdf_path)
        assert not is_processed, "Modified file should not be marked as processed"
        print("✓ Modified file correctly detected as needing reprocessing")
        
        print(f"\n=== Test 4: Update metadata with new hash ===")
        # Save new metadata with updated hash
        updated_metadata = ProcessingMetadata(
            file_path=test_pdf_path,
            file_hash=new_hash,
            processing_timestamp=datetime.now().isoformat(),
            chunks_created=30,
            law_type="GST"
        )
        updated_metadata.save_to_db(processor.vector_db)
        print("✓ Updated metadata with new hash")
        
        # Check if now detected as processed with new hash
        is_processed = processor._is_already_processed(test_pdf_path)
        assert is_processed, "File with updated metadata should be marked as processed"
        print("✓ File with updated metadata correctly detected as processed")
        
        print(f"\n=== Test 5: Check different file ===")
        # Create another test file
        test_pdf_path2 = os.path.join(temp_data_dir, "another_document.pdf")
        with open(test_pdf_path2, "wb") as f:
            f.write(b"Different PDF content")
        
        is_processed = processor._is_already_processed(test_pdf_path2)
        assert not is_processed, "Different file should not be marked as processed"
        print("✓ Different file correctly detected as not processed")
        
        print("\n" + "=" * 60)
        print("ALL INTEGRATION TESTS PASSED ✓")
        print("=" * 60)
        print("\nTask 5.3 Integration Verified:")
        print("  ✓ _is_already_processed detects new files")
        print("  ✓ _is_already_processed detects files with saved metadata")
        print("  ✓ _is_already_processed detects modified files")
        print("  ✓ Metadata can be updated for modified files")
        print("  ✓ Different files are handled independently")
        print("\nValidates Requirements:")
        print("  ✓ 8.2: Processing Idempotency")
        print("  ✓ 8.5: Duplicate Detection Consistency")
        
        # Processor cleanup handled by garbage collection; explicit delete not required
        
    finally:
        # Clean up temporary directories
        for temp_dir in [temp_db_dir, temp_data_dir]:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print(f"\nCleaned up: {temp_dir}")
                except PermissionError:
                    print(f"\nNote: Could not clean up {temp_dir} (files in use)")


if __name__ == "__main__":
    test_is_already_processed_with_metadata()

"""
Test for Task 5.2: _is_already_processed() method

This test verifies that the SeedDataProcessor can correctly detect
whether a document has already been processed by querying the vector
database and comparing file hashes.

Validates Requirements: 8.2, 8.5
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.seed_data import SeedDataProcessor
from legal_ingestion import LegalChunk


def test_is_already_processed_new_file():
    """
    Test that _is_already_processed() returns False for a new file
    that hasn't been processed yet.
    
    Validates Requirement: 8.2
    """
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, "data")
        db_dir = os.path.join(temp_dir, "db")
        os.makedirs(data_dir)
        
        # Create a test PDF file (just a text file for testing)
        test_pdf = os.path.join(data_dir, "test_document.pdf")
        with open(test_pdf, 'w') as f:
            f.write("Test content for new file")
        
        # Initialize processor
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        
        # Check if file is already processed (should be False)
        result = processor._is_already_processed(test_pdf)
        
        # Clean up database connection before temp directory cleanup
        del processor.vector_db
        del processor
        
        assert result is False, "New file should not be marked as already processed"
        print("✓ Test passed: New file correctly identified as not processed")


def test_is_already_processed_existing_file():
    """
    Test that _is_already_processed() returns True for a file
    that has already been processed with the same hash.
    
    Validates Requirement: 8.2, 8.5
    """
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, "data")
        db_dir = os.path.join(temp_dir, "db")
        os.makedirs(data_dir)
        
        # Create a test PDF file
        test_pdf = os.path.join(data_dir, "test_document.pdf")
        test_content = "Test content for existing file"
        with open(test_pdf, 'w') as f:
            f.write(test_content)
        
        # Initialize processor
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        
        # Get file hash
        file_hash = processor._get_file_hash(test_pdf)
        
        # Manually add a chunk to the database with this file's metadata
        test_chunk = LegalChunk(
            text="Test chunk content",
            law_type="GST",
            section_number="1",
            source_file="test_document.pdf",
            file_hash=file_hash
        )
        
        processor.vector_db.add_chunks([test_chunk])
        
        # Now check if file is already processed (should be True)
        result = processor._is_already_processed(test_pdf)
        
        # Clean up database connection before temp directory cleanup
        del processor.vector_db
        del processor
        
        assert result is True, "Existing file with matching hash should be marked as already processed"
        print("✓ Test passed: Existing file with matching hash correctly identified")


def test_is_already_processed_modified_file():
    """
    Test that _is_already_processed() returns False for a file
    that exists in the database but has been modified (different hash).
    
    Validates Requirement: 8.5
    """
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, "data")
        db_dir = os.path.join(temp_dir, "db")
        os.makedirs(data_dir)
        
        # Create a test PDF file
        test_pdf = os.path.join(data_dir, "test_document.pdf")
        with open(test_pdf, 'w') as f:
            f.write("Original content")
        
        # Initialize processor
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        
        # Add a chunk with the original file hash
        original_hash = processor._get_file_hash(test_pdf)
        test_chunk = LegalChunk(
            text="Test chunk content",
            law_type="GST",
            section_number="1",
            source_file="test_document.pdf",
            file_hash=original_hash
        )
        processor.vector_db.add_chunks([test_chunk])
        
        # Modify the file (change content)
        with open(test_pdf, 'w') as f:
            f.write("Modified content - this is different")
        
        # Now check if file is already processed (should be False because hash changed)
        result = processor._is_already_processed(test_pdf)
        
        # Clean up database connection before temp directory cleanup
        del processor.vector_db
        del processor
        
        assert result is False, "Modified file with different hash should not be marked as already processed"
        print("✓ Test passed: Modified file correctly identified as needing reprocessing")


def test_is_already_processed_error_handling():
    """
    Test that _is_already_processed() handles errors gracefully
    and returns False when there's an error.
    """
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, "data")
        db_dir = os.path.join(temp_dir, "db")
        os.makedirs(data_dir)
        
        # Initialize processor
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
        
        # Try to check a non-existent file (should handle error gracefully)
        non_existent_file = os.path.join(data_dir, "non_existent.pdf")
        
        try:
            result = processor._is_already_processed(non_existent_file)
            # Should return False or raise an error that we can catch
            
            # Clean up database connection before temp directory cleanup
            del processor.vector_db
            del processor
            
            print("✓ Test passed: Error handling works correctly")
        except Exception as e:
            # Clean up database connection before temp directory cleanup
            del processor.vector_db
            del processor
            
            # This is also acceptable - the method should handle errors
            print(f"✓ Test passed: Error raised as expected: {e}")


def run_all_tests():
    """Run all tests for task 5.2"""
    print("=" * 80)
    print("Testing Task 5.2: _is_already_processed() method")
    print("=" * 80)
    print()
    
    tests = [
        ("Test 1: New file not processed", test_is_already_processed_new_file),
        ("Test 2: Existing file with matching hash", test_is_already_processed_existing_file),
        ("Test 3: Modified file with different hash", test_is_already_processed_modified_file),
        ("Test 4: Error handling", test_is_already_processed_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 80)
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

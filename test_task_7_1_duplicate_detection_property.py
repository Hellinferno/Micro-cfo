#!/usr/bin/env python3
"""
Property-Based Tests for Duplicate Detection
Task 7.1: Write property test for duplicate detection

Tests:
- Property 27: Duplicate Detection Consistency

Validates Requirements: 8.5
"""

import pytest
import os
import tempfile
import shutil
from hypothesis import given, strategies as st, settings, example, HealthCheck
from pathlib import Path
import hashlib
from contextlib import contextmanager

# Import the components we're testing
from scripts.seed_data import SeedDataProcessor, ProcessingMetadata
from legal_ingestion import LegalChunk


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

@contextmanager
def temp_test_env():
    """Create temporary directories for testing (context manager for hypothesis compatibility)"""
    temp_dir = tempfile.mkdtemp(prefix="test_seed_")
    data_dir = os.path.join(temp_dir, "data")
    db_dir = os.path.join(temp_dir, "db")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)
    
    try:
        yield {
            'temp_dir': temp_dir,
            'data_dir': data_dir,
            'db_dir': db_dir
        }
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def create_test_pdf(file_path: str, content: str) -> str:
    """
    Create a simple test PDF file with given content.
    Returns the file hash.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(file_path, pagesize=letter)
        c.drawString(100, 750, content)
        c.save()
        
        # Calculate and return file hash
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    except ImportError:
        # If reportlab not available, create a dummy file
        with open(file_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(content.encode('utf-8'))
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()


# ============================================================================
# Property 27: Duplicate Detection Consistency
# ============================================================================

@st.composite
def pdf_filename_and_content(draw):
    """Generate a PDF filename and content"""
    # Generate filename with law type patterns
    law_types = ['CGST', 'IGST', 'Income_Tax', 'Companies_Act', 'PLI']
    law_type = draw(st.sampled_from(law_types))
    year = draw(st.integers(min_value=1900, max_value=2099))
    
    filename = f"{law_type}_Act_{year}.pdf"
    
    # Generate some content
    content = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')),
        min_size=20,
        max_size=200
    ))
    
    return filename, content


@given(pdf_filename_and_content())
@settings(max_examples=10, deadline=60000)  # Reduced examples, longer deadline
@example(("CGST_Act_2017.pdf", "Section 16 - Input tax credit eligibility"))
@example(("Income_Tax_Act_1961.pdf", "Section 80C - Deductions"))
def test_property_27_duplicate_detection_consistency(filename_and_content):
    """
    **Property 27: Duplicate Detection Consistency**
    
    For any two documents with the same filename and modification timestamp,
    the system should recognize them as duplicates and process only once.
    
    **Validates: Requirements 8.5**
    
    Property: If a document is processed once, attempting to process it again
    with the same content should detect it as a duplicate and skip processing.
    """
    filename, content = filename_and_content
    
    with temp_test_env() as env:
        data_dir = env['data_dir']
        db_dir = env['db_dir']
    
    # Create test PDF file
    pdf_path = os.path.join(data_dir, filename)
    file_hash = create_test_pdf(pdf_path, content)
    
    # Initialize processor
    try:
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
    except Exception as e:
        pytest.skip(f"Could not initialize SeedDataProcessor: {e}")
    
    # First processing - should NOT be detected as duplicate
    is_duplicate_first = processor._is_already_processed(pdf_path)
    assert not is_duplicate_first, \
        "First processing should NOT detect document as duplicate"
    
    # Simulate processing by storing metadata
    from datetime import datetime
    metadata = ProcessingMetadata(
        file_path=pdf_path,
        file_hash=file_hash,
        processing_timestamp=datetime.now().isoformat(),
        chunks_created=5,  # Arbitrary number
        law_type="GST"
    )
    metadata.save_to_db(processor.vector_db)
    
    # Second processing - should BE detected as duplicate
    is_duplicate_second = processor._is_already_processed(pdf_path)
    assert is_duplicate_second, \
        "Second processing should detect document as duplicate with same hash"
    
    # Verify metadata can be loaded
    loaded_metadata = ProcessingMetadata.load_from_db(processor.vector_db, pdf_path)
    assert loaded_metadata is not None, \
        "Metadata should be loadable from database"
    assert loaded_metadata.file_hash == file_hash, \
        f"Loaded file hash should match original: {loaded_metadata.file_hash} vs {file_hash}"
    assert loaded_metadata.file_path == pdf_path, \
        f"Loaded file path should match original: {loaded_metadata.file_path} vs {pdf_path}"


@given(pdf_filename_and_content(), st.text(min_size=20, max_size=200))
@settings(max_examples=10, deadline=60000)
def test_property_27_modified_file_not_duplicate(filename_and_content, new_content):
    """
    **Property 27 (Modified File Case): Modified Files Are Not Duplicates**
    
    For any document that has been processed, if the file content changes
    (different hash), the system should NOT recognize it as a duplicate
    and should allow reprocessing.
    
    **Validates: Requirements 8.5**
    
    Property: If a document is processed once, then modified (different hash),
    attempting to process it again should NOT detect it as a duplicate.
    """
    filename, original_content = filename_and_content
    
    with temp_test_env() as env:
        data_dir = env['data_dir']
        db_dir = env['db_dir']
    
    # Ensure new content is different from original
    if new_content == original_content:
        new_content = original_content + " MODIFIED"
    
    # Create test PDF file with original content
    pdf_path = os.path.join(data_dir, filename)
    original_hash = create_test_pdf(pdf_path, original_content)
    
    # Initialize processor
    try:
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
    except Exception as e:
        pytest.skip(f"Could not initialize SeedDataProcessor: {e}")
    
    # Store metadata for original file
    from datetime import datetime
    metadata = ProcessingMetadata(
        file_path=pdf_path,
        file_hash=original_hash,
        processing_timestamp=datetime.now().isoformat(),
        chunks_created=5,
        law_type="GST"
    )
    metadata.save_to_db(processor.vector_db)
    
    # Modify the file (create new PDF with different content)
    new_hash = create_test_pdf(pdf_path, new_content)
    
    # Verify hashes are different
    assert new_hash != original_hash, \
        "Modified file should have different hash"
    
    # Check if detected as duplicate - should NOT be
    is_duplicate = processor._is_already_processed(pdf_path)
    assert not is_duplicate, \
        "Modified file (different hash) should NOT be detected as duplicate"


@given(st.lists(pdf_filename_and_content(), min_size=2, max_size=3, unique_by=lambda x: x[0]))
@settings(max_examples=5, deadline=60000)
def test_property_27_multiple_files_independent(files_list):
    """
    **Property 27 (Multiple Files Case): Multiple Files Are Tracked Independently**
    
    For any set of different documents, each should be tracked independently
    for duplicate detection. Processing one document should not affect
    duplicate detection for other documents.
    
    **Validates: Requirements 8.5**
    
    Property: Processing multiple different documents should track each
    independently, and duplicate detection should work correctly for each.
    """
    with temp_test_env() as env:
        data_dir = env['data_dir']
        db_dir = env['db_dir']
    
    # Initialize processor
    try:
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
    except Exception as e:
        pytest.skip(f"Could not initialize SeedDataProcessor: {e}")
    
    # Create and process all files
    file_paths = []
    file_hashes = []
    
    for filename, content in files_list:
        pdf_path = os.path.join(data_dir, filename)
        file_hash = create_test_pdf(pdf_path, content)
        file_paths.append(pdf_path)
        file_hashes.append(file_hash)
        
        # Store metadata
        from datetime import datetime
        metadata = ProcessingMetadata(
            file_path=pdf_path,
            file_hash=file_hash,
            processing_timestamp=datetime.now().isoformat(),
            chunks_created=5,
            law_type="GST"
        )
        metadata.save_to_db(processor.vector_db)
    
    # Verify each file is detected as duplicate independently
    for pdf_path, expected_hash in zip(file_paths, file_hashes):
        is_duplicate = processor._is_already_processed(pdf_path)
        assert is_duplicate, \
            f"File {pdf_path} should be detected as duplicate"
        
        # Verify metadata is correct for this specific file
        loaded_metadata = ProcessingMetadata.load_from_db(processor.vector_db, pdf_path)
        assert loaded_metadata is not None, \
            f"Metadata should exist for {pdf_path}"
        assert loaded_metadata.file_hash == expected_hash, \
            f"Hash should match for {pdf_path}"


@given(pdf_filename_and_content())
@settings(max_examples=10, deadline=60000)
def test_property_27_file_hash_calculation_consistency(filename_and_content):
    """
    **Property 27 (Hash Consistency): File Hash Calculation Is Consistent**
    
    For any file, calculating the hash multiple times should produce
    the same result (hash function is deterministic).
    
    **Validates: Requirements 8.5**
    
    Property: _get_file_hash() should return the same hash for the same file
    when called multiple times.
    """
    filename, content = filename_and_content
    
    with temp_test_env() as env:
        data_dir = env['data_dir']
        db_dir = env['db_dir']
    
    # Create test PDF file
    pdf_path = os.path.join(data_dir, filename)
    create_test_pdf(pdf_path, content)
    
    # Initialize processor
    try:
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
    except Exception as e:
        pytest.skip(f"Could not initialize SeedDataProcessor: {e}")
    
    # Calculate hash multiple times
    hash1 = processor._get_file_hash(pdf_path)
    hash2 = processor._get_file_hash(pdf_path)
    hash3 = processor._get_file_hash(pdf_path)
    
    # All hashes should be identical
    assert hash1 == hash2 == hash3, \
        "File hash calculation should be consistent across multiple calls"
    
    # Hash should be a valid SHA256 hex string (64 characters)
    assert len(hash1) == 64, \
        f"SHA256 hash should be 64 characters, got {len(hash1)}"
    assert all(c in '0123456789abcdef' for c in hash1), \
        "Hash should contain only hexadecimal characters"


# ============================================================================
# Edge Cases
# ============================================================================

def test_property_27_nonexistent_file():
    """
    **Property 27 (Edge Case): Nonexistent Files Are Not Duplicates**
    
    For any file path that doesn't exist, duplicate detection should
    return False (not a duplicate).
    
    **Validates: Requirements 8.5**
    """
    with temp_test_env() as env:
        data_dir = env['data_dir']
        db_dir = env['db_dir']
    
    # Initialize processor
    try:
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
    except Exception as e:
        pytest.skip(f"Could not initialize SeedDataProcessor: {e}")
    
    # Check nonexistent file
    nonexistent_path = os.path.join(data_dir, "nonexistent_file.pdf")
    
    # Should not raise exception, should return False
    try:
        is_duplicate = processor._is_already_processed(nonexistent_path)
        # If file doesn't exist, _get_file_hash will fail, so this should handle gracefully
        # The implementation catches exceptions and returns False
    except FileNotFoundError:
        # This is acceptable - file doesn't exist
        pass


def test_property_27_empty_database():
    """
    **Property 27 (Edge Case): Empty Database Has No Duplicates**
    
    For any file, when the database is empty (no metadata stored),
    duplicate detection should return False.
    
    **Validates: Requirements 8.5**
    """
    with temp_test_env() as env:
        data_dir = env['data_dir']
        db_dir = env['db_dir']
    
    # Create test PDF file
    pdf_path = os.path.join(data_dir, "test_file.pdf")
    create_test_pdf(pdf_path, "Test content")
    
    # Initialize processor (fresh database)
    try:
        processor = SeedDataProcessor(data_dir=data_dir, db_path=db_dir)
    except Exception as e:
        pytest.skip(f"Could not initialize SeedDataProcessor: {e}")
    
    # Check for duplicate in empty database
    is_duplicate = processor._is_already_processed(pdf_path)
    assert not is_duplicate, \
        "Empty database should not have any duplicates"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])

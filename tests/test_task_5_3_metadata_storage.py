"""
Test for Task 5.3: Add metadata storage to vector database

This test verifies that ProcessingMetadata can be saved to and loaded from
the vector database, enabling idempotent operations.

Validates Requirement: 8.5
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.seed_data import ProcessingMetadata
from vector_database import LegalVectorDB


def test_metadata_save_and_load():
    """
    Test that ProcessingMetadata can be saved to and loaded from the database.
    
    This test verifies:
    1. Metadata can be saved to the vector database
    2. Metadata can be loaded back with the same values
    3. Loading non-existent metadata returns None
    4. Metadata round-trip preserves all fields
    
    Validates Requirement: 8.5
    """
    # Create temporary database directory
    temp_db_dir = tempfile.mkdtemp(prefix="test_metadata_db_")
    
    try:
        # Initialize vector database
        print(f"Initializing test database at: {temp_db_dir}")
        vector_db = LegalVectorDB(db_path=temp_db_dir)
        
        # Create test metadata
        test_metadata = ProcessingMetadata(
            file_path="./data/initial_acts/CGST_Act_2017.pdf",
            file_hash="abc123def456",
            processing_timestamp=datetime.now().isoformat(),
            chunks_created=42,
            law_type="GST"
        )
        
        print("\n=== Test 1: Save metadata ===")
        test_metadata.save_to_db(vector_db)
        print("✓ Metadata saved successfully")
        
        print("\n=== Test 2: Load metadata ===")
        loaded_metadata = ProcessingMetadata.load_from_db(
            vector_db,
            "./data/initial_acts/CGST_Act_2017.pdf"
        )
        
        assert loaded_metadata is not None, "Loaded metadata should not be None"
        print(f"✓ Metadata loaded successfully")
        
        print("\n=== Test 3: Verify all fields match ===")
        assert loaded_metadata.file_path == test_metadata.file_path, \
            f"file_path mismatch: {loaded_metadata.file_path} != {test_metadata.file_path}"
        print(f"  ✓ file_path: {loaded_metadata.file_path}")
        
        assert loaded_metadata.file_hash == test_metadata.file_hash, \
            f"file_hash mismatch: {loaded_metadata.file_hash} != {test_metadata.file_hash}"
        print(f"  ✓ file_hash: {loaded_metadata.file_hash}")
        
        assert loaded_metadata.processing_timestamp == test_metadata.processing_timestamp, \
            f"processing_timestamp mismatch"
        print(f"  ✓ processing_timestamp: {loaded_metadata.processing_timestamp}")
        
        assert loaded_metadata.chunks_created == test_metadata.chunks_created, \
            f"chunks_created mismatch: {loaded_metadata.chunks_created} != {test_metadata.chunks_created}"
        print(f"  ✓ chunks_created: {loaded_metadata.chunks_created}")
        
        assert loaded_metadata.law_type == test_metadata.law_type, \
            f"law_type mismatch: {loaded_metadata.law_type} != {test_metadata.law_type}"
        print(f"  ✓ law_type: {loaded_metadata.law_type}")
        
        print("\n=== Test 4: Load non-existent metadata ===")
        non_existent = ProcessingMetadata.load_from_db(
            vector_db,
            "./data/initial_acts/NonExistent.pdf"
        )
        
        assert non_existent is None, "Non-existent metadata should return None"
        print("✓ Non-existent metadata returns None as expected")
        
        print("\n=== Test 5: Update existing metadata (upsert) ===")
        updated_metadata = ProcessingMetadata(
            file_path="./data/initial_acts/CGST_Act_2017.pdf",
            file_hash="xyz789updated",
            processing_timestamp=datetime.now().isoformat(),
            chunks_created=50,
            law_type="GST"
        )
        
        updated_metadata.save_to_db(vector_db)
        print("✓ Updated metadata saved")
        
        reloaded_metadata = ProcessingMetadata.load_from_db(
            vector_db,
            "./data/initial_acts/CGST_Act_2017.pdf"
        )
        
        assert reloaded_metadata.file_hash == "xyz789updated", \
            "Updated hash should be reflected"
        assert reloaded_metadata.chunks_created == 50, \
            "Updated chunks_created should be reflected"
        print("✓ Metadata update (upsert) works correctly")
        
        print("\n=== Test 6: Get all processed files ===")
        # Add another metadata entry
        another_metadata = ProcessingMetadata(
            file_path="./data/initial_acts/Income_Tax_Act_1961.pdf",
            file_hash="it123hash",
            processing_timestamp=datetime.now().isoformat(),
            chunks_created=100,
            law_type="Income Tax"
        )
        another_metadata.save_to_db(vector_db)
        
        all_processed = vector_db.get_all_processed_files()
        assert len(all_processed) >= 2, f"Should have at least 2 processed files, got {len(all_processed)}"
        print(f"✓ Found {len(all_processed)} processed files")
        
        for processed in all_processed:
            print(f"  - {processed['file_path']}: {processed['law_type']}, {processed['chunks_created']} chunks")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nTask 5.3 Implementation Verified:")
        print("  ✓ ProcessingMetadata can be saved to vector database")
        print("  ✓ ProcessingMetadata can be loaded from vector database")
        print("  ✓ Metadata round-trip preserves all fields")
        print("  ✓ Non-existent metadata returns None")
        print("  ✓ Metadata can be updated (upsert)")
        print("  ✓ All processed files can be retrieved")
        print("\nValidates Requirement 8.5: Duplicate Detection Consistency")
        
        # Close database connection before cleanup
        del vector_db
        
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db_dir):
            try:
                shutil.rmtree(temp_db_dir)
                print(f"\nCleaned up test database: {temp_db_dir}")
            except PermissionError:
                print(f"\nNote: Could not clean up {temp_db_dir} (files in use)")
                print("This is normal on Windows and will be cleaned up on next reboot")


if __name__ == "__main__":
    test_metadata_save_and_load()

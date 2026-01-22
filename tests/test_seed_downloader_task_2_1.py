"""
Test for Task 2.1: SeedDownloader initialization and directory creation

This test verifies that the SeedDownloader class properly:
1. Initializes with a configurable output directory
2. Creates the output directory if it doesn't exist
3. Handles errors properly during directory creation

Requirements: 10.1, 10.5
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from seed_downloader import SeedDownloader


def test_initialization_with_default_directory():
    """Test that SeedDownloader initializes with default directory."""
    downloader = SeedDownloader()
    assert downloader.output_dir == "./data/initial_acts/"
    print("✓ Default directory initialization works")


def test_initialization_with_custom_directory():
    """Test that SeedDownloader initializes with custom directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_dir = os.path.join(temp_dir, "custom_output")
        downloader = SeedDownloader(output_dir=custom_dir)
        assert downloader.output_dir == custom_dir
        assert os.path.exists(custom_dir)
        print("✓ Custom directory initialization works")


def test_directory_creation():
    """Test that output directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "test_output", "nested", "path")
        
        # Verify directory doesn't exist before initialization
        assert not os.path.exists(output_dir)
        
        # Initialize downloader
        downloader = SeedDownloader(output_dir=output_dir)
        
        # Verify directory was created
        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)
        print("✓ Directory creation works for nested paths")


def test_directory_already_exists():
    """Test that initialization works when directory already exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "existing_dir")
        
        # Create directory before initialization
        os.makedirs(output_dir)
        assert os.path.exists(output_dir)
        
        # Initialize downloader (should not fail)
        downloader = SeedDownloader(output_dir=output_dir)
        
        # Verify directory still exists
        assert os.path.exists(output_dir)
        print("✓ Initialization works with existing directory")


def test_error_handling_invalid_path():
    """Test error handling when directory creation fails."""
    # Try to create directory in a location that should fail
    # (using a file path as directory)
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file
        file_path = os.path.join(temp_dir, "test_file.txt")
        with open(file_path, 'w') as f:
            f.write("test")
        
        # Try to create a directory with the same name as the file
        invalid_dir = os.path.join(file_path, "subdir")
        
        try:
            downloader = SeedDownloader(output_dir=invalid_dir)
            assert False, "Should have raised OSError"
        except OSError as e:
            print(f"✓ Error handling works: {str(e)}")


def test_directory_permissions():
    """Test that created directory has proper read/write permissions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "perm_test")
        
        # Initialize downloader
        downloader = SeedDownloader(output_dir=output_dir)
        
        # Test write permission by creating a file
        test_file = os.path.join(output_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Test read permission
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert content == "test content"
        print("✓ Directory has proper read/write permissions")


def run_all_tests():
    """Run all tests for task 2.1."""
    print("=" * 60)
    print("Testing Task 2.1: SeedDownloader Initialization")
    print("=" * 60)
    
    tests = [
        test_initialization_with_default_directory,
        test_initialization_with_custom_directory,
        test_directory_creation,
        test_directory_already_exists,
        test_error_handling_invalid_path,
        test_directory_permissions,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\nRunning: {test.__name__}")
            test()
            passed += 1
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

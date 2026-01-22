#!/usr/bin/env python3
"""
Property-Based Tests for File Validator
Tests multi-format file support validation

Feature: frontend-backend-integration
Property 10: Multi-format File Support
Validates: Requirements 4.5
"""

import pytest
import tempfile
import os
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from file_validator import (
    FileFormatDetector,
    PDFValidator,
    ImageValidator,
    ComprehensiveFileValidator,
    FileFormat,
    FileValidationError
)


# ============================================================================
# Test Data Generators
# ============================================================================

def create_valid_pdf(file_path: Path) -> None:
    """Create a minimal valid PDF file"""
    pdf_content = b"""%PDF-1.4
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
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
190
%%EOF
"""
    with open(file_path, 'wb') as f:
        f.write(pdf_content)


def create_valid_png(file_path: Path) -> None:
    """Create a minimal valid PNG file (1x1 pixel)"""
    png_content = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR'  # IHDR chunk
        b'\x00\x00\x00\x01'  # Width: 1
        b'\x00\x00\x00\x01'  # Height: 1
        b'\x08\x02\x00\x00\x00'  # Bit depth, color type, etc.
        b'\x90wS\xde'  # CRC
        b'\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'  # IDAT chunk
        b'\x00\x00\x00\x00IEND\xae\x42\x60\x82'  # IEND chunk
    )
    with open(file_path, 'wb') as f:
        f.write(png_content)


def create_valid_jpeg(file_path: Path) -> None:
    """Create a minimal valid JPEG file"""
    jpeg_content = (
        b'\xff\xd8\xff\xe0'  # SOI + APP0 marker
        b'\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'  # JFIF header
        b'\xff\xdb\x00C'  # DQT marker
        b'\x00' + (b'\x08' * 64) +  # Quantization table
        b'\xff\xc0\x00\x0b'  # SOF0 marker
        b'\x08\x00\x01\x00\x01\x01\x01\x11\x00'  # Frame header (1x1 image)
        b'\xff\xda\x00\x08'  # SOS marker
        b'\x01\x01\x00\x00?\x00'  # Scan header
        b'\xd2\xcf \xff\xd9'  # Compressed data + EOI
    )
    with open(file_path, 'wb') as f:
        f.write(jpeg_content)


def create_corrupted_pdf(file_path: Path) -> None:
    """Create a corrupted PDF (missing EOF marker)"""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
>>
endobj
"""
    with open(file_path, 'wb') as f:
        f.write(pdf_content)


def create_corrupted_png(file_path: Path) -> None:
    """Create a corrupted PNG (missing IEND chunk)"""
    png_content = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR'  # IHDR chunk
        b'\x00\x00\x00\x01'  # Width: 1
        b'\x00\x00\x00\x01'  # Height: 1
        b'\x08\x02\x00\x00\x00'  # Bit depth, color type, etc.
        b'\x90wS\xde'  # CRC
        # Missing IEND chunk
    )
    with open(file_path, 'wb') as f:
        f.write(png_content)


def create_corrupted_jpeg(file_path: Path) -> None:
    """Create a corrupted JPEG (missing EOI marker)"""
    jpeg_content = (
        b'\xff\xd8\xff\xe0'  # SOI + APP0 marker
        b'\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'  # JFIF header
        # Missing EOI marker
    )
    with open(file_path, 'wb') as f:
        f.write(jpeg_content)


def create_file_with_wrong_extension(file_path: Path, actual_format: str) -> None:
    """Create a file with mismatched extension and content"""
    if actual_format == "pdf":
        create_valid_pdf(file_path)
    elif actual_format == "png":
        create_valid_png(file_path)
    elif actual_format == "jpeg":
        create_valid_jpeg(file_path)


# ============================================================================
# Property 10: Multi-format File Support
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    file_format=st.sampled_from(['pdf', 'png', 'jpeg'])
)
def test_property_10_valid_format_detection(file_format: str):
    """
    Feature: frontend-backend-integration, Property 10: Multi-format File Support
    
    Property: For any file in the supported formats (PDF, PNG, JPEG),
    the Integration Layer should correctly identify the format based on content,
    validate it, and process it successfully.
    
    Validates: Requirements 4.5
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a valid file of the specified format
        file_path = Path(tmpdir) / f"test.{file_format}"
        
        if file_format == 'pdf':
            create_valid_pdf(file_path)
            expected_format = FileFormat.PDF
        elif file_format == 'png':
            create_valid_png(file_path)
            expected_format = FileFormat.PNG
        elif file_format == 'jpeg':
            create_valid_jpeg(file_path)
            expected_format = FileFormat.JPEG
        
        # Property: Format detection should correctly identify the format
        detected_format = FileFormatDetector.detect_format(file_path)
        assert detected_format == expected_format, \
            f"Expected {expected_format}, but detected {detected_format}"
        
        # Property: Comprehensive validation should succeed for valid files
        validated_format = ComprehensiveFileValidator.validate_uploaded_file(
            file_path, file_path.name
        )
        assert validated_format == expected_format, \
            f"Validation returned {validated_format}, expected {expected_format}"


@settings(max_examples=100, deadline=None)
@given(
    actual_format=st.sampled_from(['pdf', 'png', 'jpeg']),
    wrong_extension=st.sampled_from(['pdf', 'png', 'jpeg', 'txt', 'doc'])
)
def test_property_10_content_based_detection(actual_format: str, wrong_extension: str):
    """
    Feature: frontend-backend-integration, Property 10: Multi-format File Support
    
    Property: For any file, format detection should be based on content (magic bytes)
    rather than file extension, preventing malicious files from bypassing validation.
    
    Validates: Requirements 4.5
    """
    # Skip if extension matches actual format (not testing wrong extension case)
    assume(actual_format != wrong_extension)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create file with wrong extension but correct content
        file_path = Path(tmpdir) / f"test.{wrong_extension}"
        create_file_with_wrong_extension(file_path, actual_format)
        
        # Property: Detection should be based on content, not extension
        detected_format = FileFormatDetector.detect_format(file_path)
        
        if actual_format == 'pdf':
            assert detected_format == FileFormat.PDF
        elif actual_format == 'png':
            assert detected_format == FileFormat.PNG
        elif actual_format == 'jpeg':
            assert detected_format == FileFormat.JPEG


@settings(max_examples=100, deadline=None)
@given(
    file_format=st.sampled_from(['pdf', 'png', 'jpeg'])
)
def test_property_10_corruption_detection(file_format: str):
    """
    Feature: frontend-backend-integration, Property 10: Multi-format File Support
    
    Property: For any corrupted file in supported formats, the validator should
    detect the corruption and raise appropriate errors.
    
    Validates: Requirements 4.5
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a corrupted file of the specified format
        file_path = Path(tmpdir) / f"corrupted.{file_format}"
        
        if file_format == 'pdf':
            create_corrupted_pdf(file_path)
        elif file_format == 'png':
            create_corrupted_png(file_path)
        elif file_format == 'jpeg':
            create_corrupted_jpeg(file_path)
        
        # Property: Corrupted files should be detected and rejected
        with pytest.raises(FileValidationError) as exc_info:
            ComprehensiveFileValidator.validate_uploaded_file(
                file_path, file_path.name
            )
        
        # Verify error message indicates corruption
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in [
            'corrupt', 'invalid', 'missing', 'eof', 'iend', 'eoi'
        ]), f"Error message should indicate corruption: {error_msg}"


@settings(max_examples=100, deadline=None)
@given(
    random_bytes=st.binary(min_size=100, max_size=1000)
)
def test_property_10_unknown_format_rejection(random_bytes: bytes):
    """
    Feature: frontend-backend-integration, Property 10: Multi-format File Support
    
    Property: For any file with unknown or unsupported format, the validator
    should reject it with appropriate error.
    
    Validates: Requirements 4.5
    """
    # Skip if random bytes happen to match a valid format signature
    assume(not random_bytes.startswith(b'%PDF-'))
    assume(not random_bytes.startswith(b'\x89PNG'))
    assume(not random_bytes.startswith(b'\xff\xd8\xff'))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "unknown.bin"
        with open(file_path, 'wb') as f:
            f.write(random_bytes)
        
        # Property: Unknown formats should be rejected
        with pytest.raises(FileValidationError) as exc_info:
            ComprehensiveFileValidator.validate_uploaded_file(
                file_path, file_path.name
            )
        
        # Verify error message indicates unknown format
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in [
            'unknown', 'unsupported', 'format'
        ]), f"Error message should indicate unknown format: {error_msg}"


@settings(max_examples=100, deadline=None)
@given(
    file_format=st.sampled_from(['pdf', 'png', 'jpeg'])
)
def test_property_10_format_specific_validation(file_format: str):
    """
    Feature: frontend-backend-integration, Property 10: Multi-format File Support
    
    Property: For any file format, format-specific validation should be performed
    (PDF structure, PNG chunks, JPEG markers) to ensure file integrity.
    
    Validates: Requirements 4.5
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / f"test.{file_format}"
        
        # Create valid file
        if file_format == 'pdf':
            create_valid_pdf(file_path)
        elif file_format == 'png':
            create_valid_png(file_path)
        elif file_format == 'jpeg':
            create_valid_jpeg(file_path)
        
        # Property: Format-specific validation should pass for valid files
        if file_format == 'pdf':
            is_valid, error = PDFValidator.validate_structure(file_path)
            assert is_valid, f"PDF validation failed: {error}"
            assert error is None
        elif file_format == 'png':
            is_valid, error = ImageValidator.validate_png(file_path)
            assert is_valid, f"PNG validation failed: {error}"
            assert error is None
        elif file_format == 'jpeg':
            is_valid, error = ImageValidator.validate_jpeg(file_path)
            assert is_valid, f"JPEG validation failed: {error}"
            assert error is None


# ============================================================================
# Unit Tests for Edge Cases
# ============================================================================

def test_empty_file_rejection():
    """Test that empty files are rejected"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "empty.pdf"
        file_path.touch()  # Create empty file
        
        with pytest.raises(FileValidationError) as exc_info:
            ComprehensiveFileValidator.validate_uploaded_file(file_path)
        
        assert "empty" in str(exc_info.value).lower()


def test_nonexistent_file_rejection():
    """Test that nonexistent files are rejected"""
    file_path = Path("/nonexistent/file.pdf")
    
    with pytest.raises(FileValidationError) as exc_info:
        ComprehensiveFileValidator.validate_uploaded_file(file_path)
    
    assert "does not exist" in str(exc_info.value).lower()


def test_pdf_with_invalid_version():
    """Test PDF with invalid version number"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "invalid_version.pdf"
        with open(file_path, 'wb') as f:
            f.write(b'%PDF-9.9\n%%EOF')  # Invalid version
        
        is_valid, error = PDFValidator.validate_structure(file_path)
        assert not is_valid
        assert "version" in error.lower()


def test_png_with_zero_dimensions():
    """Test PNG with zero width or height"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "zero_dims.png"
        png_content = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR'
            b'\x00\x00\x00\x00'  # Width: 0
            b'\x00\x00\x00\x00'  # Height: 0
            b'\x08\x02\x00\x00\x00'
            b'\x90wS\xde'
            b'\x00\x00\x00\x00IEND\xae\x42\x60\x82'
        )
        with open(file_path, 'wb') as f:
            f.write(png_content)
        
        is_valid, error = ImageValidator.validate_png(file_path)
        assert not is_valid
        assert "dimension" in error.lower()


def test_jpeg_without_soi():
    """Test JPEG without Start of Image marker"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "no_soi.jpg"
        with open(file_path, 'wb') as f:
            f.write(b'\x00\x00\xff\xd9')  # No SOI, just EOI
        
        is_valid, error = ImageValidator.validate_jpeg(file_path)
        assert not is_valid
        assert "soi" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

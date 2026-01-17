#!/usr/bin/env python3
"""
File Format Validator for MicroCFO Integration Server
Provides comprehensive file format detection and validation based on content, not just extensions.

Requirements: 4.5
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class FileFormat(Enum):
    """Supported file formats"""
    PDF = "pdf"
    PNG = "png"
    JPEG = "jpeg"
    UNKNOWN = "unknown"


class FileValidationError(Exception):
    """Exception raised when file validation fails"""
    pass


class FileFormatDetector:
    """
    Detects file format based on content (magic bytes) rather than extension.
    
    This provides more reliable file type detection and prevents malicious files
    from bypassing validation by using incorrect extensions.
    
    Requirements: 4.5
    """
    
    # Magic bytes for supported formats
    MAGIC_BYTES = {
        FileFormat.PDF: [
            b'%PDF-',  # PDF signature
        ],
        FileFormat.PNG: [
            b'\x89PNG\r\n\x1a\n',  # PNG signature
        ],
        FileFormat.JPEG: [
            b'\xff\xd8\xff\xe0',  # JPEG/JFIF
            b'\xff\xd8\xff\xe1',  # JPEG/Exif
            b'\xff\xd8\xff\xe2',  # JPEG with ICC profile
            b'\xff\xd8\xff\xe3',  # JPEG
            b'\xff\xd8\xff\xe8',  # JPEG
            b'\xff\xd8\xff\xdb',  # JPEG raw
            b'\xff\xd8\xff\xee',  # JPEG
        ],
    }
    
    @classmethod
    def detect_format(cls, file_path: Path) -> FileFormat:
        """
        Detect file format by reading magic bytes from file content.
        
        Args:
            file_path: Path to the file to detect
            
        Returns:
            FileFormat enum value
            
        Raises:
            FileValidationError: If file cannot be read
        """
        try:
            with open(file_path, 'rb') as f:
                # Read first 16 bytes (enough for all our magic byte checks)
                header = f.read(16)
                
            # Check against known magic bytes
            for file_format, magic_bytes_list in cls.MAGIC_BYTES.items():
                for magic_bytes in magic_bytes_list:
                    if header.startswith(magic_bytes):
                        logger.debug(f"Detected format {file_format.value} for {file_path.name}")
                        return file_format
            
            logger.warning(f"Unknown file format for {file_path.name}")
            return FileFormat.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise FileValidationError(f"Cannot read file: {str(e)}")
    
    @classmethod
    def validate_format(cls, file_path: Path, expected_formats: list[FileFormat]) -> FileFormat:
        """
        Validate that file matches one of the expected formats.
        
        Args:
            file_path: Path to the file to validate
            expected_formats: List of acceptable FileFormat values
            
        Returns:
            Detected FileFormat
            
        Raises:
            FileValidationError: If format doesn't match expected formats
        """
        detected_format = cls.detect_format(file_path)
        
        if detected_format == FileFormat.UNKNOWN:
            raise FileValidationError(
                f"Unknown or unsupported file format for {file_path.name}"
            )
        
        if detected_format not in expected_formats:
            expected_names = [f.value for f in expected_formats]
            raise FileValidationError(
                f"File format {detected_format.value} not allowed. "
                f"Expected one of: {', '.join(expected_names)}"
            )
        
        return detected_format


class PDFValidator:
    """
    Validates PDF file structure to detect corruption or malformed files.
    
    Requirements: 4.5
    """
    
    @staticmethod
    def validate_structure(file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF file structure.
        
        Checks for:
        - Valid PDF header
        - EOF marker presence
        - Basic structure integrity
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'rb') as f:
                # Read header
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    return False, "Invalid PDF header"
                
                # Check PDF version
                try:
                    version_str = header[5:8].decode('ascii')
                    version = float(version_str)
                    if version < 1.0 or version > 2.0:
                        return False, f"Invalid PDF version: {version}"
                except:
                    return False, "Invalid PDF version format"
                
                # Read last 1KB to check for EOF marker
                f.seek(-min(1024, file_path.stat().st_size), 2)
                tail = f.read()
                
                if b'%%EOF' not in tail:
                    return False, "Missing PDF EOF marker (file may be corrupted)"
                
                # Check for xref table or cross-reference stream
                if b'xref' not in tail and b'/XRef' not in tail:
                    logger.warning("PDF missing xref table (may be corrupted)")
                    # Don't fail, as some PDFs use alternative structures
                
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating PDF structure: {str(e)}")
            return False, f"PDF validation error: {str(e)}"


class ImageValidator:
    """
    Validates image file structure to detect corruption or malformed files.
    
    Requirements: 4.5
    """
    
    @staticmethod
    def validate_png(file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate PNG file structure.
        
        Checks for:
        - Valid PNG signature
        - IHDR chunk presence
        - IEND chunk presence
        
        Args:
            file_path: Path to PNG file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'rb') as f:
                # Check PNG signature
                signature = f.read(8)
                if signature != b'\x89PNG\r\n\x1a\n':
                    return False, "Invalid PNG signature"
                
                # Check for IHDR chunk (must be first)
                chunk_length = int.from_bytes(f.read(4), 'big')
                chunk_type = f.read(4)
                if chunk_type != b'IHDR':
                    return False, "Missing or invalid IHDR chunk"
                
                # Read IHDR data
                ihdr_data = f.read(chunk_length)
                if len(ihdr_data) != 13:  # IHDR is always 13 bytes
                    return False, "Invalid IHDR chunk size"
                
                # Extract dimensions
                width = int.from_bytes(ihdr_data[0:4], 'big')
                height = int.from_bytes(ihdr_data[4:8], 'big')
                
                if width == 0 or height == 0:
                    return False, "Invalid PNG dimensions (zero width or height)"
                
                if width > 65535 or height > 65535:
                    logger.warning(f"Very large PNG dimensions: {width}x{height}")
                
                # Check for IEND chunk at end
                f.seek(-12, 2)  # IEND chunk is 12 bytes
                iend_length = int.from_bytes(f.read(4), 'big')
                iend_type = f.read(4)
                
                if iend_type != b'IEND' or iend_length != 0:
                    return False, "Missing or invalid IEND chunk (file may be corrupted)"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating PNG structure: {str(e)}")
            return False, f"PNG validation error: {str(e)}"
    
    @staticmethod
    def validate_jpeg(file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate JPEG file structure.
        
        Checks for:
        - Valid JPEG SOI marker
        - Valid JPEG EOI marker
        - Basic segment structure
        
        Args:
            file_path: Path to JPEG file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'rb') as f:
                # Check SOI (Start of Image) marker
                soi = f.read(2)
                if soi != b'\xff\xd8':
                    return False, "Invalid JPEG SOI marker"
                
                # Read next marker to verify it's a valid JPEG segment
                marker = f.read(2)
                if not marker.startswith(b'\xff'):
                    return False, "Invalid JPEG segment marker"
                
                # Check for EOI (End of Image) marker at end
                f.seek(-2, 2)
                eoi = f.read(2)
                
                if eoi != b'\xff\xd9':
                    return False, "Missing JPEG EOI marker (file may be corrupted)"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating JPEG structure: {str(e)}")
            return False, f"JPEG validation error: {str(e)}"


class ComprehensiveFileValidator:
    """
    Comprehensive file validator that combines format detection and structure validation.
    
    This is the main interface for file validation in the integration server.
    
    Requirements: 4.5
    """
    
    SUPPORTED_FORMATS = [FileFormat.PDF, FileFormat.PNG, FileFormat.JPEG]
    
    @classmethod
    def validate_file(cls, file_path: Path) -> Tuple[FileFormat, bool, Optional[str]]:
        """
        Perform comprehensive file validation.
        
        Steps:
        1. Detect file format based on content (magic bytes)
        2. Validate format is supported
        3. Perform format-specific structure validation
        4. Check for corruption
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Tuple of (detected_format, is_valid, error_message)
            
        Raises:
            FileValidationError: If validation fails critically
        """
        # Step 1: Detect format
        try:
            detected_format = FileFormatDetector.detect_format(file_path)
        except FileValidationError as e:
            raise FileValidationError(f"Cannot detect file format: {str(e)}")
        
        # Step 2: Check if format is supported
        if detected_format == FileFormat.UNKNOWN:
            raise FileValidationError(
                "Unknown or unsupported file format. "
                "Supported formats: PDF, PNG, JPEG"
            )
        
        if detected_format not in cls.SUPPORTED_FORMATS:
            raise FileValidationError(
                f"File format {detected_format.value} is not supported"
            )
        
        # Step 3: Perform format-specific validation
        is_valid = True
        error_message = None
        
        if detected_format == FileFormat.PDF:
            is_valid, error_message = PDFValidator.validate_structure(file_path)
        elif detected_format == FileFormat.PNG:
            is_valid, error_message = ImageValidator.validate_png(file_path)
        elif detected_format == FileFormat.JPEG:
            is_valid, error_message = ImageValidator.validate_jpeg(file_path)
        
        if not is_valid:
            raise FileValidationError(
                f"File validation failed: {error_message}"
            )
        
        logger.info(
            f"File {file_path.name} validated successfully as {detected_format.value}"
        )
        
        return detected_format, is_valid, error_message
    
    @classmethod
    def validate_uploaded_file(
        cls,
        file_path: Path,
        filename: Optional[str] = None
    ) -> FileFormat:
        """
        Validate an uploaded file with comprehensive checks.
        
        This is a convenience method that raises FileValidationError on any issue.
        
        Args:
            file_path: Path to uploaded file
            filename: Original filename (for logging)
            
        Returns:
            Detected FileFormat
            
        Raises:
            FileValidationError: If validation fails
        """
        log_name = filename or file_path.name
        logger.info(f"Validating uploaded file: {log_name}")
        
        # Check file exists and is readable
        if not file_path.exists():
            raise FileValidationError(f"File does not exist: {log_name}")
        
        if not file_path.is_file():
            raise FileValidationError(f"Path is not a file: {log_name}")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise FileValidationError(f"File is empty: {log_name}")
        
        # Perform comprehensive validation
        detected_format, is_valid, error_message = cls.validate_file(file_path)
        
        return detected_format

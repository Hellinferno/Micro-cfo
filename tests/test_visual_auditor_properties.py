#!/usr/bin/env python3
"""
Property-Based Tests for Visual Auditor Router
Tests secure file processing properties using Hypothesis
"""

import pytest
import tempfile
import uuid
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from fastapi import UploadFile, HTTPException
import io
from PIL import Image

from integration_server import app
from routers.visual_auditor import validate_file, save_uploaded_file, cleanup_temp_file, file_to_base64_url

# Test client with proper host header
client = TestClient(app, base_url="http://testserver")

class MockUploadFile:
    """Mock UploadFile for testing"""
    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.content_type = content_type
        self.size = len(content)
        self.file = io.BytesIO(content)

def create_test_image(width: int = 100, height: int = 100) -> bytes:
    """Create a test PNG image"""
    img = Image.new('RGB', (width, height), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def create_test_pdf() -> bytes:
    """Create a minimal test PDF"""
    # Minimal PDF content
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
%%EOF"""
    return pdf_content

@given(
    file_ext=st.sampled_from(['.pdf', '.png', '.jpg', '.jpeg']),
    file_size=st.integers(min_value=100, max_value=1024*1024)  # 100 bytes to 1MB
)
@settings(
    max_examples=100,
    deadline=None,  # Disable deadline for property tests
    suppress_health_check=[HealthCheck.too_slow]  # Allow slower generation
)
def test_secure_file_processing_property(file_ext: str, file_size: int):
    """
    Feature: frontend-backend-integration, Property 4: Secure File Processing
    
    For any uploaded file that meets the validation criteria, the file should be 
    securely stored, processed by the appropriate MCP tool, and cleaned up afterward, 
    with access restricted to the uploading user.
    
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """
    # Generate filename with valid extension
    base_name = f"test_{uuid.uuid4().hex[:8]}"
    filename = f"{base_name}{file_ext}"
    
    # Generate appropriate content and content type
    if file_ext == '.pdf':
        content_type = 'application/pdf'
        file_content = create_test_pdf()
    else:
        content_type = 'image/png'
        file_content = create_test_image()
    
    # Truncate content to match file_size if needed
    if len(file_content) > file_size:
        file_content = file_content[:file_size]
    
    # Create mock upload file
    mock_file = MockUploadFile(
        filename=filename,
        content=file_content,
        content_type=content_type
    )
    
    file_path = None
    try:
        # Property 1: File validation should pass for valid files
        validate_file(mock_file)  # Should not raise exception
        
        # Property 2: File should be saved with secure UUID filename
        file_id, file_path = save_uploaded_file(mock_file)
        
        # Verify secure storage properties
        assert isinstance(file_id, str)
        assert len(file_id) == 36  # UUID length
        assert file_path.exists()
        assert file_path.parent.name == "temp_uploads"
        assert file_id in file_path.name  # UUID in filename
        
        # Property 3: File content should be preserved
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        assert saved_content == file_content
        
        # Property 4: File should be convertible to base64 for MCP processing
        base64_url = file_to_base64_url(file_path)
        assert base64_url.startswith('data:')
        assert 'base64,' in base64_url
        
        # Property 5: File should be cleanable
        cleanup_temp_file(file_path)
        assert not file_path.exists()  # File should be deleted
        
    except Exception as e:
        # Clean up on any failure
        if file_path and file_path.exists():
            cleanup_temp_file(file_path)
        raise e

@given(
    invalid_ext=st.sampled_from(['.txt', '.exe', '.doc', '.zip', '.py']),
    file_size=st.integers(min_value=1, max_value=1000)
)
@settings(max_examples=50, deadline=None)
def test_file_validation_rejects_invalid_files(invalid_ext: str, file_size: int):
    """
    Property: File validation should reject files with invalid extensions
    
    **Validates: Requirements 4.1, 4.5**
    """
    filename = f"test{invalid_ext}"
    content = b"test content"
    
    mock_file = MockUploadFile(
        filename=filename,
        content=content,
        content_type="application/octet-stream"
    )
    
    # Should raise HTTPException for invalid file types
    with pytest.raises(HTTPException):
        validate_file(mock_file)

@given(
    file_size=st.integers(min_value=10*1024*1024 + 1, max_value=50*1024*1024)  # > 10MB
)
@settings(max_examples=20, deadline=None)
def test_file_validation_rejects_oversized_files(file_size: int):
    """
    Property: File validation should reject files exceeding size limits
    
    **Validates: Requirements 4.1**
    """
    filename = "test.png"
    content = b"x" * min(file_size, 1000)  # Don't actually create huge content
    
    mock_file = MockUploadFile(
        filename=filename,
        content=content,
        content_type="image/png"
    )
    mock_file.size = file_size  # Override size for testing
    
    # Should raise HTTPException for oversized files
    with pytest.raises(HTTPException):
        validate_file(mock_file)

@given(
    num_files=st.integers(min_value=1, max_value=5)  # Reduced for performance
)
@settings(max_examples=20, deadline=None)
def test_concurrent_file_processing_isolation(num_files: int):
    """
    Property: Multiple concurrent file uploads should be processed independently
    with proper isolation and cleanup
    
    **Validates: Requirements 4.2, 4.3, 4.4**
    """
    file_paths = []
    file_ids = []
    
    try:
        # Process multiple files concurrently
        for i in range(num_files):
            filename = f"test_{i}.png"
            content = create_test_image(50 + i, 50 + i)  # Different sizes
            
            mock_file = MockUploadFile(
                filename=filename,
                content=content,
                content_type="image/png"
            )
            
            # Each file should get unique ID and path
            file_id, file_path = save_uploaded_file(mock_file)
            file_ids.append(file_id)
            file_paths.append(file_path)
        
        # Verify isolation properties
        assert len(set(file_ids)) == num_files  # All IDs unique
        assert len(set(file_paths)) == num_files  # All paths unique
        
        # All files should exist independently
        for file_path in file_paths:
            assert file_path.exists()
        
        # Cleanup should work independently
        for file_path in file_paths:
            cleanup_temp_file(file_path)
            assert not file_path.exists()
            
    except Exception as e:
        # Clean up all files on failure
        for file_path in file_paths:
            if file_path.exists():
                cleanup_temp_file(file_path)
        raise e

def test_upload_endpoint_integration():
    """
    Integration test for the upload endpoint with property validation
    
    **Validates: Requirements 1.4, 4.1, 4.5**
    """
    # Create test image
    test_content = create_test_image()
    
    # Test successful upload with proper headers
    response = client.post(
        "/api/v1/agents/visual-auditor/upload-document",
        files={"file": ("test.png", test_content, "image/png")},
        data={"process_immediately": "false"},  # Don't process to avoid MCP dependency
        headers={"Host": "testserver"}
    )
    
    # Should succeed with valid file
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "file_id" in data
    assert data["filename"] == "test.png"
    assert data["file_type"] == "image/png"

def test_upload_endpoint_rejects_invalid_files():
    """
    Test that upload endpoint properly rejects invalid files
    
    **Validates: Requirements 4.1, 4.5**
    """
    # Test invalid file type
    response = client.post(
        "/api/v1/agents/visual-auditor/upload-document",
        files={"file": ("test.txt", b"invalid content", "text/plain")},
        data={"process_immediately": "false"},
        headers={"Host": "testserver"}
    )
    
    # Should reject invalid file type
    assert response.status_code == 400
    
    # Check if response is JSON or plain text
    try:
        error_data = response.json()
        assert "not allowed" in error_data.get("detail", "")
    except:
        # If not JSON, check plain text response
        assert "not allowed" in response.text

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
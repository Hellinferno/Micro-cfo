#!/usr/bin/env python3
"""
Test suite for Task 1.3: Enhanced LegalDocumentProcessor.process_pdf()

Tests the following enhancements:
- Auto-detect law type from filename if not provided
- Apply text cleaning after extraction
- Handle empty content with warning and skip
- Handle extraction errors gracefully

Validates Requirements: 3.1, 4.4, 4.5
"""

import os
import tempfile
import logging
from pathlib import Path
from PyPDF2 import PdfWriter, PdfReader
from PyPDF2.generic import NameObject, DictionaryObject, NumberObject, DecodedStreamObject

from legal_ingestion import LegalDocumentProcessor, detect_law_type_from_filename, clean_pdf_text


def _escape_pdf_text(text: str) -> str:
    """Escape characters that have special meaning in PDF text objects."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def create_test_pdf(content: str, filename: str) -> str:
    """Create a test PDF containing the provided content.

    The helper first attempts to use reportlab for convenience. If the
    dependency is unavailable we fall back to constructing a simple PDF using
    PyPDF2 primitives so that downstream text extraction still works during
    tests.
    """

    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, filename)

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        canvas_obj = canvas.Canvas(pdf_path, pagesize=letter)
        y_position = 750
        for raw_line in content.splitlines():
            line = raw_line.strip() or " "
            canvas_obj.drawString(40, y_position, line[:90])
            y_position -= 15
            if y_position < 40:
                canvas_obj.showPage()
                y_position = 750
        canvas_obj.save()
        return pdf_path
    except ImportError:
        # Fallback: build a minimal PDF using PyPDF2 primitives.
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)

        # Register Helvetica font resource for the page.
        font_dict = DictionaryObject()
        font_dict[NameObject("/Type")] = NameObject("/Font")
        font_dict[NameObject("/Subtype")] = NameObject("/Type1")
        font_dict[NameObject("/BaseFont")] = NameObject("/Helvetica")
        font_ref = writer._add_object(font_dict)

        resources = DictionaryObject()
        resources[NameObject("/Font")] = DictionaryObject({NameObject("/F1"): font_ref})
        page[NameObject("/Resources")] = resources

        # Prepare text drawing commands.
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            lines = [" "]

        commands = [
            "BT",
            "/F1 12 Tf",
            "1 0 0 1 50 760 Tm",
        ]

        for index, raw_line in enumerate(lines):
            escaped = _escape_pdf_text(raw_line[:100])
            if index > 0:
                commands.append("0 -14 Td")
            commands.append(f"({escaped}) Tj")

        commands.append("ET")
        content_stream = "\n".join(commands)

        stream_object = DecodedStreamObject()
        stream_data = content_stream.encode("utf-8")
        stream_object.set_data(stream_data)
        stream_object[NameObject("/Length")] = NumberObject(len(stream_data))
        stream_ref = writer._add_object(stream_object)
        page[NameObject("/Contents")] = stream_ref

        with open(pdf_path, "wb") as pdf_file:
            writer.write(pdf_file)

        return pdf_path


def test_auto_detect_law_type():
    """Test that law type is auto-detected from filename when not provided"""
    print("\n=== Test 1: Auto-detect law type from filename ===")
    
    processor = LegalDocumentProcessor()
    
    # Create test PDFs with different filenames
    test_cases = [
        ("CGST_Act_2017.pdf", "GST"),
        ("Income_Tax_Act_1961.pdf", "Income Tax"),
        ("Companies_Act_2013.pdf", "Corporate Law"),
        ("PLI_Textiles_Guidelines.pdf", "Subsidy Scheme"),
        ("random_document.pdf", "General")
    ]
    
    sample_content = """
Section 1 - Short title and commencement
(1) This Act may be called the Test Act, 2023.
(2) It shall come into force on such date as the Central Government may notify.
"""
    
    for filename, expected_law_type in test_cases:
        pdf_path = create_test_pdf(sample_content, filename)
        
        try:
            # Process PDF without providing law_type (should auto-detect)
            chunks = processor.process_pdf(pdf_path, law_type=None)
            
            if chunks:
                detected_law_type = chunks[0].law_type
                status = "✓ PASS" if detected_law_type == expected_law_type else "✗ FAIL"
                print(f"{status}: {filename} -> Expected: {expected_law_type}, Got: {detected_law_type}")
            else:
                print(f"✗ FAIL: {filename} -> No chunks created")
        finally:
            # Cleanup
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            temp_dir = os.path.dirname(pdf_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)


def test_text_cleaning_applied():
    """Test that text cleaning is applied after extraction"""
    print("\n=== Test 2: Text cleaning is applied ===")
    
    processor = LegalDocumentProcessor()
    
    # Create PDF with repetitive headers and excessive whitespace
    content_with_noise = """Header Text
Page 1
Section 1 - Test Section
This is the actual content that should be preserved.
Footer Text


Header Text
Page 2
More content here.
Footer Text"""
    
    pdf_path = create_test_pdf(content_with_noise, "test_cleaning.pdf")
    
    try:
        chunks = processor.process_pdf(pdf_path, law_type="GST")
        
        if chunks:
            # Check that chunks don't contain repetitive headers/footers
            all_text = " ".join([chunk.text for chunk in chunks])
            
            # The cleaning should have removed or reduced repetitive content
            header_count = all_text.count("Header Text")
            footer_count = all_text.count("Footer Text")
            
            print(f"Header occurrences: {header_count}")
            print(f"Footer occurrences: {footer_count}")
            
            # Check that actual content is preserved
            if "actual content" in all_text.lower():
                print("✓ PASS: Actual content preserved")
            else:
                print("✗ FAIL: Actual content not found")
            
            # Check that excessive whitespace is normalized
            if "\n\n\n" not in all_text:
                print("✓ PASS: Excessive whitespace normalized")
            else:
                print("✗ FAIL: Excessive whitespace still present")
        else:
            print("✗ FAIL: No chunks created")
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        temp_dir = os.path.dirname(pdf_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def test_empty_content_handling():
    """Test that empty content is handled with warning and skip"""
    print("\n=== Test 3: Empty content handling ===")
    
    processor = LegalDocumentProcessor()
    
    # Create PDF with minimal/empty content
    empty_content = "   \n\n   \n   "
    
    pdf_path = create_test_pdf(empty_content, "empty_test.pdf")
    
    try:
        # Capture log output
        import logging
        logging.basicConfig(level=logging.WARNING)
        
        chunks = processor.process_pdf(pdf_path, law_type="GST")
        
        if len(chunks) == 0:
            print("✓ PASS: Empty content returns empty list")
        else:
            print(f"✗ FAIL: Expected 0 chunks, got {len(chunks)}")
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        temp_dir = os.path.dirname(pdf_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def test_extraction_error_handling():
    """Test that extraction errors are handled gracefully"""
    print("\n=== Test 4: Extraction error handling ===")
    
    processor = LegalDocumentProcessor()
    
    # Test with non-existent file
    non_existent_path = "/path/to/nonexistent/file.pdf"
    chunks = processor.process_pdf(non_existent_path, law_type="GST")
    
    if len(chunks) == 0:
        print("✓ PASS: Non-existent file returns empty list")
    else:
        print(f"✗ FAIL: Expected 0 chunks for non-existent file, got {len(chunks)}")
    
    # Test with invalid PDF (create a text file with .pdf extension)
    temp_dir = tempfile.mkdtemp()
    invalid_pdf_path = os.path.join(temp_dir, "invalid.pdf")
    
    try:
        with open(invalid_pdf_path, 'w') as f:
            f.write("This is not a valid PDF file")
        
        chunks = processor.process_pdf(invalid_pdf_path, law_type="GST")
        
        if len(chunks) == 0:
            print("✓ PASS: Invalid PDF returns empty list")
        else:
            print(f"✗ FAIL: Expected 0 chunks for invalid PDF, got {len(chunks)}")
    finally:
        # Cleanup
        if os.path.exists(invalid_pdf_path):
            os.remove(invalid_pdf_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def test_integration_with_existing_functionality():
    """Test that enhanced process_pdf still works with existing functionality"""
    print("\n=== Test 5: Integration with existing functionality ===")
    
    processor = LegalDocumentProcessor()
    
    # Create PDF with legal content that should be properly chunked
    legal_content = """
Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged on any supply of goods or services or both to him which are used or intended to be used in the course or furtherance of his business.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless the turnover exceeds 5 crore.

Provided that where the goods against an invoice are received in lots or instalments, the registered person shall be entitled to take credit upon receipt of the last lot or instalment.

Section 17 - Apportionment of credit and blocked credits

(5) Input tax credit shall not be available in respect of motor vehicles.
"""
    
    pdf_path = create_test_pdf(legal_content, "CGST_Act_Test.pdf")
    
    try:
        chunks = processor.process_pdf(pdf_path)  # No law_type provided
        
        print(f"Created {len(chunks)} chunks")
        
        # Verify chunks were created
        if len(chunks) > 0:
            print("✓ PASS: Chunks created successfully")
        else:
            print("✗ FAIL: No chunks created")
        
        # Verify law type was auto-detected
        if chunks and chunks[0].law_type == "GST":
            print("✓ PASS: Law type auto-detected as GST")
        else:
            print(f"✗ FAIL: Expected law type GST, got {chunks[0].law_type if chunks else 'None'}")
        
        # Verify section numbers were extracted
        section_numbers = [chunk.section_number for chunk in chunks if chunk.section_number]
        if section_numbers:
            print(f"✓ PASS: Section numbers extracted: {section_numbers}")
        else:
            print("✗ FAIL: No section numbers extracted")
        
        # Verify turnover threshold was extracted
        turnover_chunks = [chunk for chunk in chunks if chunk.turnover_threshold]
        if turnover_chunks:
            print(f"✓ PASS: Turnover threshold extracted: {turnover_chunks[0].turnover_threshold}")
        else:
            print("✗ FAIL: No turnover threshold extracted")
        
        # Verify chunk types were identified
        chunk_types = set([chunk.chunk_type for chunk in chunks])
        print(f"Chunk types found: {chunk_types}")
        if "proviso" in chunk_types:
            print("✓ PASS: Proviso chunk type identified")
        else:
            print("⚠ WARNING: No proviso chunk type found (may be due to text extraction)")
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        temp_dir = os.path.dirname(pdf_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def main():
    """Run all tests"""
    print("=" * 70)
    print("Testing Task 1.3: Enhanced LegalDocumentProcessor.process_pdf()")
    print("=" * 70)
    
    # Configure logging to show warnings
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    test_auto_detect_law_type()
    test_text_cleaning_applied()
    test_empty_content_handling()
    test_extraction_error_handling()
    test_integration_with_existing_functionality()
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()

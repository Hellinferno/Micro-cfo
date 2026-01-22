#!/usr/bin/env python3
"""
Test suite for clean_pdf_text() function (Task 1.2)
Tests requirement 4.2: Remove repetitive headers/footers, page numbers, and excessive whitespace
"""

import pytest
from legal_ingestion import clean_pdf_text


def test_remove_page_numbers_standalone():
    """Test removal of standalone page numbers"""
    text = """Section 1 - Introduction
This is the content of section 1.
1
Section 2 - Details
This is the content of section 2.
2"""
    
    cleaned = clean_pdf_text(text)
    
    # Page numbers should be removed
    assert "Section 1 - Introduction" in cleaned
    assert "This is the content of section 1." in cleaned
    assert "Section 2 - Details" in cleaned
    assert "This is the content of section 2." in cleaned
    # Standalone "1" and "2" should be removed
    lines = cleaned.split('\n')
    assert "1" not in [line.strip() for line in lines]
    assert "2" not in [line.strip() for line in lines]


def test_remove_page_numbers_with_prefix():
    """Test removal of page numbers with 'Page' prefix"""
    text = """Section 1 - Introduction
Content here
Page 1
Section 2 - Details
More content
Page 2"""
    
    cleaned = clean_pdf_text(text)
    
    # Page markers should be removed
    assert "Page 1" not in cleaned
    assert "Page 2" not in cleaned
    # Content should remain
    assert "Section 1 - Introduction" in cleaned
    assert "Content here" in cleaned


def test_remove_page_numbers_with_separators():
    """Test removal of page numbers with separators like '- 1 -'"""
    text = """Section 1 - Introduction
Content here
- 1 -
Section 2 - Details
More content
| 2 |"""
    
    cleaned = clean_pdf_text(text)
    
    # Page markers should be removed
    assert "- 1 -" not in cleaned
    assert "| 2 |" not in cleaned
    # Content should remain
    assert "Section 1 - Introduction" in cleaned
    assert "Content here" in cleaned


def test_remove_repetitive_headers():
    """Test removal of repetitive headers that appear multiple times"""
    text = """Official Government Document
Section 1 - Introduction
Content of section 1
Official Government Document
Section 2 - Details
Content of section 2
Official Government Document
Section 3 - More
Content of section 3
Official Government Document
Section 4 - Final
Content of section 4"""
    
    cleaned = clean_pdf_text(text)
    
    # Repetitive header should be removed (appears 4 times, threshold is >3)
    assert cleaned.count("Official Government Document") == 0
    # Content should remain
    assert "Section 1 - Introduction" in cleaned
    assert "Content of section 1" in cleaned
    assert "Section 2 - Details" in cleaned


def test_remove_repetitive_footers():
    """Test removal of repetitive footers"""
    text = """Section 1 - Introduction
Content of section 1
Copyright 2023 - All Rights Reserved
Section 2 - Details
Content of section 2
Copyright 2023 - All Rights Reserved
Section 3 - More
Content of section 3
Copyright 2023 - All Rights Reserved
Section 4 - Final
Content of section 4
Copyright 2023 - All Rights Reserved"""
    
    cleaned = clean_pdf_text(text)
    
    # Repetitive footer should be removed
    assert cleaned.count("Copyright 2023 - All Rights Reserved") == 0
    # Content should remain
    assert "Section 1 - Introduction" in cleaned
    assert "Content of section 1" in cleaned


def test_remove_excessive_whitespace():
    """Test removal of excessive whitespace (multiple spaces and blank lines)"""
    text = """Section 1 - Introduction

This    has    multiple    spaces.


And multiple blank lines.



Section 2 - Details"""
    
    cleaned = clean_pdf_text(text)
    
    # Multiple spaces should be reduced to single space
    assert "This    has    multiple    spaces" not in cleaned
    assert "This has multiple spaces" in cleaned
    
    # Excessive blank lines should be reduced (max 2 newlines = 1 blank line)
    assert "\n\n\n" not in cleaned
    assert "\n\n\n\n" not in cleaned


def test_preserve_legal_markers():
    """Test that legal markers like (a), (b), (c) are preserved"""
    text = """Section 1 - Conditions
The following conditions apply:
(a) First condition
(b) Second condition
(c) Third condition"""
    
    cleaned = clean_pdf_text(text)
    
    # Legal markers should be preserved
    assert "(a)" in cleaned
    assert "(b)" in cleaned
    assert "(c)" in cleaned
    assert "First condition" in cleaned
    assert "Second condition" in cleaned


def test_empty_text_handling():
    """Test handling of empty or whitespace-only text"""
    # Empty string
    assert clean_pdf_text("") == ""
    
    # Only whitespace
    assert clean_pdf_text("   \n\n   \t  ") == ""
    
    # Only newlines
    assert clean_pdf_text("\n\n\n") == ""


def test_real_world_example():
    """Test with a realistic legal document excerpt"""
    text = """Ministry of Finance - Government of India
CGST Act 2017
Page 1

Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged on any supply of goods or services or both to him which are used or intended to be used in the course or furtherance of his business.

Ministry of Finance - Government of India
CGST Act 2017
Page 2

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless the turnover exceeds 5 crore.

Provided that where the goods against an invoice are received in lots or instalments, the registered person shall be entitled to take credit upon receipt of the last lot or instalment.

Ministry of Finance - Government of India
CGST Act 2017
Page 3"""
    
    cleaned = clean_pdf_text(text)
    
    # Repetitive headers should be removed
    assert cleaned.count("Ministry of Finance - Government of India") == 0
    assert cleaned.count("CGST Act 2017") == 0
    
    # Page numbers should be removed
    assert "Page 1" not in cleaned
    assert "Page 2" not in cleaned
    assert "Page 3" not in cleaned
    
    # Legal content should be preserved
    assert "Section 16" in cleaned
    assert "Eligibility and conditions" in cleaned
    assert "(1) Every registered person" in cleaned
    assert "(2) Notwithstanding" in cleaned
    assert "Provided that" in cleaned
    assert "turnover exceeds 5 crore" in cleaned


def test_preserve_section_numbers():
    """Test that section numbers in content are preserved (not treated as page numbers)"""
    text = """Section 1 - Introduction
This section discusses requirements.

Section 2 - Definitions
This section provides definitions.

Section 3 - Procedures
This section outlines procedures."""
    
    cleaned = clean_pdf_text(text)
    
    # Section headers should be preserved
    assert "Section 1 - Introduction" in cleaned
    assert "Section 2 - Definitions" in cleaned
    assert "Section 3 - Procedures" in cleaned


def test_remove_non_printable_characters():
    """Test removal of non-printable characters"""
    text = "Section 1\x00\x01\x02 - Introduction\nContent with\x03 non-printable\x04 chars"
    
    cleaned = clean_pdf_text(text)
    
    # Non-printable characters should be removed
    assert "\x00" not in cleaned
    assert "\x01" not in cleaned
    assert "\x02" not in cleaned
    assert "\x03" not in cleaned
    assert "\x04" not in cleaned
    
    # Regular content should remain
    assert "Section 1" in cleaned
    assert "Introduction" in cleaned
    assert "Content with" in cleaned


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

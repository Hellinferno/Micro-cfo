#!/usr/bin/env python3
"""
Property-Based Tests for clean_pdf_text() function (Task 1.5)

Tests Property 10: Header/Footer Removal
Tests Property 11: Empty Content Handling

Validates: Requirements 4.2, 4.5

Uses hypothesis for property-based testing with minimum 100 iterations.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from legal_ingestion import clean_pdf_text
import re


# ============================================================================
# Property 10: Header/Footer Removal
# ============================================================================

@given(
    num_pages=st.integers(min_value=3, max_value=5),
    header_text=st.sampled_from([
        "Ministry of Finance Government of India",
        "Central Board of Direct Taxes",
        "Official Government Document",
        "Department of Revenue India",
        "Income Tax Department"
    ]),
    footer_text=st.sampled_from([
        "Copyright All Rights Reserved",
        "Confidential Document",
        "For Official Use Only",
        "Page Footer Text",
        "End of Page"
    ])
)
@settings(max_examples=100, deadline=None)
def test_property_repetitive_headers_removed(num_pages, header_text, footer_text):
    """
    Property 10: Header/Footer Removal
    
    For any PDF with repetitive header or footer content, the extracted text chunks
    should not contain the repetitive header/footer text.
    
    Validates: Requirements 4.2
    
    Property: If a line appears 3 or more times in the text, it should be removed
    from the cleaned output (as it's likely a header/footer).
    """
    # Ensure header and footer are distinct
    assume(header_text != footer_text)
    
    # Create unique content (not using loop variable)
    content_lines = [
        "Section One Introduction to legal provisions",
        "This section describes requirement details",
        "The applicable threshold is specified herein"
    ]
    
    # Build text with repetitive headers and footers
    pages = []
    for i in range(num_pages):
        page = [header_text]
        # Add unique content per page
        page.append(f"Page {i+1} specific content about legal matters")
        page.extend(content_lines)
        page.append(footer_text)
        pages.append('\n'.join(page))
    
    text = '\n'.join(pages)
    
    # Clean the text
    cleaned = clean_pdf_text(text)
    
    # Property: Repetitive header and footer should be removed
    # (appears 'num_pages' times, which is >= 3)
    assert header_text not in cleaned, \
        f"Repetitive header '{header_text}' should be removed (appeared {num_pages} times)"
    assert footer_text not in cleaned, \
        f"Repetitive footer '{footer_text}' should be removed (appeared {num_pages} times)"
    
    # Property: Content should be preserved (at least some of it)
    assert "Section" in cleaned or "legal" in cleaned or "requirement" in cleaned, \
        "Some content should be preserved after cleaning"


@given(
    content=st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),  # ASCII printable only
        min_size=20,
        max_size=200
    ).filter(lambda x: not x.strip().isdigit() and any(c.isalpha() for c in x)),
    page_num=st.integers(min_value=1, max_value=999)
)
@settings(max_examples=100, deadline=None)
def test_property_page_numbers_removed(content, page_num):
    """
    Property 10: Header/Footer Removal (Page Numbers)
    
    For any PDF containing page numbers in various formats, the cleaned text
    should not contain standalone page numbers.
    
    Validates: Requirements 4.2
    
    Property: Page numbers in common formats should be removed from cleaned text.
    """
    assume(content.strip() != "")
    assume(str(page_num) not in content)  # Ensure page number isn't in content
    assume(not content.strip().isdigit())  # Ensure content isn't just digits
    assume(any(c.isalpha() for c in content))  # Ensure content has letters
    
    # Test various page number formats
    formats = [
        f"{page_num}",  # Standalone number
        f"Page {page_num}",  # With prefix
        f"Pg. {page_num}",  # Abbreviated prefix
        f"- {page_num} -",  # With separators
        f"| {page_num} |",  # With pipes
    ]
    
    for page_format in formats:
        text = f"{content}\n{page_format}\n{content}"
        cleaned = clean_pdf_text(text)
        
        # Property: Page number format should be removed
        assert page_format not in cleaned, \
            f"Page number format '{page_format}' should be removed"
        
        # Property: Content should be preserved
        # Check that at least some of the content is present
        content_words = [w for w in content.strip().split()[:5] if not w.isdigit()]
        for word in content_words:
            if len(word) > 3 and any(c.isalpha() for c in word):  # Only check meaningful words with letters
                assert word in cleaned, \
                    f"Content word '{word}' should be preserved"


@given(
    lines=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),  # ASCII printable only
            min_size=10,
            max_size=100
        ).filter(lambda x: not x.strip().isdigit() and any(c.isalpha() for c in x)),
        min_size=3,
        max_size=10
    ),
    spaces=st.integers(min_value=2, max_value=10),
    newlines=st.integers(min_value=3, max_value=10)
)
@settings(max_examples=100, deadline=None)
def test_property_excessive_whitespace_normalized(lines, spaces, newlines):
    """
    Property 10: Header/Footer Removal (Whitespace Normalization)
    
    For any text with excessive whitespace (multiple spaces or blank lines),
    the cleaned text should have normalized whitespace.
    
    Validates: Requirements 4.2
    
    Property: Multiple consecutive spaces should be reduced to single space,
    and excessive blank lines should be reduced to at most 2 newlines.
    """
    # Filter out empty lines and digit-only lines
    non_empty_lines = [line for line in lines if line.strip() != "" and 
                       not line.strip().isdigit() and 
                       any(c.isalpha() for c in line)]
    
    # Remove duplicate lines to avoid them being flagged as repetitive
    seen = set()
    unique_lines = []
    for line in non_empty_lines:
        if line.strip() not in seen:
            unique_lines.append(line)
            seen.add(line.strip())
    
    assume(len(unique_lines) >= 2)
    
    # Create text with excessive whitespace
    # Add multiple spaces within lines
    spaced_lines = [line.replace(' ', ' ' * spaces) for line in unique_lines]
    
    # Join with excessive newlines
    text = ('\n' * newlines).join(spaced_lines)
    
    # Clean the text
    cleaned = clean_pdf_text(text)
    
    # Skip if cleaning removed everything (e.g., all lines were repetitive)
    assume(cleaned != "")
    
    # Property: No more than 2 consecutive spaces should exist
    assert '   ' not in cleaned, \
        "More than 2 consecutive spaces should be normalized"
    
    # Property: No more than 2 consecutive newlines should exist (1 blank line)
    assert '\n\n\n' not in cleaned, \
        "Excessive blank lines should be normalized to at most 2 newlines"
    
    # Property: Content should still be present
    for line in unique_lines[:2]:
        # Check that words from the line are present (spaces may be normalized)
        words = [w for w in line.strip().split()[:3] if not w.isdigit() and any(c.isalpha() for c in w)]
        for word in words:
            if len(word) > 3:
                assert word in cleaned, \
                    f"Content word '{word}' should be preserved"


@given(
    content=st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),  # ASCII printable only
        min_size=20,
        max_size=200
    ).filter(lambda x: not x.strip().isdigit() and any(c.isalpha() for c in x)),
    legal_marker=st.sampled_from(['(a)', '(b)', '(c)', '(i)', '(ii)', '(iii)', '(1)', '(2)'])
)
@settings(max_examples=100, deadline=None)
def test_property_legal_markers_preserved(content, legal_marker):
    """
    Property 10: Header/Footer Removal (Legal Markers Preservation)
    
    For any text containing legal markers like (a), (b), (c), these markers
    should be preserved even though they are short lines.
    
    Validates: Requirements 4.2
    
    Property: Legal sub-clause markers should not be removed during cleaning.
    """
    assume(content.strip() != "")
    assume(legal_marker not in content)
    assume(not content.strip().isdigit())
    assume(any(c.isalpha() for c in content))
    
    # Create text with legal marker
    text = f"{content}\n{legal_marker} This is a legal sub-clause\n{content}"
    
    # Clean the text
    cleaned = clean_pdf_text(text)
    
    # Property: Legal marker should be preserved
    assert legal_marker in cleaned, \
        f"Legal marker '{legal_marker}' should be preserved in cleaned text"
    
    # Property: Content should be preserved
    content_words = [w for w in content.strip().split()[:5] if not w.isdigit() and any(c.isalpha() for c in w)]
    for word in content_words:
        if len(word) > 3:
            assert word in cleaned, \
                f"Content word '{word}' should be preserved"


# ============================================================================
# Property 11: Empty Content Handling
# ============================================================================

@given(
    whitespace=st.text(alphabet=st.characters(whitelist_categories=('Zs',)), min_size=0, max_size=100)
)
@settings(max_examples=100, deadline=None)
def test_property_empty_whitespace_only_text(whitespace):
    """
    Property 11: Empty Content Handling
    
    For any PDF that produces empty or whitespace-only text after extraction,
    the system should return empty string.
    
    Validates: Requirements 4.5
    
    Property: Whitespace-only input should produce empty output.
    """
    # Add some newlines and tabs to the whitespace
    text = whitespace + '\n\n\t\t  \n  '
    
    # Clean the text
    cleaned = clean_pdf_text(text)
    
    # Property: Empty or whitespace-only input should produce empty output
    assert cleaned == "", \
        "Whitespace-only text should produce empty string after cleaning"


@given(
    empty_variant=st.sampled_from(['', '\n', '\n\n', '\t', '\t\t', '   ', '\n\t\n', '  \n  \n  '])
)
@settings(max_examples=100, deadline=None)
def test_property_empty_text_variants(empty_variant):
    """
    Property 11: Empty Content Handling (Variants)
    
    For any variant of empty text (empty string, only newlines, only tabs, only spaces),
    the cleaned output should be empty string.
    
    Validates: Requirements 4.5
    
    Property: All variants of empty/whitespace text should produce empty output.
    """
    # Clean the text
    cleaned = clean_pdf_text(empty_variant)
    
    # Property: All empty variants should produce empty string
    assert cleaned == "", \
        f"Empty variant '{repr(empty_variant)}' should produce empty string after cleaning"


@given(
    short_lines=st.lists(
        st.text(alphabet=st.characters(whitelist_categories=('Zs',)), min_size=0, max_size=5),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=100, deadline=None)
def test_property_very_short_content_removed(short_lines):
    """
    Property 11: Empty Content Handling (Short Lines)
    
    For any text consisting only of very short lines (< 3 characters) that are not
    legal markers, the cleaned output should be empty or minimal.
    
    Validates: Requirements 4.5
    
    Property: Very short non-legal-marker lines should be removed.
    """
    # Create text from short lines (excluding legal markers)
    text = '\n'.join(short_lines)
    
    # Ensure no legal markers are present
    assume('(a)' not in text)
    assume('(b)' not in text)
    assume('(c)' not in text)
    assume('(1)' not in text)
    assume('(2)' not in text)
    
    # Clean the text
    cleaned = clean_pdf_text(text)
    
    # Property: Very short content should result in empty or minimal output
    # (since lines < 3 chars that aren't legal markers are removed)
    assert len(cleaned) < len(text) or cleaned == "", \
        "Very short non-legal-marker content should be removed or minimized"


@given(
    content=st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),  # ASCII printable only
        min_size=20,
        max_size=200
    ).filter(lambda x: not x.strip().isdigit() and any(c.isalpha() for c in x) and len(x.strip()) > 10)
)
@settings(max_examples=100, deadline=None)
def test_property_non_empty_content_preserved(content):
    """
    Property 11: Empty Content Handling (Non-Empty Preservation)
    
    For any non-empty, meaningful content, the cleaned output should not be empty.
    
    Validates: Requirements 4.5
    
    Property: Non-empty input with meaningful content should produce non-empty output.
    """
    assume(content.strip() != "")
    assume(len(content.strip()) > 10)  # Ensure meaningful content
    assume(not content.strip().isdigit())  # Not just digits
    assume(any(c.isalpha() for c in content))  # Has letters
    
    # Clean the text
    cleaned = clean_pdf_text(content)
    
    # Property: Non-empty meaningful content should produce non-empty output
    assert cleaned != "", \
        "Non-empty meaningful content should not produce empty output"
    
    # Property: Some of the original content should be preserved
    content_words = [w for w in content.strip().split() if not w.isdigit() and any(c.isalpha() for c in w)]
    preserved_count = sum(1 for word in content_words if word in cleaned)
    assert preserved_count > 0, \
        "At least some words from original content should be preserved"


@given(
    non_printable_chars=st.lists(
        st.sampled_from(['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', 
                        '\x08', '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12',
                        '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a',
                        '\x1b', '\x1c', '\x1d', '\x1e', '\x1f']),
        min_size=1,
        max_size=10
    ),
    content=st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),  # ASCII printable only
        min_size=10,
        max_size=50
    ).filter(lambda x: any(c.isalpha() for c in x))
)
@settings(max_examples=100, deadline=None)
def test_property_non_printable_characters_removed(non_printable_chars, content):
    """
    Property 10/11: Non-Printable Character Removal
    
    For any text containing non-printable characters (except newlines and tabs),
    the cleaned text should not contain those non-printable characters.
    
    Validates: Requirements 4.2
    
    Property: Non-printable characters should be removed from cleaned text.
    """
    assume(content.strip() != "")
    
    # Create text with non-printable characters mixed with content
    non_printable = ''.join(non_printable_chars)
    text = f"{content}{non_printable}{content}"
    
    # Clean the text
    cleaned = clean_pdf_text(text)
    
    # Property: Non-printable characters should be removed
    # Check that control characters (except \n and \t) are not present
    for char in non_printable_chars:
        if char not in ['\n', '\t']:
            assert char not in cleaned, \
                f"Non-printable character {repr(char)} should be removed"
    
    # Property: Printable content should be preserved
    assert content in cleaned or any(word in cleaned for word in content.split()), \
        "Printable content should be preserved after removing non-printable characters"


# ============================================================================
# Combined Properties: Idempotence and Consistency
# ============================================================================

@given(
    text=st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),  # ASCII printable only
        min_size=0,
        max_size=500
    )
)
@settings(max_examples=100, deadline=None)
def test_property_cleaning_is_idempotent(text):
    """
    Property: Idempotence
    
    For any text, cleaning it once should produce the same result as cleaning it twice.
    
    Property: clean_pdf_text(clean_pdf_text(text)) == clean_pdf_text(text)
    
    Note: This property holds for all text that survives the first cleaning pass.
    Very short lines (< 3 chars) may be removed, which is intentional behavior.
    """
    # Clean once
    cleaned_once = clean_pdf_text(text)
    
    # Clean twice
    cleaned_twice = clean_pdf_text(cleaned_once)
    
    # Property: Cleaning should be idempotent
    # If the first cleaning produced output, the second should be identical
    assert cleaned_once == cleaned_twice, \
        f"Cleaning should be idempotent: cleaning twice should produce same result as cleaning once.\nOnce: {repr(cleaned_once)}\nTwice: {repr(cleaned_twice)}"


@given(
    text=st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),  # ASCII printable only
        min_size=0,
        max_size=500
    )
)
@settings(max_examples=100, deadline=None)
def test_property_output_length_not_greater_than_input(text):
    """
    Property: Length Monotonicity
    
    For any text, the cleaned output should not be longer than the input
    (cleaning removes or normalizes, never adds content).
    
    Property: len(clean_pdf_text(text)) <= len(text)
    """
    cleaned = clean_pdf_text(text)
    
    # Property: Cleaned text should not be longer than original
    assert len(cleaned) <= len(text), \
        "Cleaned text should not be longer than original text"


@given(
    text=st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),  # ASCII printable only
        min_size=10,
        max_size=500
    )
)
@settings(max_examples=100, deadline=None)
def test_property_no_excessive_whitespace_in_output(text):
    """
    Property: Whitespace Normalization Guarantee
    
    For any text, the cleaned output should never contain excessive whitespace
    (more than 2 consecutive spaces or more than 2 consecutive newlines).
    
    Property: Cleaned text has normalized whitespace.
    """
    cleaned = clean_pdf_text(text)
    
    # Property: No more than 2 consecutive spaces
    assert '   ' not in cleaned, \
        "Cleaned text should not contain more than 2 consecutive spaces"
    
    # Property: No more than 2 consecutive newlines (1 blank line)
    assert '\n\n\n' not in cleaned, \
        "Cleaned text should not contain more than 2 consecutive newlines"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

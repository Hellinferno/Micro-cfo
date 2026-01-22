#!/usr/bin/env python3
"""
Property-Based Tests for Legal Structure Detection
Tests structure-aware chunking patterns in legal documents

Feature: legal-data-seeding
Properties 13-17: Structure Detection Properties
Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from legal_ingestion import LegalTextSplitter, LegalChunk
import re


# ============================================================================
# Test Data Generators (Strategies)
# ============================================================================

@st.composite
def section_numbers(draw):
    """Generate valid section numbers (e.g., '16', '16A', '16AA')"""
    number = draw(st.integers(min_value=1, max_value=999))
    # Optional letter suffix (A, B, AA, BB, etc.)
    has_suffix = draw(st.booleans())
    if has_suffix:
        letter = draw(st.sampled_from(['A', 'B', 'C', 'D', 'AA', 'BB', 'CC']))
        return f"{number}{letter}"
    return str(number)


@st.composite
def section_text(draw):
    """Generate text with Section pattern"""
    section_num = draw(section_numbers())
    title = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'), min_codepoint=32, max_codepoint=122),
        min_size=10,
        max_size=50
    ))
    
    # Generate section content
    content = draw(st.text(min_size=20, max_size=200))
    
    # Choose section format
    format_choice = draw(st.sampled_from([
        f"Section {section_num} - {title}\n\n{content}",
        f"SECTION {section_num} - {title}\n\n{content}",
        f"Section {section_num}: {title}\n\n{content}",
    ]))
    
    return format_choice, section_num


@st.composite
def rule_text(draw):
    """Generate text with Rule pattern"""
    rule_num = draw(section_numbers())
    title = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'), min_codepoint=32, max_codepoint=122),
        min_size=10,
        max_size=50
    ))
    
    # Generate rule content
    content = draw(st.text(min_size=20, max_size=200))
    
    # Choose rule format
    format_choice = draw(st.sampled_from([
        f"Rule {rule_num} - {title}\n\n{content}",
        f"RULE {rule_num} - {title}\n\n{content}",
        f"Rule {rule_num}: {title}\n\n{content}",
    ]))
    
    return format_choice, rule_num


@st.composite
def proviso_text(draw):
    """Generate text with Proviso pattern"""
    content = draw(st.text(min_size=20, max_size=200))
    
    # Choose proviso format
    format_choice = draw(st.sampled_from([
        f"Provided that {content}",
        f"PROVIDED THAT {content}",
        f"  Provided that {content}",  # With leading whitespace
        f"    Provided that {content}",
        f"Provided further that {content}",
    ]))
    
    return format_choice


@st.composite
def sub_clause_text(draw):
    """Generate text with sub-clause pattern"""
    # Generate multiple sub-clauses
    num_clauses = draw(st.integers(min_value=1, max_value=5))
    clauses = []
    
    for i in range(num_clauses):
        # Choose between letter and number sub-clauses
        use_letter = draw(st.booleans())
        if use_letter:
            marker = chr(ord('a') + i) if i < 26 else f"a{i}"
        else:
            marker = str(i + 1)
        
        content = draw(st.text(min_size=10, max_size=100))
        
        # Choose format
        format_choice = draw(st.sampled_from([
            f"({marker}) {content}",
            f"  ({marker}) {content}",  # With leading whitespace
            f"    ({marker}) {content}",
        ]))
        
        clauses.append(format_choice)
    
    return "\n".join(clauses)


@st.composite
def section_with_proviso(draw):
    """Generate section text with proviso clause"""
    section_content, section_num = draw(section_text())
    proviso_content = draw(proviso_text())
    
    combined = f"{section_content}\n\n{proviso_content}"
    return combined, section_num


@st.composite
def section_with_sub_clauses(draw):
    """Generate section text with sub-clauses"""
    section_content, section_num = draw(section_text())
    sub_clause_content = draw(sub_clause_text())
    
    combined = f"{section_content}\n\n{sub_clause_content}"
    return combined, section_num


# ============================================================================
# Property 13: Section Boundary Detection
# ============================================================================

@given(text_and_num=section_text())
@settings(max_examples=100)
def test_property_section_boundary_detection(text_and_num):
    """
    Property 13: Section Boundary Detection
    
    For any legal document text containing section patterns (e.g., "Section 5", "Section 12A"),
    the chunking process should identify these as section boundaries and create separate chunks.
    
    **Validates: Requirements 5.1**
    """
    text, expected_section_num = text_and_num
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk for text with Section pattern, got {len(chunks)}"
    
    # The chunk should contain the section text
    assert any("Section" in chunk.text or "SECTION" in chunk.text for chunk in chunks), \
        "Section pattern not found in any chunk"


@given(
    text1_and_num1=section_text(),
    text2_and_num2=section_text()
)
@settings(max_examples=100)
def test_property_multiple_sections_create_separate_chunks(text1_and_num1, text2_and_num2):
    """
    Property 13: Multiple sections should create separate chunks
    
    For any two section texts, when combined, they should create at least two separate chunks.
    
    **Validates: Requirements 5.1**
    """
    text1, num1 = text1_and_num1
    text2, num2 = text2_and_num2
    
    # Ensure sections have different numbers
    assume(num1 != num2)
    
    combined_text = f"{text1}\n\n{text2}"
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(combined_text, "GST")
    
    # Should create at least 2 chunks for 2 sections
    assert len(chunks) >= 2, \
        f"Expected at least 2 chunks for 2 sections, got {len(chunks)}"


@given(text_and_num=rule_text())
@settings(max_examples=100)
def test_property_rule_boundary_detection(text_and_num):
    """
    Property 13: Rule Boundary Detection
    
    For any legal document text containing rule patterns (e.g., "Rule 42"),
    the chunking process should identify these as boundaries and create chunks.
    
    **Validates: Requirements 5.1**
    """
    text, expected_rule_num = text_and_num
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk for text with Rule pattern, got {len(chunks)}"
    
    # The chunk should contain the rule text
    assert any("Rule" in chunk.text or "RULE" in chunk.text for chunk in chunks), \
        "Rule pattern not found in any chunk"


# ============================================================================
# Property 14: Proviso Clause Detection
# ============================================================================

@given(text_and_num=section_with_proviso())
@settings(max_examples=100)
def test_property_proviso_clause_detection(text_and_num):
    """
    Property 14: Proviso Clause Detection
    
    For any legal document text containing proviso patterns (e.g., "Provided that"),
    the chunking process should identify these as proviso clauses and mark them 
    with chunk_type "proviso".
    
    **Validates: Requirements 5.2**
    """
    text, section_num = text_and_num
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    
    # At least one chunk should contain the proviso text
    has_proviso_text = any("Provided" in chunk.text or "PROVIDED" in chunk.text for chunk in chunks)
    assert has_proviso_text, "Proviso pattern not found in any chunk"
    
    # At least one chunk should be marked as proviso type
    has_proviso_type = any(chunk.chunk_type == "proviso" for chunk in chunks)
    assert has_proviso_type, "No chunk marked with chunk_type='proviso'"


@given(proviso_content=proviso_text())
@settings(max_examples=100)
def test_property_standalone_proviso_detection(proviso_content):
    """
    Property 14: Standalone proviso clause detection
    
    For any proviso text (even without a parent section), the chunking process
    should identify it and mark it with chunk_type "proviso".
    
    **Validates: Requirements 5.2**
    """
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(proviso_content, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk for proviso text, got {len(chunks)}"
    
    # The chunk should be marked as proviso
    assert chunks[0].chunk_type == "proviso", \
        f"Expected chunk_type='proviso', got '{chunks[0].chunk_type}'"


# ============================================================================
# Property 15: Sub-clause Detection
# ============================================================================

@given(text_and_num=section_with_sub_clauses())
@settings(max_examples=100)
def test_property_sub_clause_detection(text_and_num):
    """
    Property 15: Sub-clause Detection
    
    For any legal document text containing sub-clause patterns (e.g., "(a)", "(b)", "(c)"),
    the chunking process should identify these as sub-clauses and mark them 
    with chunk_type "sub_clause".
    
    **Validates: Requirements 5.3**
    """
    text, section_num = text_and_num
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    
    # At least one chunk should contain sub-clause markers
    has_sub_clause_text = any(re.search(r'\([a-z0-9]+\)', chunk.text) for chunk in chunks)
    assert has_sub_clause_text, "Sub-clause pattern not found in any chunk"
    
    # At least one chunk should be marked as sub_clause type
    has_sub_clause_type = any(chunk.chunk_type == "sub_clause" for chunk in chunks)
    assert has_sub_clause_type, "No chunk marked with chunk_type='sub_clause'"


@given(sub_clause_content=sub_clause_text())
@settings(max_examples=100)
def test_property_standalone_sub_clause_detection(sub_clause_content):
    """
    Property 15: Standalone sub-clause detection
    
    For any sub-clause text (even without a parent section), the chunking process
    should identify it and mark it with chunk_type "sub_clause".
    
    **Validates: Requirements 5.3**
    """
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(sub_clause_content, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk for sub-clause text, got {len(chunks)}"
    
    # The chunk should be marked as sub_clause
    assert chunks[0].chunk_type == "sub_clause", \
        f"Expected chunk_type='sub_clause', got '{chunks[0].chunk_type}'"


# ============================================================================
# Property 16: Section Number Extraction
# ============================================================================

@given(text_and_num=section_text())
@settings(max_examples=100)
def test_property_section_number_extraction(text_and_num):
    """
    Property 16: Section Number Extraction
    
    For any legal chunk created from text containing a section identifier,
    the chunk's section_number metadata field should contain the extracted 
    section identifier.
    
    **Validates: Requirements 5.4**
    """
    text, expected_section_num = text_and_num
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    
    # The first chunk should have the section number extracted
    assert chunks[0].section_number is not None, \
        "Section number not extracted from text with Section pattern"
    
    # The extracted section number should match the expected one
    assert chunks[0].section_number == expected_section_num, \
        f"Expected section_number='{expected_section_num}', got '{chunks[0].section_number}'"


@given(text_and_num=rule_text())
@settings(max_examples=100)
def test_property_rule_number_extraction(text_and_num):
    """
    Property 16: Rule Number Extraction
    
    For any legal chunk created from text containing a rule identifier,
    the chunk's section_number metadata field should contain the extracted 
    rule identifier.
    
    **Validates: Requirements 5.4**
    """
    text, expected_rule_num = text_and_num
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    
    # The first chunk should have the rule number extracted
    assert chunks[0].section_number is not None, \
        "Rule number not extracted from text with Rule pattern"
    
    # The extracted rule number should match the expected one
    assert chunks[0].section_number == expected_rule_num, \
        f"Expected section_number='{expected_rule_num}', got '{chunks[0].section_number}'"


@given(
    text1_and_num1=section_text(),
    text2_and_num2=section_text()
)
@settings(max_examples=100)
def test_property_section_numbers_preserved_across_chunks(text1_and_num1, text2_and_num2):
    """
    Property 16: Section numbers preserved across multiple chunks
    
    For any multiple sections, each chunk should have its correct section number.
    
    **Validates: Requirements 5.4**
    """
    text1, num1 = text1_and_num1
    text2, num2 = text2_and_num2
    
    # Ensure sections have different numbers
    assume(num1 != num2)
    
    combined_text = f"{text1}\n\n{text2}"
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(combined_text, "GST")
    
    # Should create at least 2 chunks
    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"
    
    # Each chunk should have a section number
    for i, chunk in enumerate(chunks[:2]):
        assert chunk.section_number is not None, \
            f"Chunk {i} missing section_number"


# ============================================================================
# Property 17: Chunk Type Preservation
# ============================================================================

@given(text_and_num=section_text())
@settings(max_examples=100)
def test_property_chunk_type_main_for_section(text_and_num):
    """
    Property 17: Chunk Type Preservation - Main
    
    For any legal chunk created from a basic section (without proviso or sub-clauses),
    the chunk_type field should be "main".
    
    **Validates: Requirements 5.5**
    """
    text, section_num = text_and_num
    
    # Ensure text doesn't accidentally contain proviso or sub-clause patterns
    assume("Provided" not in text and "PROVIDED" not in text)
    assume(not re.search(r'\([a-z0-9]+\)', text))
    
    splitter = LegalTextSplitter()
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    
    # The chunk should be marked as main type
    assert chunks[0].chunk_type == "main", \
        f"Expected chunk_type='main' for basic section, got '{chunks[0].chunk_type}'"


@given(text_and_num=section_with_proviso())
@settings(max_examples=100)
def test_property_chunk_type_proviso_preservation(text_and_num):
    """
    Property 17: Chunk Type Preservation - Proviso
    
    For any legal chunk created with a proviso clause, the chunk_type field
    should be correctly identified as "proviso" and preserved.
    
    **Validates: Requirements 5.5**
    """
    text, section_num = text_and_num
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    
    # At least one chunk should be marked as proviso
    has_proviso = any(chunk.chunk_type == "proviso" for chunk in chunks)
    assert has_proviso, "No chunk marked with chunk_type='proviso'"


@given(text_and_num=section_with_sub_clauses())
@settings(max_examples=100)
def test_property_chunk_type_sub_clause_preservation(text_and_num):
    """
    Property 17: Chunk Type Preservation - Sub-clause
    
    For any legal chunk created with sub-clauses, the chunk_type field
    should be correctly identified as "sub_clause" and preserved.
    
    **Validates: Requirements 5.5**
    """
    text, section_num = text_and_num
    
    # Ensure text doesn't contain proviso (which takes priority)
    assume("Provided" not in text and "PROVIDED" not in text)
    
    splitter = LegalTextSplitter()
    chunks = splitter.split_legal_text(text, "GST")
    
    # Should create at least one chunk
    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    
    # At least one chunk should be marked as sub_clause
    has_sub_clause = any(chunk.chunk_type == "sub_clause" for chunk in chunks)
    assert has_sub_clause, "No chunk marked with chunk_type='sub_clause'"


@given(text=st.text(min_size=10, max_size=200))
@settings(max_examples=100)
def test_property_chunk_type_always_valid(text):
    """
    Property 17: Chunk type is always one of the valid types
    
    For any legal chunk created, the chunk_type field should always be
    one of: "main", "proviso", or "sub_clause".
    
    **Validates: Requirements 5.5**
    """
    splitter = LegalTextSplitter()
    
    chunks = splitter.split_legal_text(text, "GST")
    
    valid_chunk_types = {"main", "proviso", "sub_clause"}
    
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_type in valid_chunk_types, \
            f"Chunk {i} has invalid chunk_type: '{chunk.chunk_type}'"


# ============================================================================
# Specific Example Tests (Concrete Cases)
# ============================================================================

def test_example_section_16_structure():
    """
    Concrete example: Section 16 from CGST Act with complex structure
    """
    text = """
Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit.

Provided that where the goods against an invoice are received in lots or instalments.

(a) he is in possession of a tax invoice;
(b) he has received the goods or services.
"""
    
    splitter = LegalTextSplitter()
    chunks = splitter.split_legal_text(text, "GST")
    
    assert len(chunks) == 1
    assert chunks[0].section_number == "16"
    # Proviso takes priority over sub-clause
    assert chunks[0].chunk_type == "proviso"
    assert "Provided that" in chunks[0].text
    assert "(a)" in chunks[0].text
    assert "(b)" in chunks[0].text


def test_example_multiple_sections_with_different_types():
    """
    Concrete example: Multiple sections with different chunk types
    """
    text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

Section 17 - Apportionment of credit

Input tax credit shall be apportioned if:

(a) the goods are used for taxable supplies;
(b) the goods are used for exempt supplies.

Section 18 - Availability of credit

Credit shall be available.

Provided that the credit shall not exceed the amount specified.
"""
    
    splitter = LegalTextSplitter()
    chunks = splitter.split_legal_text(text, "GST")
    
    assert len(chunks) == 3
    
    # Section 16: main type
    assert chunks[0].section_number == "16"
    assert chunks[0].chunk_type == "main"
    
    # Section 17: sub_clause type
    assert chunks[1].section_number == "17"
    assert chunks[1].chunk_type == "sub_clause"
    
    # Section 18: proviso type
    assert chunks[2].section_number == "18"
    assert chunks[2].chunk_type == "proviso"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

#!/usr/bin/env python3
"""
Property-Based Tests for Law Type Detection
Tests filename pattern matching for legal document classification

Feature: legal-data-seeding
Property 9: Law Type Detection from Filename
Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from legal_ingestion import detect_law_type_from_filename


# ============================================================================
# Test Data Generators (Strategies)
# ============================================================================

@st.composite
def gst_filenames(draw):
    """Generate filenames that should be classified as GST"""
    # Choose between CGST and IGST
    gst_type = draw(st.sampled_from(["CGST", "IGST", "cgst", "igst", "Cgst", "Igst"]))
    
    # Optional prefix/suffix components
    prefix = draw(st.sampled_from(["", "The_", "India_", "Official_"]))
    suffix = draw(st.sampled_from(["", "_Act", "_2017", "_Rules", "_Amendment"]))
    
    # Optional separator (underscore, hyphen, or space)
    separator = draw(st.sampled_from(["_", "-", " "]))
    
    # Build filename
    filename = f"{prefix}{gst_type}{suffix}"
    
    # Optional file extension
    extension = draw(st.sampled_from([".pdf", ".PDF", ".txt", ".TXT", ""]))
    
    return filename + extension


@st.composite
def income_tax_filenames(draw):
    """Generate filenames that should be classified as Income Tax"""
    # Choose between different Income Tax patterns
    pattern = draw(st.sampled_from([
        "Income Tax", "Income_Tax", "Income-Tax", "INCOME TAX", "income tax",
        "IT Act", "IT_Act", "IT-Act", "it act", "IT ACT"
    ]))
    
    # Optional prefix/suffix components
    prefix = draw(st.sampled_from(["", "The_", "India_", "Official_"]))
    suffix = draw(st.sampled_from(["", "_1961", "_Act", "_Rules", "_Amendment"]))
    
    # Build filename
    filename = f"{prefix}{pattern}{suffix}"
    
    # Optional file extension
    extension = draw(st.sampled_from([".pdf", ".PDF", ".txt", ".TXT", ""]))
    
    return filename + extension


@st.composite
def corporate_law_filenames(draw):
    """Generate filenames that should be classified as Corporate Law"""
    # Choose between different Corporate Law patterns
    pattern = draw(st.sampled_from([
        "Companies Act", "Companies_Act", "Companies-Act", "COMPANIES ACT", "companies act",
        "MCA", "mca", "Mca"
    ]))
    
    # Optional prefix/suffix components
    prefix = draw(st.sampled_from(["", "The_", "India_", "Official_"]))
    suffix = draw(st.sampled_from(["", "_2013", "_Rules", "_Amendment", "_Guidelines"]))
    
    # Build filename
    filename = f"{prefix}{pattern}{suffix}"
    
    # Optional file extension
    extension = draw(st.sampled_from([".pdf", ".PDF", ".txt", ".TXT", ""]))
    
    return filename + extension


@st.composite
def subsidy_scheme_filenames(draw):
    """Generate filenames that should be classified as Subsidy Scheme"""
    # Choose between different Subsidy Scheme patterns
    pattern = draw(st.sampled_from([
        "PLI", "pli", "Pli",
        "Scheme", "scheme", "SCHEME",
        "PLI_Scheme", "PLI Scheme", "PLI-Scheme"
    ]))
    
    # Optional prefix/suffix components
    prefix = draw(st.sampled_from(["", "Textiles_", "Manufacturing_", "Production_"]))
    suffix = draw(st.sampled_from(["", "_Guidelines", "_Rules", "_2021", "_Details"]))
    
    # Build filename
    filename = f"{prefix}{pattern}{suffix}"
    
    # Optional file extension
    extension = draw(st.sampled_from([".pdf", ".PDF", ".txt", ".TXT", ""]))
    
    return filename + extension


@st.composite
def general_filenames(draw):
    """Generate filenames that should be classified as General (no specific pattern match)"""
    # Generate random words that don't contain any law type keywords
    words = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122),
            min_size=3,
            max_size=10
        ),
        min_size=1,
        max_size=3
    ))
    
    # Join with separator
    separator = draw(st.sampled_from(["_", "-", " "]))
    filename = separator.join(words)
    
    # Ensure it doesn't accidentally contain any law type keywords
    filename_upper = filename.upper()
    assume("CGST" not in filename_upper)
    assume("IGST" not in filename_upper)
    assume("INCOME" not in filename_upper)
    assume("TAX" not in filename_upper)
    assume("COMPANIES" not in filename_upper)
    assume("MCA" not in filename_upper)
    assume("PLI" not in filename_upper)
    assume("SCHEME" not in filename_upper)
    
    # Optional file extension
    extension = draw(st.sampled_from([".pdf", ".PDF", ".txt", ".TXT", ""]))
    
    return filename + extension


# ============================================================================
# Property 9: Law Type Detection from Filename
# ============================================================================

@given(filename=gst_filenames())
@settings(max_examples=100)
def test_property_gst_detection(filename):
    """
    Property: Any filename containing CGST or IGST (case-insensitive) 
    should be classified as "GST"
    
    **Validates: Requirements 3.1**
    """
    result = detect_law_type_from_filename(filename)
    assert result == "GST", f"Expected 'GST' for filename '{filename}', got '{result}'"


@given(filename=income_tax_filenames())
@settings(max_examples=100)
def test_property_income_tax_detection(filename):
    """
    Property: Any filename containing "Income Tax" or "IT Act" (case-insensitive)
    should be classified as "Income Tax"
    
    **Validates: Requirements 3.2**
    """
    result = detect_law_type_from_filename(filename)
    assert result == "Income Tax", f"Expected 'Income Tax' for filename '{filename}', got '{result}'"


@given(filename=corporate_law_filenames())
@settings(max_examples=100)
def test_property_corporate_law_detection(filename):
    """
    Property: Any filename containing "Companies Act" or "MCA" (case-insensitive)
    should be classified as "Corporate Law"
    
    **Validates: Requirements 3.3**
    """
    result = detect_law_type_from_filename(filename)
    assert result == "Corporate Law", f"Expected 'Corporate Law' for filename '{filename}', got '{result}'"


@given(filename=subsidy_scheme_filenames())
@settings(max_examples=100)
def test_property_subsidy_scheme_detection(filename):
    """
    Property: Any filename containing "PLI" or "Scheme" (case-insensitive)
    should be classified as "Subsidy Scheme"
    
    **Validates: Requirements 3.4**
    """
    result = detect_law_type_from_filename(filename)
    assert result == "Subsidy Scheme", f"Expected 'Subsidy Scheme' for filename '{filename}', got '{result}'"


@given(filename=general_filenames())
@settings(max_examples=100)
def test_property_general_detection(filename):
    """
    Property: Any filename that doesn't match known patterns
    should be classified as "General"
    
    **Validates: Requirements 3.5**
    """
    result = detect_law_type_from_filename(filename)
    assert result == "General", f"Expected 'General' for filename '{filename}', got '{result}'"


# ============================================================================
# Additional Property Tests: Classification Consistency
# ============================================================================

@given(
    filename=st.text(min_size=1, max_size=100),
    case_variant=st.sampled_from(["upper", "lower", "title"])
)
@settings(max_examples=100)
def test_property_case_insensitivity(filename, case_variant):
    """
    Property: Law type detection should be case-insensitive.
    The same filename in different cases should produce the same result.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    # Apply case transformation
    if case_variant == "upper":
        transformed = filename.upper()
    elif case_variant == "lower":
        transformed = filename.lower()
    else:  # title
        transformed = filename.title()
    
    # Both should produce the same result
    original_result = detect_law_type_from_filename(filename)
    transformed_result = detect_law_type_from_filename(transformed)
    
    assert original_result == transformed_result, \
        f"Case sensitivity issue: '{filename}' -> '{original_result}', '{transformed}' -> '{transformed_result}'"


@given(
    filename=st.text(min_size=1, max_size=100),
    separator=st.sampled_from(["_", "-", " "])
)
@settings(max_examples=100)
def test_property_separator_normalization(filename, separator):
    """
    Property: Law type detection should normalize separators (underscores, hyphens, spaces).
    Filenames with different separators but same content should produce the same result.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    # Create variants with different separators
    variant1 = filename.replace("_", separator).replace("-", separator).replace(" ", separator)
    variant2 = filename.replace("_", " ").replace("-", " ")
    
    result1 = detect_law_type_from_filename(variant1)
    result2 = detect_law_type_from_filename(variant2)
    
    # Both should produce the same result
    assert result1 == result2, \
        f"Separator normalization issue: '{variant1}' -> '{result1}', '{variant2}' -> '{result2}'"


@given(filename=st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_property_valid_output(filename):
    """
    Property: Law type detection should always return one of the valid law types.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    valid_law_types = {"GST", "Income Tax", "Corporate Law", "Subsidy Scheme", "General"}
    
    result = detect_law_type_from_filename(filename)
    
    assert result in valid_law_types, \
        f"Invalid law type returned: '{result}' for filename '{filename}'"


@given(
    base_filename=st.text(min_size=1, max_size=50),
    path_prefix=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=3)
)
@settings(max_examples=100)
def test_property_path_handling(base_filename, path_prefix):
    """
    Property: Law type detection should work with full paths, not just filenames.
    The result should be the same whether a full path or just filename is provided.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    # Create a full path
    if path_prefix:
        full_path = "/".join(path_prefix) + "/" + base_filename
    else:
        full_path = base_filename
    
    # Both should produce the same result
    filename_result = detect_law_type_from_filename(base_filename)
    path_result = detect_law_type_from_filename(full_path)
    
    assert filename_result == path_result, \
        f"Path handling issue: '{base_filename}' -> '{filename_result}', '{full_path}' -> '{path_result}'"


# ============================================================================
# Specific Example Tests (Edge Cases)
# ============================================================================

def test_example_actual_filenames():
    """
    Test with actual filenames from the seed downloader configuration.
    These are concrete examples that must work correctly.
    """
    test_cases = [
        ("CGST_Act_2017.pdf", "GST"),
        ("IGST_Act_2017.pdf", "GST"),
        ("Income_Tax_Act_1961.pdf", "Income Tax"),
        ("Companies_Act_2013.pdf", "Corporate Law"),
        ("PLI_Textiles_Guidelines.pdf", "Subsidy Scheme"),
        ("random_document.pdf", "General"),
        ("some_other_file.txt", "General"),
    ]
    
    for filename, expected in test_cases:
        result = detect_law_type_from_filename(filename)
        assert result == expected, f"Failed for '{filename}': expected '{expected}', got '{result}'"


def test_example_edge_cases():
    """
    Test edge cases and boundary conditions.
    """
    test_cases = [
        # Empty and minimal inputs
        ("", "General"),
        ("a", "General"),
        
        # Case variations
        ("cgst.pdf", "GST"),
        ("CGST.PDF", "GST"),
        ("CgSt_act.pdf", "GST"),
        
        # Multiple keywords (first match wins)
        ("CGST_Income_Tax.pdf", "GST"),  # GST checked first
        
        # Keywords in different positions
        ("Act_CGST_2017.pdf", "GST"),
        ("2017_CGST_Act.pdf", "GST"),
        
        # With full paths
        ("/data/initial_acts/CGST_Act_2017.pdf", "GST"),
        ("C:\\Documents\\Income_Tax_Act_1961.pdf", "Income Tax"),
        
        # Special characters
        ("CGST-Act-2017.pdf", "GST"),
        ("Income Tax Act 1961.pdf", "Income Tax"),
        
        # Partial matches should not trigger
        ("CGSTX_Act.pdf", "GST"),  # Still contains CGST
        ("XCGST_Act.pdf", "GST"),  # Still contains CGST
    ]
    
    for filename, expected in test_cases:
        result = detect_law_type_from_filename(filename)
        assert result == expected, f"Failed for '{filename}': expected '{expected}', got '{result}'"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

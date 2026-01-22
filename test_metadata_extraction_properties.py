#!/usr/bin/env python3
"""
Property-Based Tests for Metadata Extraction
Task 2.4: Write property tests for metadata extraction

Tests:
- Property 18: Sector Tag Assignment
- Property 19: Date Format Conversion

Validates Requirements: 6.3, 6.4, 6.5
"""

import pytest
from hypothesis import given, strategies as st, settings, example
from legal_ingestion import extract_metadata_from_text
import re


# ============================================================================
# Property 18: Sector Tag Assignment
# ============================================================================

# Define sector keywords as per the design document
SECTOR_KEYWORDS = {
    'Textile': ['textile', 'garment', 'fabric', 'apparel', 'clothing', 'weaving', 'spinning'],
    'Manufacturing': ['manufacturing', 'production', 'factory', 'industrial', 'producer', 'manufacture'],
    'Technology': ['software', 'IT', 'technology', 'digital', 'computer', 'information technology'],
    'Trading': ['trading', 'commerce', 'merchant', 'dealer', 'wholesale', 'retail', 'trade']
}

# Strategy to generate text with sector keywords
@st.composite
def text_with_sector_keyword(draw):
    """Generate text containing a sector keyword"""
    # Choose a random sector and keyword
    sector = draw(st.sampled_from(list(SECTOR_KEYWORDS.keys())))
    keyword = draw(st.sampled_from(SECTOR_KEYWORDS[sector]))
    
    # Generate surrounding text
    prefix = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')), 
                         min_size=0, max_size=50))
    suffix = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')), 
                         min_size=0, max_size=50))
    
    # Construct text with keyword as a complete word (with word boundaries)
    text = f"{prefix} {keyword} {suffix}"
    
    return text, sector, keyword


@given(text_with_sector_keyword())
@settings(max_examples=100)
@example((
    "This provision applies to textile manufacturing units",
    "Textile",
    "textile"
))
@example((
    "All manufacturing units must comply",
    "Manufacturing", 
    "manufacturing"
))
@example((
    "Software companies are covered",
    "Technology",
    "software"
))
@example((
    "Trading businesses must register",
    "Trading",
    "trading"
))
def test_property_18_sector_tag_assignment(text_and_sector):
    """
    **Property 18: Sector Tag Assignment**
    
    For any legal text containing sector keywords (textile, garment, manufacturing, 
    production, etc.), the resulting chunks should have the appropriate sector_tag 
    assigned based on the keyword mapping.
    
    **Validates: Requirements 6.3, 6.4**
    
    Property: If text contains a keyword from SECTOR_KEYWORDS[sector], 
    then extract_metadata_from_text(text)['sector_tag'] should equal sector
    or a higher-priority sector (due to priority ordering).
    """
    text, expected_sector, keyword = text_and_sector
    
    # Extract metadata
    metadata = extract_metadata_from_text(text)
    
    # The sector tag should be assigned
    assert metadata['sector_tag'] is not None, \
        f"Sector tag should be assigned when text contains keyword '{keyword}'"
    
    # The sector tag should be one of the valid sectors
    assert metadata['sector_tag'] in SECTOR_KEYWORDS.keys(), \
        f"Sector tag '{metadata['sector_tag']}' should be one of {list(SECTOR_KEYWORDS.keys())}"
    
    # Due to priority ordering (Textile > Manufacturing > Technology > Trading),
    # the assigned sector should be the expected sector OR a higher priority sector
    # if the text happens to contain multiple sector keywords
    sector_priority = ['Textile', 'Manufacturing', 'Technology', 'Trading']
    expected_priority = sector_priority.index(expected_sector)
    actual_priority = sector_priority.index(metadata['sector_tag'])
    
    # The actual sector should be equal to or higher priority than expected
    assert actual_priority <= expected_priority, \
        f"Expected sector '{expected_sector}' or higher priority, got '{metadata['sector_tag']}'"


@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')), 
               min_size=10, max_size=200))
@settings(max_examples=100)
def test_property_18_no_sector_keywords(text):
    """
    **Property 18 (Negative Case): No Sector Tag Without Keywords**
    
    For any legal text that does NOT contain sector keywords, the sector_tag 
    should be None.
    
    **Validates: Requirements 6.3, 6.4**
    """
    # Filter out texts that accidentally contain sector keywords
    text_lower = text.lower()
    contains_keyword = False
    for keywords in SECTOR_KEYWORDS.values():
        for keyword in keywords:
            # Check for word boundary matches
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                contains_keyword = True
                break
        if contains_keyword:
            break
    
    # Skip if text contains a sector keyword
    if contains_keyword:
        return
    
    # Extract metadata
    metadata = extract_metadata_from_text(text)
    
    # Sector tag should be None when no keywords present
    assert metadata['sector_tag'] is None, \
        f"Sector tag should be None when text has no sector keywords, got '{metadata['sector_tag']}'"


# ============================================================================
# Property 19: Date Format Conversion
# ============================================================================

# Strategy to generate valid dates in DD-MM-YYYY format
@st.composite
def valid_date_ddmmyyyy(draw):
    """Generate a valid date in DD-MM-YYYY format"""
    day = draw(st.integers(min_value=1, max_value=28))  # Use 28 to avoid month-specific issues
    month = draw(st.integers(min_value=1, max_value=12))
    year = draw(st.integers(min_value=1900, max_value=2099))
    
    # Format as DD-MM-YYYY
    date_str = f"{day:02d}-{month:02d}-{year}"
    
    # Expected ISO format
    iso_date = f"{year}-{month:02d}-{day:02d}"
    
    return date_str, iso_date


# Strategy to generate text with date patterns
@st.composite
def text_with_date_pattern(draw):
    """Generate text containing a date pattern"""
    date_str, iso_date = draw(valid_date_ddmmyyyy())
    
    # Choose a date pattern prefix
    pattern_prefix = draw(st.sampled_from([
        'w.e.f.',
        'with effect from',
        'effective from',
        'from'
    ]))
    
    # Choose separator (- or /)
    separator = draw(st.sampled_from(['-', '/']))
    date_with_sep = date_str.replace('-', separator)
    
    # Generate surrounding text
    prefix = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')), 
                         min_size=0, max_size=50))
    suffix = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')), 
                         min_size=0, max_size=50))
    
    # Construct text with date pattern
    text = f"{prefix} {pattern_prefix} {date_with_sep} {suffix}"
    
    return text, iso_date, date_with_sep, pattern_prefix


@given(text_with_date_pattern())
@settings(max_examples=100)
@example((
    "This provision shall apply w.e.f. 01-04-2023",
    "2023-04-01",
    "01-04-2023",
    "w.e.f."
))
@example((
    "Applicable with effect from 15-08-2022",
    "2022-08-15",
    "15-08-2022",
    "with effect from"
))
@example((
    "This rule is effective from 01/07/2021",
    "2021-07-01",
    "01/07/2021",
    "effective from"
))
def test_property_19_date_format_conversion(text_and_date):
    """
    **Property 19: Date Format Conversion**
    
    For any legal text containing date patterns (e.g., "w.e.f. 01-04-2023"), 
    the extracted effective_date should be converted to ISO format (YYYY-MM-DD).
    
    **Validates: Requirements 6.5**
    
    Property: If text contains a date pattern "DD-MM-YYYY" or "DD/MM/YYYY",
    then extract_metadata_from_text(text)['effective_date'] should equal "YYYY-MM-DD".
    """
    text, expected_iso_date, original_date, pattern_prefix = text_and_date
    
    # Extract metadata
    metadata = extract_metadata_from_text(text)
    
    # Effective date should be extracted
    assert metadata['effective_date'] is not None, \
        f"Effective date should be extracted from text containing '{pattern_prefix} {original_date}'"
    
    # Effective date should be in ISO format (YYYY-MM-DD)
    iso_format_pattern = r'^\d{4}-\d{2}-\d{2}$'
    assert re.match(iso_format_pattern, metadata['effective_date']), \
        f"Effective date '{metadata['effective_date']}' should be in ISO format YYYY-MM-DD"
    
    # Effective date should match the expected ISO date
    assert metadata['effective_date'] == expected_iso_date, \
        f"Expected ISO date '{expected_iso_date}', got '{metadata['effective_date']}'"


@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')), 
               min_size=10, max_size=200))
@settings(max_examples=100)
def test_property_19_no_date_patterns(text):
    """
    **Property 19 (Negative Case): No Date Without Patterns**
    
    For any legal text that does NOT contain date patterns, the effective_date 
    should be None.
    
    **Validates: Requirements 6.5**
    """
    # Filter out texts that accidentally contain date patterns
    date_pattern = r'(w\.e\.f\.|with\s+effect\s+from|effective\s+from|from)\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}'
    contains_date = re.search(date_pattern, text, re.IGNORECASE)
    
    # Skip if text contains a date pattern
    if contains_date:
        return
    
    # Extract metadata
    metadata = extract_metadata_from_text(text)
    
    # Effective date should be None when no date patterns present
    assert metadata['effective_date'] is None, \
        f"Effective date should be None when text has no date patterns, got '{metadata['effective_date']}'"


# ============================================================================
# Combined Property Test
# ============================================================================

@st.composite
def text_with_multiple_metadata(draw):
    """Generate text containing multiple metadata fields"""
    # Generate sector keyword
    sector = draw(st.sampled_from(list(SECTOR_KEYWORDS.keys())))
    sector_keyword = draw(st.sampled_from(SECTOR_KEYWORDS[sector]))
    
    # Generate date
    date_str, iso_date = draw(valid_date_ddmmyyyy())
    date_pattern = draw(st.sampled_from(['w.e.f.', 'with effect from', 'effective from']))
    
    # Generate turnover (optional)
    include_turnover = draw(st.booleans())
    turnover_text = ""
    expected_turnover = None
    if include_turnover:
        crores = draw(st.integers(min_value=1, max_value=100))
        turnover_text = f"turnover exceeding {crores} crore"
        expected_turnover = crores * 10000000
    
    # Construct text
    parts = [
        draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')), 
                    min_size=5, max_size=30)),
        sector_keyword,
        turnover_text,
        f"{date_pattern} {date_str}",
        draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')), 
                    min_size=5, max_size=30))
    ]
    text = " ".join(filter(None, parts))
    
    return text, sector, iso_date, expected_turnover


@given(text_with_multiple_metadata())
@settings(max_examples=100)
def test_combined_metadata_extraction(text_and_metadata):
    """
    **Combined Property Test: Multiple Metadata Fields**
    
    For any legal text containing multiple metadata fields (sector, date, turnover),
    all fields should be correctly extracted and formatted.
    
    **Validates: Requirements 6.3, 6.4, 6.5**
    """
    text, expected_sector, expected_date, expected_turnover = text_and_metadata
    
    # Extract metadata
    metadata = extract_metadata_from_text(text)
    
    # Sector tag should be assigned
    assert metadata['sector_tag'] is not None, \
        "Sector tag should be extracted from text with sector keyword"
    assert metadata['sector_tag'] in SECTOR_KEYWORDS.keys(), \
        f"Sector tag should be valid, got '{metadata['sector_tag']}'"
    
    # Effective date should be extracted and in ISO format
    assert metadata['effective_date'] is not None, \
        "Effective date should be extracted from text with date pattern"
    assert metadata['effective_date'] == expected_date, \
        f"Expected date '{expected_date}', got '{metadata['effective_date']}'"
    
    # Turnover should match if included
    if expected_turnover is not None:
        assert metadata['turnover_threshold'] == expected_turnover, \
            f"Expected turnover {expected_turnover}, got {metadata['turnover_threshold']}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

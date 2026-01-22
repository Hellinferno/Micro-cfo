#!/usr/bin/env python3
"""
Test script for extract_metadata_from_text() function
Validates Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from legal_ingestion import extract_metadata_from_text


def test_turnover_extraction_5_crore():
    """Test extraction of 5 crore turnover threshold"""
    text = "Any person whose turnover exceeding 5 crore shall be liable"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['turnover_threshold'] == 50000000, \
        f"Expected 50000000, got {metadata['turnover_threshold']}"
    print("✓ Test passed: 5 crore → 50000000 rupees")


def test_turnover_extraction_50_crore():
    """Test extraction of 50 crore turnover threshold"""
    text = "Applicable to businesses with turnover exceeding 50 crore"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['turnover_threshold'] == 500000000, \
        f"Expected 500000000, got {metadata['turnover_threshold']}"
    print("✓ Test passed: 50 crore → 500000000 rupees")


def test_turnover_with_rs_prefix():
    """Test extraction with Rs. prefix"""
    text = "aggregate turnover of Rs. 20 crore or more"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['turnover_threshold'] == 200000000, \
        f"Expected 200000000, got {metadata['turnover_threshold']}"
    print("✓ Test passed: Rs. 20 crore → 200000000 rupees")


def test_sector_tag_textile():
    """Test extraction of Textile sector tag"""
    text = "This provision applies to textile manufacturing units"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['sector_tag'] == 'Textile', \
        f"Expected 'Textile', got {metadata['sector_tag']}"
    print("✓ Test passed: 'textile' keyword → Textile sector")


def test_sector_tag_garment():
    """Test extraction of Textile sector tag using 'garment' keyword"""
    text = "Applicable to garment exporters and apparel manufacturers"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['sector_tag'] == 'Textile', \
        f"Expected 'Textile', got {metadata['sector_tag']}"
    print("✓ Test passed: 'garment' keyword → Textile sector")


def test_sector_tag_manufacturing():
    """Test extraction of Manufacturing sector tag"""
    text = "All manufacturing units must comply with this regulation"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['sector_tag'] == 'Manufacturing', \
        f"Expected 'Manufacturing', got {metadata['sector_tag']}"
    print("✓ Test passed: 'manufacturing' keyword → Manufacturing sector")


def test_sector_tag_technology():
    """Test extraction of Technology sector tag"""
    text = "Software companies and IT service providers are covered"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['sector_tag'] == 'Technology', \
        f"Expected 'Technology', got {metadata['sector_tag']}"
    print("✓ Test passed: 'software' keyword → Technology sector")


def test_sector_tag_trading():
    """Test extraction of Trading sector tag"""
    text = "This applies to trading businesses and wholesale dealers"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['sector_tag'] == 'Trading', \
        f"Expected 'Trading', got {metadata['sector_tag']}"
    print("✓ Test passed: 'trading' keyword → Trading sector")


def test_effective_date_wef():
    """Test extraction of effective date with w.e.f. pattern"""
    text = "This provision shall apply w.e.f. 01-04-2023"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['effective_date'] == '2023-04-01', \
        f"Expected '2023-04-01', got {metadata['effective_date']}"
    print("✓ Test passed: w.e.f. 01-04-2023 → 2023-04-01")


def test_effective_date_with_effect_from():
    """Test extraction of effective date with 'with effect from' pattern"""
    text = "Applicable with effect from 15-08-2022"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['effective_date'] == '2022-08-15', \
        f"Expected '2022-08-15', got {metadata['effective_date']}"
    print("✓ Test passed: with effect from 15-08-2022 → 2022-08-15")


def test_effective_date_slash_separator():
    """Test extraction of effective date with slash separator"""
    text = "This rule is effective from 01/07/2021"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['effective_date'] == '2021-07-01', \
        f"Expected '2021-07-01', got {metadata['effective_date']}"
    print("✓ Test passed: from 01/07/2021 → 2021-07-01")


def test_combined_metadata():
    """Test extraction of multiple metadata fields from same text"""
    text = """
    Section 25 - Registration for persons with turnover exceeding 5 crore
    
    This provision applies to textile manufacturing units and shall be
    effective from w.e.f. 01-04-2023.
    """
    metadata = extract_metadata_from_text(text)
    
    assert metadata['turnover_threshold'] == 50000000, \
        f"Expected turnover 50000000, got {metadata['turnover_threshold']}"
    assert metadata['sector_tag'] == 'Textile', \
        f"Expected sector 'Textile', got {metadata['sector_tag']}"
    assert metadata['effective_date'] == '2023-04-01', \
        f"Expected date '2023-04-01', got {metadata['effective_date']}"
    print("✓ Test passed: Combined metadata extraction")


def test_empty_text():
    """Test handling of empty text"""
    metadata = extract_metadata_from_text("")
    
    assert metadata['turnover_threshold'] is None
    assert metadata['sector_tag'] is None
    assert metadata['effective_date'] is None
    print("✓ Test passed: Empty text returns None values")


def test_no_metadata():
    """Test text with no extractable metadata"""
    text = "This is a general legal provision without specific metadata"
    metadata = extract_metadata_from_text(text)
    
    assert metadata['turnover_threshold'] is None
    assert metadata['sector_tag'] is None
    assert metadata['effective_date'] is None
    print("✓ Test passed: Text without metadata returns None values")


if __name__ == "__main__":
    print("Testing extract_metadata_from_text() function")
    print("=" * 60)
    
    # Run all tests
    test_turnover_extraction_5_crore()
    test_turnover_extraction_50_crore()
    test_turnover_with_rs_prefix()
    test_sector_tag_textile()
    test_sector_tag_garment()
    test_sector_tag_manufacturing()
    test_sector_tag_technology()
    test_sector_tag_trading()
    test_effective_date_wef()
    test_effective_date_with_effect_from()
    test_effective_date_slash_separator()
    test_combined_metadata()
    test_empty_text()
    test_no_metadata()
    
    print("=" * 60)
    print("All tests passed! ✓")

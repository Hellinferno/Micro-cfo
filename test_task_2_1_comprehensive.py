#!/usr/bin/env python3
"""
Comprehensive test for Task 2.1: extract_metadata_from_text() function
Validates Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from legal_ingestion import extract_metadata_from_text


def test_requirement_6_1_turnover_5_crore():
    """
    Requirement 6.1: WHEN processing legal text containing "turnover exceeding 5 crore", 
    THE Legal_Ingestion_Pipeline SHALL extract turnover_threshold as 50000000
    """
    test_cases = [
        "Any person whose turnover exceeding 5 crore shall register",
        "Applicable when turnover exceeds 5 crore",
        "For businesses with turnover above 5 crore",
        "Where aggregate turnover of 5 crore is reached",
    ]
    
    for text in test_cases:
        metadata = extract_metadata_from_text(text)
        assert metadata['turnover_threshold'] == 50000000, \
            f"Failed for text: {text}. Got {metadata['turnover_threshold']}"
    
    print("✓ Requirement 6.1 validated: 5 crore → 50000000 rupees")


def test_requirement_6_2_turnover_50_crore():
    """
    Requirement 6.2: WHEN processing legal text containing "turnover exceeding 50 crore", 
    THE Legal_Ingestion_Pipeline SHALL extract turnover_threshold as 500000000
    """
    test_cases = [
        "Businesses with turnover exceeding 50 crore must comply",
        "When turnover exceeds Rs. 50 crore",
        "Aggregate turnover of 50 crore or more",
        "For turnover above 50 crore",
    ]
    
    for text in test_cases:
        metadata = extract_metadata_from_text(text)
        assert metadata['turnover_threshold'] == 500000000, \
            f"Failed for text: {text}. Got {metadata['turnover_threshold']}"
    
    print("✓ Requirement 6.2 validated: 50 crore → 500000000 rupees")


def test_requirement_6_3_sector_textile():
    """
    Requirement 6.3: WHEN processing legal text mentioning "textile" or "garment", 
    THE Legal_Ingestion_Pipeline SHALL add sector_tag "Textile"
    """
    test_cases = [
        "This applies to textile manufacturing units",
        "Garment exporters must comply",
        "Applicable to fabric producers",
        "For apparel and clothing manufacturers",
        "Textile weaving and spinning operations",
    ]
    
    for text in test_cases:
        metadata = extract_metadata_from_text(text)
        assert metadata['sector_tag'] == 'Textile', \
            f"Failed for text: {text}. Got {metadata['sector_tag']}"
    
    print("✓ Requirement 6.3 validated: textile/garment keywords → Textile sector")


def test_requirement_6_4_sector_manufacturing():
    """
    Requirement 6.4: WHEN processing legal text mentioning "manufacturing" or "production", 
    THE Legal_Ingestion_Pipeline SHALL add sector_tag "Manufacturing"
    """
    test_cases = [
        "All manufacturing units must register",
        "Production facilities are covered",
        "Factory operations require compliance",
        "Industrial producers must follow",
        "Manufacturing and production activities",
    ]
    
    for text in test_cases:
        metadata = extract_metadata_from_text(text)
        assert metadata['sector_tag'] == 'Manufacturing', \
            f"Failed for text: {text}. Got {metadata['sector_tag']}"
    
    print("✓ Requirement 6.4 validated: manufacturing/production keywords → Manufacturing sector")


def test_requirement_6_5_effective_date():
    """
    Requirement 6.5: WHEN processing legal text containing date patterns like "w.e.f. 01-04-2023", 
    THE Legal_Ingestion_Pipeline SHALL extract effective_date in ISO format
    """
    test_cases = [
        ("This provision applies w.e.f. 01-04-2023", "2023-04-01"),
        ("Effective with effect from 15-08-2022", "2022-08-15"),
        ("Applicable from 01/07/2021", "2021-07-01"),
        ("This rule is effective from 10-11-2020", "2020-11-10"),
        ("w.e.f. 1-1-2024", "2024-01-01"),  # Single digit dates
    ]
    
    for text, expected_date in test_cases:
        metadata = extract_metadata_from_text(text)
        assert metadata['effective_date'] == expected_date, \
            f"Failed for text: {text}. Expected {expected_date}, got {metadata['effective_date']}"
    
    print("✓ Requirement 6.5 validated: Date patterns → ISO format (YYYY-MM-DD)")


def test_all_sectors():
    """Test all four sector types"""
    sectors = {
        'Textile': "textile manufacturing",
        'Manufacturing': "production facility",
        'Technology': "software development",
        'Trading': "wholesale trading"
    }
    
    for expected_sector, text in sectors.items():
        metadata = extract_metadata_from_text(text)
        assert metadata['sector_tag'] == expected_sector, \
            f"Failed for {expected_sector}. Got {metadata['sector_tag']}"
    
    print("✓ All sector tags validated: Textile, Manufacturing, Technology, Trading")


def test_sector_priority():
    """Test that sector priority works correctly (Textile > Manufacturing > Technology > Trading)"""
    # Text with both textile and manufacturing keywords - should return Textile
    text = "textile manufacturing facility"
    metadata = extract_metadata_from_text(text)
    assert metadata['sector_tag'] == 'Textile', \
        f"Priority failed: Expected Textile, got {metadata['sector_tag']}"
    
    print("✓ Sector priority validated: Textile takes precedence")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    # Empty text
    metadata = extract_metadata_from_text("")
    assert all(v is None for v in metadata.values()), "Empty text should return all None"
    
    # None text
    metadata = extract_metadata_from_text(None)
    assert all(v is None for v in metadata.values()), "None text should return all None"
    
    # Text with no metadata
    metadata = extract_metadata_from_text("This is a general provision")
    assert all(v is None for v in metadata.values()), "Text without metadata should return all None"
    
    # Decimal turnover values
    metadata = extract_metadata_from_text("turnover exceeding 7.5 crore")
    assert metadata['turnover_threshold'] == 75000000, "Decimal crores should work"
    
    print("✓ Edge cases validated: empty text, None, no metadata, decimal values")


def test_real_world_legal_text():
    """Test with realistic legal text containing multiple metadata fields"""
    legal_text = """
    Section 22 - Compulsory Registration
    
    (1) Every supplier shall be liable to be registered under this Act in the State 
    or Union territory, other than special category States, from where he makes a 
    taxable supply of goods or services or both, if his aggregate turnover exceeding 
    5 crore in a financial year:
    
    Provided that persons engaged exclusively in the business of supplying goods or 
    services or both that are not liable to tax or wholly exempt from tax under this 
    Act or under the Integrated Goods and Services Tax Act, shall not be liable to 
    registration.
    
    (2) Every person who, on the day immediately preceding the appointed day, is 
    registered or holds a licence under an existing law, shall be liable to be 
    registered under this Act with effect from the appointed day w.e.f. 01-07-2017.
    
    (3) Notwithstanding anything contained in sub-section (1), the following 
    categories of persons shall be required to be registered under this Act:
    
    (a) persons making any inter-State taxable supply;
    (b) casual taxable persons making taxable supply;
    (c) persons who are required to pay tax under reverse charge;
    (d) persons who are required to pay tax under sub-section (5) of section 9;
    (e) persons who supply goods or services or both on behalf of other taxable persons 
        whether as an agent or otherwise;
    (f) input service distributor;
    (g) persons who supply goods or services or both, other than supplies specified 
        under section 9(5), through such electronic commerce operator who is required 
        to collect tax at source under section 52;
    (h) every electronic commerce operator;
    (i) every person supplying online information and database access or retrieval 
        services from a place outside India to a person in India, other than a 
        registered person;
    (j) such other person or class of persons as may be notified by the Government 
        on the recommendations of the Council.
    """
    
    metadata = extract_metadata_from_text(legal_text)
    
    # Should extract turnover threshold
    assert metadata['turnover_threshold'] == 50000000, \
        f"Expected 50000000, got {metadata['turnover_threshold']}"
    
    # Should extract effective date
    assert metadata['effective_date'] == '2017-07-01', \
        f"Expected '2017-07-01', got {metadata['effective_date']}"
    
    # Sector tag might be None (no sector keywords in this text)
    # This is expected behavior
    
    print("✓ Real-world legal text validated: Multiple metadata fields extracted correctly")


def test_case_insensitivity():
    """Test that extraction is case-insensitive"""
    test_cases = [
        ("TURNOVER EXCEEDING 5 CRORE", 50000000),
        ("Turnover Exceeding 5 Crore", 50000000),
        ("turnover exceeding 5 crore", 50000000),
    ]
    
    for text, expected in test_cases:
        metadata = extract_metadata_from_text(text)
        assert metadata['turnover_threshold'] == expected, \
            f"Case insensitivity failed for: {text}"
    
    print("✓ Case insensitivity validated")


def test_return_type():
    """Test that function returns correct dictionary structure"""
    metadata = extract_metadata_from_text("test text")
    
    # Check it's a dictionary
    assert isinstance(metadata, dict), "Should return a dictionary"
    
    # Check it has all required keys
    required_keys = {'turnover_threshold', 'sector_tag', 'effective_date'}
    assert set(metadata.keys()) == required_keys, \
        f"Should have keys {required_keys}, got {set(metadata.keys())}"
    
    print("✓ Return type validated: Dictionary with correct keys")


if __name__ == "__main__":
    print("=" * 70)
    print("COMPREHENSIVE TEST: Task 2.1 - extract_metadata_from_text()")
    print("=" * 70)
    print()
    
    # Test each requirement
    test_requirement_6_1_turnover_5_crore()
    test_requirement_6_2_turnover_50_crore()
    test_requirement_6_3_sector_textile()
    test_requirement_6_4_sector_manufacturing()
    test_requirement_6_5_effective_date()
    
    print()
    print("Additional validation tests:")
    print("-" * 70)
    
    # Additional tests
    test_all_sectors()
    test_sector_priority()
    test_edge_cases()
    test_real_world_legal_text()
    test_case_insensitivity()
    test_return_type()
    
    print()
    print("=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
    print()
    print("Summary:")
    print("  ✓ Requirement 6.1: Turnover 5 crore extraction")
    print("  ✓ Requirement 6.2: Turnover 50 crore extraction")
    print("  ✓ Requirement 6.3: Textile sector tag extraction")
    print("  ✓ Requirement 6.4: Manufacturing sector tag extraction")
    print("  ✓ Requirement 6.5: Effective date extraction and ISO conversion")
    print()
    print("Task 2.1 implementation is complete and validated!")

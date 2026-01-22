#!/usr/bin/env python3
"""
Test for detect_law_type_from_filename function
Task 1.1 verification
"""

from legal_ingestion import detect_law_type_from_filename


def test_gst_detection():
    """Test GST pattern detection (CGST, IGST)"""
    assert detect_law_type_from_filename("CGST_Act_2017.pdf") == "GST"
    assert detect_law_type_from_filename("IGST_Act_2017.pdf") == "GST"
    assert detect_law_type_from_filename("cgst_rules.pdf") == "GST"  # Case insensitive
    assert detect_law_type_from_filename("path/to/IGST_document.pdf") == "GST"  # Full path
    print("✓ GST detection tests passed")


def test_income_tax_detection():
    """Test Income Tax pattern detection (Income Tax, IT Act)"""
    assert detect_law_type_from_filename("Income_Tax_Act_1961.pdf") == "Income Tax"
    assert detect_law_type_from_filename("IT_Act_amendments.pdf") == "Income Tax"
    assert detect_law_type_from_filename("income_tax_rules.pdf") == "Income Tax"  # Case insensitive
    assert detect_law_type_from_filename("data/IT Act 2023.pdf") == "Income Tax"  # Full path
    print("✓ Income Tax detection tests passed")


def test_corporate_law_detection():
    """Test Corporate Law pattern detection (Companies Act, MCA)"""
    assert detect_law_type_from_filename("Companies_Act_2013.pdf") == "Corporate Law"
    assert detect_law_type_from_filename("MCA_circular.pdf") == "Corporate Law"
    assert detect_law_type_from_filename("companies_act_amendments.pdf") == "Corporate Law"  # Case insensitive
    assert detect_law_type_from_filename("docs/MCA notification.pdf") == "Corporate Law"  # Full path
    print("✓ Corporate Law detection tests passed")


def test_subsidy_scheme_detection():
    """Test Subsidy Scheme pattern detection (PLI, Scheme)"""
    assert detect_law_type_from_filename("PLI_Textiles_Guidelines.pdf") == "Subsidy Scheme"
    assert detect_law_type_from_filename("Manufacturing_Scheme_2023.pdf") == "Subsidy Scheme"
    assert detect_law_type_from_filename("pli_electronics.pdf") == "Subsidy Scheme"  # Case insensitive
    assert detect_law_type_from_filename("schemes/PLI Guidelines.pdf") == "Subsidy Scheme"  # Full path
    print("✓ Subsidy Scheme detection tests passed")


def test_general_default():
    """Test default to General for unmatched patterns"""
    assert detect_law_type_from_filename("random_document.pdf") == "General"
    assert detect_law_type_from_filename("some_legal_text.txt") == "General"
    assert detect_law_type_from_filename("unknown.pdf") == "General"
    print("✓ General default tests passed")


def test_edge_cases():
    """Test edge cases"""
    # Empty string
    assert detect_law_type_from_filename("") == "General"
    
    # Multiple patterns - should match first one checked
    # GST is checked first, so CGST should win even if "scheme" is also present
    assert detect_law_type_from_filename("CGST_Scheme.pdf") == "GST"
    
    # Partial matches should work
    assert detect_law_type_from_filename("new_CGST_rules.pdf") == "GST"
    
    print("✓ Edge case tests passed")


if __name__ == "__main__":
    print("Testing detect_law_type_from_filename function...")
    print()
    
    test_gst_detection()
    test_income_tax_detection()
    test_corporate_law_detection()
    test_subsidy_scheme_detection()
    test_general_default()
    test_edge_cases()
    
    print()
    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)
    print()
    print("Requirements validated:")
    print("  ✓ 3.1: CGST/IGST → GST")
    print("  ✓ 3.2: Income Tax/IT Act → Income Tax")
    print("  ✓ 3.3: Companies Act/MCA → Corporate Law")
    print("  ✓ 3.4: PLI/Scheme → Subsidy Scheme")
    print("  ✓ 3.5: No match → General")

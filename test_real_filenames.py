#!/usr/bin/env python3
"""
Test detect_law_type_from_filename with actual filenames from seed_downloader.py
"""

from legal_ingestion import detect_law_type_from_filename


def test_actual_seed_filenames():
    """Test with the actual filenames configured in seed_downloader.py"""
    
    # From LEGAL_SOURCES in seed_downloader.py
    test_cases = [
        ("CGST_Act_2017.pdf", "GST"),
        ("IGST_Act_2017.pdf", "GST"),
        ("Income_Tax_Act_1961.pdf", "Income Tax"),
        ("Companies_Act_2013.pdf", "Corporate Law"),
        ("PLI_Textiles_Guidelines.pdf", "Subsidy Scheme"),
    ]
    
    print("Testing with actual seed downloader filenames:")
    print("=" * 60)
    
    all_passed = True
    for filename, expected_law_type in test_cases:
        detected = detect_law_type_from_filename(filename)
        status = "✓" if detected == expected_law_type else "✗"
        
        print(f"{status} {filename:40} → {detected:20} (expected: {expected_law_type})")
        
        if detected != expected_law_type:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All actual filenames detected correctly!")
        return True
    else:
        print("\n✗ Some filenames were not detected correctly!")
        return False


if __name__ == "__main__":
    success = test_actual_seed_filenames()
    exit(0 if success else 1)

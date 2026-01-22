#!/usr/bin/env python3
"""
Test suite for Task 3.1: Comprehensive tests for LegalTextSplitter patterns

This test suite validates the structure detection capabilities of the LegalTextSplitter class:
- Section boundary detection (Section X, Rule Y)
- Proviso clause detection ("Provided that")
- Sub-clause detection ((a), (b), (c))
- Section number extraction
- Chunk type preservation (main, proviso, sub_clause)

Validates Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from legal_ingestion import LegalTextSplitter, LegalChunk


class TestSectionBoundaryDetection:
    """
    Test section boundary detection patterns.
    
    Validates Requirement 5.1: WHEN processing a legal document, THE Legal_Ingestion_Pipeline 
    SHALL identify section boundaries using patterns like "Section X"
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_section_pattern_basic(self):
        """Test basic section pattern detection: 'Section 16'"""
        text = """
Section 16 - Eligibility and conditions for taking input tax credit

Every registered person shall be entitled to take credit of input tax charged.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16"
        assert "Section 16" in chunks[0].text
    
    def test_section_pattern_with_letter_suffix(self):
        """Test section pattern with letter suffix: 'Section 16A'"""
        text = """
Section 16A - Special provisions for input tax credit

This section applies to specific cases.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16A"
        assert "Section 16A" in chunks[0].text
    
    def test_multiple_sections_create_separate_chunks(self):
        """Test that multiple sections create separate chunks"""
        text = """
Section 16 - Eligibility and conditions

Every registered person shall be entitled to take credit.

Section 17 - Apportionment of credit

Input tax credit shall be apportioned.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 2
        assert chunks[0].section_number == "16"
        assert chunks[1].section_number == "17"
        assert "Section 16" in chunks[0].text
        assert "Section 17" in chunks[1].text
    
    def test_section_pattern_case_insensitive(self):
        """Test that section pattern matching is case-insensitive"""
        text = """
SECTION 16 - ELIGIBILITY AND CONDITIONS

Every registered person shall be entitled to take credit.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16"
    
    def test_rule_pattern_detection(self):
        """Test Rule pattern detection: 'Rule 42'"""
        text = """
Rule 42 - Manner of determination of input tax credit

The input tax credit shall be determined in the following manner.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "42"
        assert "Rule 42" in chunks[0].text
    
    def test_rule_pattern_with_letter_suffix(self):
        """Test Rule pattern with letter suffix: 'Rule 42A'"""
        text = """
Rule 42A - Special provisions for determination

Special provisions apply in certain cases.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "42A"
    
    def test_notification_pattern_detection(self):
        """Test Notification pattern detection"""
        text = """
Notification No. 12/2023 - Central Tax

In exercise of the powers conferred by section 168.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert "Notification No." in chunks[0].text
    
    def test_mixed_section_and_rule_boundaries(self):
        """Test document with both Section and Rule boundaries"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

Rule 42 - Manner of determination

The input tax credit shall be determined.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 2
        assert chunks[0].section_number == "16"
        assert chunks[1].section_number == "42"


class TestProvisoClauseDetection:
    """
    Test proviso clause detection patterns.
    
    Validates Requirement 5.2: WHEN processing a legal document, THE Legal_Ingestion_Pipeline 
    SHALL identify proviso clauses using patterns like "Provided that"
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_proviso_basic_pattern(self):
        """Test basic proviso pattern: 'Provided that'"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

Provided that where the goods are received in lots, the credit shall be taken upon receipt of the last lot.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        # Proviso should be part of the same chunk as the section
        assert len(chunks) == 1
        assert "Provided that" in chunks[0].text
        assert chunks[0].chunk_type == "proviso"
    
    def test_proviso_with_leading_whitespace(self):
        """Test proviso pattern with leading whitespace"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

    Provided that where the goods are received in lots.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert "Provided that" in chunks[0].text
        assert chunks[0].chunk_type == "proviso"
    
    def test_proviso_case_insensitive(self):
        """Test that proviso pattern matching is case-insensitive"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

PROVIDED THAT where the goods are received in lots.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "proviso"
    
    def test_proviso_further_pattern(self):
        """Test 'Provided further that' pattern"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

Provided that where the goods are received in lots.

Provided further that the credit shall not exceed the amount specified.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert "Provided further that" in chunks[0].text
        assert chunks[0].chunk_type == "proviso"
    
    def test_proviso_appends_to_section(self):
        """Test that proviso appends to the previous section chunk"""
        text = """
Section 16 - Eligibility conditions

(1) Every registered person shall be entitled to take credit.

Provided that where the goods are received in lots.

Section 17 - Apportionment of credit

Input tax credit shall be apportioned.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 2
        # First chunk should contain both section and proviso
        assert "Section 16" in chunks[0].text
        assert "Provided that" in chunks[0].text
        assert chunks[0].chunk_type == "proviso"
        # Second chunk should be separate
        assert "Section 17" in chunks[1].text


class TestSubClauseDetection:
    """
    Test sub-clause detection patterns.
    
    Validates Requirement 5.3: WHEN processing a legal document, THE Legal_Ingestion_Pipeline 
    SHALL identify sub-clauses using patterns like "(a)", "(b)", "(c)"
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_sub_clause_basic_pattern(self):
        """Test basic sub-clause pattern: '(a)', '(b)', '(c)'"""
        text = """
Section 16 - Eligibility conditions

(1) Every registered person shall be entitled to take credit if:

(a) he is in possession of a tax invoice;
(b) he has received the goods or services;
(c) the tax charged has been paid to the Government.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        # All sub-clauses should be part of the same chunk
        assert len(chunks) == 1
        assert "(a)" in chunks[0].text
        assert "(b)" in chunks[0].text
        assert "(c)" in chunks[0].text
        assert chunks[0].chunk_type == "sub_clause"
    
    def test_sub_clause_numeric_pattern(self):
        """Test numeric sub-clause pattern: '(1)', '(2)', '(3)'"""
        text = """
Section 16 - Eligibility conditions

The following conditions apply:

(1) The person must be registered;
(2) The person must have a valid tax invoice;
(3) The tax must have been paid.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert "(1)" in chunks[0].text
        assert "(2)" in chunks[0].text
        assert "(3)" in chunks[0].text
        assert chunks[0].chunk_type == "sub_clause"
    
    def test_sub_clause_with_leading_whitespace(self):
        """Test sub-clause pattern with leading whitespace"""
        text = """
Section 16 - Eligibility conditions

The following conditions apply:

    (a) The person must be registered;
    (b) The person must have a valid tax invoice.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert "(a)" in chunks[0].text
        assert "(b)" in chunks[0].text
        assert chunks[0].chunk_type == "sub_clause"
    
    def test_sub_clause_appends_to_section(self):
        """Test that sub-clauses append to the previous section chunk"""
        text = """
Section 16 - Eligibility conditions

(1) Every registered person shall be entitled to take credit if:

(a) he is in possession of a tax invoice;
(b) he has received the goods or services.

Section 17 - Apportionment of credit

Input tax credit shall be apportioned.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 2
        # First chunk should contain section and sub-clauses
        assert "Section 16" in chunks[0].text
        assert "(a)" in chunks[0].text
        assert "(b)" in chunks[0].text
        assert chunks[0].chunk_type == "sub_clause"
        # Second chunk should be separate
        assert "Section 17" in chunks[1].text


class TestSectionNumberExtraction:
    """
    Test section number extraction.
    
    Validates Requirement 5.4: WHEN creating a Legal_Chunk, THE System SHALL extract 
    the section_number from the text
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_section_number_extraction_basic(self):
        """Test extraction of basic section number"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16"
    
    def test_section_number_extraction_with_letter(self):
        """Test extraction of section number with letter suffix"""
        text = """
Section 16A - Special provisions

Special provisions apply in certain cases.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16A"
    
    def test_section_number_extraction_multiple_letters(self):
        """Test extraction of section number with multiple letter suffixes"""
        text = """
Section 16AA - Additional special provisions

Additional special provisions apply.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16AA"
    
    def test_rule_number_extraction(self):
        """Test extraction of rule number"""
        text = """
Rule 42 - Manner of determination

The input tax credit shall be determined.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "42"
    
    def test_rule_number_extraction_with_letter(self):
        """Test extraction of rule number with letter suffix"""
        text = """
Rule 42B - Special manner of determination

Special provisions apply.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "42B"
    
    def test_section_number_none_for_notification(self):
        """Test that notification chunks have None as section_number"""
        text = """
Notification No. 12/2023 - Central Tax

In exercise of the powers conferred.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number is None
    
    def test_section_number_preserved_across_chunks(self):
        """Test that section numbers are correctly assigned to their respective chunks"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

Section 17 - Apportionment of credit

Input tax credit shall be apportioned.

Section 18 - Availability of credit

Credit shall be available in certain cases.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 3
        assert chunks[0].section_number == "16"
        assert chunks[1].section_number == "17"
        assert chunks[2].section_number == "18"


class TestChunkTypePreservation:
    """
    Test chunk type preservation.
    
    Validates Requirement 5.5: WHEN creating a Legal_Chunk, THE System SHALL preserve 
    the chunk_type (main, proviso, sub_clause)
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_chunk_type_main_for_section(self):
        """Test that a basic section has chunk_type 'main'"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "main"
    
    def test_chunk_type_proviso_for_proviso_clause(self):
        """Test that a proviso clause has chunk_type 'proviso'"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

Provided that where the goods are received in lots.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "proviso"
    
    def test_chunk_type_sub_clause_for_sub_clauses(self):
        """Test that sub-clauses have chunk_type 'sub_clause'"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit if:

(a) he is in possession of a tax invoice;
(b) he has received the goods or services.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "sub_clause"
    
    def test_chunk_type_priority_proviso_over_sub_clause(self):
        """Test that proviso takes priority when both patterns are present"""
        text = """
Section 16 - Eligibility conditions

Every registered person shall be entitled to take credit.

Provided that the following conditions apply:

(a) he is in possession of a tax invoice;
(b) he has received the goods or services.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        # Proviso pattern should take priority
        assert chunks[0].chunk_type == "proviso"
    
    def test_chunk_type_preserved_across_multiple_chunks(self):
        """Test that chunk types are correctly preserved for multiple chunks"""
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
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 3
        assert chunks[0].chunk_type == "main"
        assert chunks[1].chunk_type == "sub_clause"
        assert chunks[2].chunk_type == "proviso"


class TestComplexLegalStructures:
    """
    Test complex legal structures with multiple patterns combined.
    
    This class tests realistic scenarios where sections, provisos, and sub-clauses
    are combined in various ways.
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_section_with_subsections_and_proviso(self):
        """Test a section with numbered subsections and a proviso"""
        text = """
Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit unless the turnover exceeds 5 crore.

Provided that where the goods against an invoice are received in lots or instalments, the registered person shall be entitled to take credit upon receipt of the last lot or instalment.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16"
        assert chunks[0].chunk_type == "proviso"
        assert "(1)" in chunks[0].text
        assert "(2)" in chunks[0].text
        assert "Provided that" in chunks[0].text
    
    def test_section_with_lettered_sub_clauses_and_conditions(self):
        """Test a section with lettered sub-clauses"""
        text = """
Section 16 - Eligibility conditions

(2) Every registered person shall be entitled to take credit if:

(a) he is in possession of a tax invoice or debit note issued by a supplier registered under this Act;
(b) he has received the goods or services or both;
(c) the tax charged has been actually paid to the Government.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16"
        assert chunks[0].chunk_type == "sub_clause"
        assert "(a)" in chunks[0].text
        assert "(b)" in chunks[0].text
        assert "(c)" in chunks[0].text
    
    def test_multiple_sections_with_mixed_structures(self):
        """Test multiple sections with different structures"""
        text = """
Section 16 - Eligibility and conditions

(1) Every registered person shall be entitled to take credit.

(2) The credit shall be subject to the following conditions:

(a) he is in possession of a tax invoice;
(b) he has received the goods or services.

Provided that where the goods are received in lots.

Section 17 - Apportionment of credit and blocked credits

(5) Input tax credit shall not be available in respect of the following:

(a) motor vehicles for transportation of persons;
(b) food and beverages;
(c) outdoor catering services.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 2
        
        # First chunk: Section 16 with proviso
        assert chunks[0].section_number == "16"
        assert chunks[0].chunk_type == "proviso"
        assert "(1)" in chunks[0].text
        assert "(2)" in chunks[0].text
        assert "(a)" in chunks[0].text
        assert "Provided that" in chunks[0].text
        
        # Second chunk: Section 17 with sub-clauses
        assert chunks[1].section_number == "17"
        assert chunks[1].chunk_type == "sub_clause"
        assert "(5)" in chunks[1].text
        assert "(a)" in chunks[1].text
        assert "(b)" in chunks[1].text
        assert "(c)" in chunks[1].text
    
    def test_rule_with_sub_rules_and_provisos(self):
        """Test a rule with sub-rules and provisos"""
        text = """
Rule 42 - Manner of determination of input tax credit

(1) The input tax credit shall be determined in the following manner:

(a) the credit shall be calculated based on the tax invoice;
(b) the credit shall be subject to verification.

Provided that in case of discrepancy, the credit shall be adjusted.

Rule 43 - Time limit for taking input tax credit

The credit shall be taken within the prescribed time limit.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 2
        
        # First chunk: Rule 42 with sub-clauses and proviso
        assert chunks[0].section_number == "42"
        assert chunks[0].chunk_type == "proviso"
        assert "(a)" in chunks[0].text
        assert "(b)" in chunks[0].text
        assert "Provided that" in chunks[0].text
        
        # Second chunk: Rule 43
        assert chunks[1].section_number == "43"
        assert chunks[1].chunk_type == "main"


class TestEdgeCases:
    """
    Test edge cases and boundary conditions.
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_empty_text(self):
        """Test handling of empty text"""
        text = ""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 0
    
    def test_whitespace_only_text(self):
        """Test handling of whitespace-only text"""
        text = "   \n\n   \t\t   \n   "
        chunks = self.splitter.split_legal_text(text, "GST")
        
        # Should create one chunk with the whitespace (or no chunks if filtered)
        # The behavior depends on implementation details
        assert isinstance(chunks, list)
    
    def test_text_without_section_markers(self):
        """Test handling of text without any section markers"""
        text = """
This is some legal text without any section markers.
It should still be processed into a chunk.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number is None
        assert chunks[0].chunk_type == "main"
    
    def test_proviso_without_parent_section(self):
        """Test handling of proviso clause without a parent section"""
        text = """
Provided that where the goods are received in lots.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "proviso"
        assert chunks[0].section_number is None
    
    def test_sub_clause_without_parent_section(self):
        """Test handling of sub-clause without a parent section"""
        text = """
(a) he is in possession of a tax invoice;
(b) he has received the goods or services.
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "sub_clause"
        assert chunks[0].section_number is None
    
    def test_section_with_no_content(self):
        """Test handling of section with no content after it"""
        text = """
Section 16 - Eligibility conditions
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 1
        assert chunks[0].section_number == "16"
    
    def test_multiple_consecutive_sections(self):
        """Test handling of multiple consecutive sections with no content between"""
        text = """
Section 16 - Eligibility conditions
Section 17 - Apportionment of credit
Section 18 - Availability of credit
"""
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) == 3
        assert chunks[0].section_number == "16"
        assert chunks[1].section_number == "17"
        assert chunks[2].section_number == "18"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

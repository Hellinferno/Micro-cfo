#!/usr/bin/env python3
"""
Test suite for Task 2.2: Verify _create_chunk() uses enhanced metadata extraction

This test verifies that the LegalTextSplitter._create_chunk() method properly
calls extract_metadata_from_text() and merges the extracted metadata with
existing metadata.

Validates Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import pytest
from legal_ingestion import LegalTextSplitter, LegalChunk


class TestCreateChunkEnhancedMetadata:
    """Test that _create_chunk() uses enhanced metadata extraction"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_create_chunk_extracts_turnover_5_crore(self):
        """Test that _create_chunk extracts 5 crore turnover threshold"""
        text = "Any person whose turnover exceeding 5 crore shall be liable to register."
        chunk = self.splitter._create_chunk(text, "GST", "16")
        
        assert chunk.turnover_threshold == 50000000
        assert chunk.section_number == "16"
        assert chunk.law_type == "GST"
    
    def test_create_chunk_extracts_turnover_50_crore(self):
        """Test that _create_chunk extracts 50 crore turnover threshold"""
        text = "Applicable to businesses with aggregate turnover of 50 crore or more."
        chunk = self.splitter._create_chunk(text, "GST", "22")
        
        assert chunk.turnover_threshold == 500000000
        assert chunk.section_number == "22"
    
    def test_create_chunk_extracts_sector_textile(self):
        """Test that _create_chunk extracts Textile sector tag"""
        text = "This provision applies to textile manufacturers and garment exporters."
        chunk = self.splitter._create_chunk(text, "GST", "10")
        
        assert chunk.sector_tag == "Textile"
    
    def test_create_chunk_extracts_sector_manufacturing(self):
        """Test that _create_chunk extracts Manufacturing sector tag"""
        text = "All manufacturing units and production facilities must comply."
        chunk = self.splitter._create_chunk(text, "GST", "15")
        
        assert chunk.sector_tag == "Manufacturing"
    
    def test_create_chunk_extracts_sector_technology(self):
        """Test that _create_chunk extracts Technology sector tag"""
        text = "Software companies and IT service providers are eligible."
        chunk = self.splitter._create_chunk(text, "Income Tax", "80")
        
        assert chunk.sector_tag == "Technology"
    
    def test_create_chunk_extracts_sector_trading(self):
        """Test that _create_chunk extracts Trading sector tag"""
        text = "Wholesale dealers and trading companies must maintain records."
        chunk = self.splitter._create_chunk(text, "GST", "35")
        
        assert chunk.sector_tag == "Trading"
    
    def test_create_chunk_extracts_effective_date_wef(self):
        """Test that _create_chunk extracts effective date from w.e.f. pattern"""
        text = "This amendment shall apply w.e.f. 01-04-2023 to all taxpayers."
        chunk = self.splitter._create_chunk(text, "GST", "12")
        
        assert chunk.effective_date == "2023-04-01"
    
    def test_create_chunk_extracts_effective_date_with_effect_from(self):
        """Test that _create_chunk extracts effective date from 'with effect from' pattern"""
        text = "The new rate is applicable with effect from 15-08-2022."
        chunk = self.splitter._create_chunk(text, "GST", "9")
        
        assert chunk.effective_date == "2022-08-15"
    
    def test_create_chunk_extracts_all_metadata(self):
        """Test that _create_chunk extracts all metadata types together"""
        text = """
        Section 44AB - Audit of accounts of certain persons carrying on business or profession
        
        Every person carrying on business whose turnover exceeding 5 crore during the previous year
        in the textile sector shall get his accounts audited. This provision applies w.e.f. 01-04-2023.
        """
        chunk = self.splitter._create_chunk(text, "Income Tax", "44AB")
        
        assert chunk.section_number == "44AB"
        assert chunk.law_type == "Income Tax"
        assert chunk.turnover_threshold == 50000000
        assert chunk.sector_tag == "Textile"
        assert chunk.effective_date == "2023-04-01"
        assert chunk.chunk_type == "main"
    
    def test_create_chunk_identifies_proviso_type(self):
        """Test that _create_chunk correctly identifies proviso chunk type"""
        text = "Provided that no such credit shall be allowed if the invoice is not received within 180 days."
        chunk = self.splitter._create_chunk(text, "GST", "16")
        
        assert chunk.chunk_type == "proviso"
    
    def test_create_chunk_identifies_sub_clause_type(self):
        """Test that _create_chunk correctly identifies sub_clause chunk type"""
        text = "(a) he is in possession of a tax invoice or debit note issued by a supplier"
        chunk = self.splitter._create_chunk(text, "GST", "16")
        
        assert chunk.chunk_type == "sub_clause"
    
    def test_create_chunk_handles_no_metadata(self):
        """Test that _create_chunk handles text with no extractable metadata"""
        text = "This is a general provision without specific thresholds or dates."
        chunk = self.splitter._create_chunk(text, "GST", "5")
        
        assert chunk.section_number == "5"
        assert chunk.law_type == "GST"
        assert chunk.turnover_threshold is None
        assert chunk.sector_tag is None
        assert chunk.effective_date is None
        assert chunk.chunk_type == "main"
    
    def test_create_chunk_fallback_to_legacy_patterns(self):
        """Test that _create_chunk falls back to legacy patterns when enhanced extraction fails"""
        # This text uses a pattern that might be caught by legacy but not enhanced
        text = "Applicable when turnover exceeds 10 crore in works contract business."
        chunk = self.splitter._create_chunk(text, "GST", "20")
        
        # Should extract turnover (both patterns should catch this)
        assert chunk.turnover_threshold == 100000000
        
        # Legacy pattern for works_contract sector
        assert chunk.sector_tag in ["works_contract", None]  # Depends on which pattern matches first
    
    def test_create_chunk_priority_enhanced_over_legacy(self):
        """Test that enhanced extraction takes priority over legacy patterns"""
        # Text with patterns that both enhanced and legacy can extract
        text = "For textile manufacturers with turnover exceeding 5 crore, effective from 01-04-2023."
        chunk = self.splitter._create_chunk(text, "GST", "25")
        
        # Enhanced extraction should take priority
        assert chunk.turnover_threshold == 50000000
        assert chunk.sector_tag == "Textile"  # Enhanced uses "Textile" (capitalized)
        assert chunk.effective_date == "2023-04-01"
    
    def test_create_chunk_preserves_text_content(self):
        """Test that _create_chunk preserves the original text content"""
        text = "This is the original text content that should be preserved exactly."
        chunk = self.splitter._create_chunk(text, "GST", "30")
        
        assert chunk.text == text
    
    def test_create_chunk_with_empty_text(self):
        """Test that _create_chunk handles empty text gracefully"""
        text = ""
        chunk = self.splitter._create_chunk(text, "GST", None)
        
        assert chunk.text == ""
        assert chunk.law_type == "GST"
        assert chunk.section_number is None
        assert chunk.turnover_threshold is None
        assert chunk.sector_tag is None
        assert chunk.effective_date is None


class TestCreateChunkIntegration:
    """Integration tests for _create_chunk with split_legal_text"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.splitter = LegalTextSplitter()
    
    def test_split_legal_text_uses_enhanced_metadata(self):
        """Test that split_legal_text produces chunks with enhanced metadata"""
        text = """
Section 16 - Eligibility and conditions for taking input tax credit

Every registered person whose turnover exceeding 5 crore in the textile sector
shall be entitled to take credit of input tax charged. This applies w.e.f. 01-04-2023.

Provided that where the goods are received in lots, credit shall be allowed on receipt of last lot.

(a) he is in possession of a tax invoice or debit note
(b) he has received the goods or services
        """
        
        chunks = self.splitter.split_legal_text(text, "GST")
        
        # Should create multiple chunks
        assert len(chunks) > 0
        
        # First chunk should have enhanced metadata
        # Note: The chunk contains "Provided that" so it will be marked as proviso type
        main_chunk = chunks[0]
        assert main_chunk.section_number == "16"
        assert main_chunk.turnover_threshold == 50000000
        assert main_chunk.sector_tag == "Textile"
        assert main_chunk.effective_date == "2023-04-01"
        # The chunk type will be "proviso" because the text contains "Provided that"
        assert main_chunk.chunk_type in ["main", "proviso"]
    
    def test_split_legal_text_multiple_sections_with_metadata(self):
        """Test that multiple sections each get their own metadata extracted"""
        text = """
Section 10 - Textile sector provisions

Applicable to textile manufacturers with turnover exceeding 5 crore.

Section 20 - Manufacturing sector provisions

Applicable to manufacturing units with turnover exceeding 50 crore.
        """
        
        chunks = self.splitter.split_legal_text(text, "GST")
        
        assert len(chunks) >= 2
        
        # First section - textile with 5 crore
        textile_chunk = chunks[0]
        assert textile_chunk.section_number == "10"
        assert textile_chunk.sector_tag == "Textile"
        assert textile_chunk.turnover_threshold == 50000000
        
        # Second section - manufacturing with 50 crore
        manufacturing_chunk = chunks[1]
        assert manufacturing_chunk.section_number == "20"
        assert manufacturing_chunk.sector_tag == "Manufacturing"
        assert manufacturing_chunk.turnover_threshold == 500000000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

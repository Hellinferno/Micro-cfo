#!/usr/bin/env python3
"""
Phase 1: Structure-Aware Legal Document Ingestion
Converts legal PDFs into smart chunks with metadata
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class LegalChunk:
    """Smart chunk with metadata"""
    text: str
    law_type: str
    section_number: Optional[str] = None
    turnover_threshold: Optional[float] = None
    sector_tag: Optional[str] = None
    effective_date: Optional[str] = None
    chunk_type: str = "main"  # main, proviso, sub_clause

class LegalTextSplitter:
    """CA-Logic Text Splitter for Legal Documents"""
    
    # Patterns that start a new chunk
    SECTION_PATTERN = re.compile(r'^Section\s+(\d+[A-Z]*)', re.MULTILINE | re.IGNORECASE)
    RULE_PATTERN = re.compile(r'^Rule\s+(\d+[A-Z]*)', re.MULTILINE | re.IGNORECASE)
    NOTIFICATION_PATTERN = re.compile(r'^Notification\s+No\.', re.MULTILINE | re.IGNORECASE)
    
    # Patterns that should append to previous chunk
    PROVISO_PATTERN = re.compile(r'^\s*Provided\s+that', re.MULTILINE | re.IGNORECASE)
    SUB_CLAUSE_PATTERN = re.compile(r'^\s*\([a-z0-9]+\)', re.MULTILINE)
    
    # Metadata extraction patterns
    TURNOVER_PATTERN = re.compile(r'turnover\s+(?:exceeds?|above|more\s+than)\s+(?:Rs\.?\s*)?(\d+)\s*crore', re.IGNORECASE)
    SECTOR_PATTERNS = {
        'textile': re.compile(r'\b(textile|fabric|garment|apparel)\b', re.IGNORECASE),
        'manufacturing': re.compile(r'\b(manufacturing|factory|production)\b', re.IGNORECASE),
        'works_contract': re.compile(r'\bworks?\s+contract\b', re.IGNORECASE),
        'technology': re.compile(r'\b(software|technology|IT|information\s+technology)\b', re.IGNORECASE),
    }
    DATE_PATTERN = re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})')
    
    def split_legal_text(self, text: str, law_type: str = "GST") -> List[LegalChunk]:
        """
        Split legal text into smart chunks preserving structure
        """
        chunks = []
        current_chunk = []
        current_section = None
        
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a new section/rule/notification
            section_match = self.SECTION_PATTERN.match(line)
            rule_match = self.RULE_PATTERN.match(line)
            notification_match = self.NOTIFICATION_PATTERN.match(line)
            
            if section_match or rule_match or notification_match:
                # Save previous chunk if exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, law_type, current_section))
                
                # Start new chunk
                current_chunk = [line]
                current_section = section_match.group(1) if section_match else (
                    rule_match.group(1) if rule_match else None
                )
            
            # Check if this is a proviso or sub-clause (append to previous)
            elif self.PROVISO_PATTERN.match(line) or self.SUB_CLAUSE_PATTERN.match(line):
                if current_chunk:
                    current_chunk.append(line)
                else:
                    # Edge case: proviso without parent section
                    current_chunk = [line]
            
            else:
                # Regular line - add to current chunk
                if current_chunk or line.strip():
                    current_chunk.append(line)
            
            i += 1
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(self._create_chunk(chunk_text, law_type, current_section))
        
        return chunks
    
    def _create_chunk(self, text: str, law_type: str, section_number: Optional[str]) -> LegalChunk:
        """Create a LegalChunk with extracted metadata"""
        chunk = LegalChunk(
            text=text,
            law_type=law_type,
            section_number=section_number
        )
        
        # Extract turnover threshold
        turnover_match = self.TURNOVER_PATTERN.search(text)
        if turnover_match:
            crores = float(turnover_match.group(1))
            chunk.turnover_threshold = crores * 10000000  # Convert to rupees
        
        # Extract sector tags
        for sector, pattern in self.SECTOR_PATTERNS.items():
            if pattern.search(text):
                chunk.sector_tag = sector
                break
        
        # Extract effective date
        date_match = self.DATE_PATTERN.search(text)
        if date_match:
            day, month, year = date_match.groups()
            chunk.effective_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Determine chunk type
        if self.PROVISO_PATTERN.search(text):
            chunk.chunk_type = "proviso"
        elif self.SUB_CLAUSE_PATTERN.search(text):
            chunk.chunk_type = "sub_clause"
        
        return chunk


class LegalDocumentProcessor:
    """Process PDF documents and extract legal text"""
    
    def __init__(self):
        self.splitter = LegalTextSplitter()
    
    def process_pdf(self, pdf_path: str, law_type: str = "GST") -> List[LegalChunk]:
        """
        Process a PDF file and return smart chunks
        """
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(pdf_path)
            full_text = ""
            
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            return self.splitter.split_legal_text(full_text, law_type)
        
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return []
    
    def process_text_file(self, text_path: str, law_type: str = "GST") -> List[LegalChunk]:
        """
        Process a text file and return smart chunks
        """
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return self.splitter.split_legal_text(text, law_type)
        
        except Exception as e:
            print(f"Error processing text file: {e}")
            return []


# Example usage and testing
if __name__ == "__main__":
    # Test with sample legal text
    sample_text = """
Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged on any supply of goods or services or both to him which are used or intended to be used in the course or furtherance of his business.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless the turnover exceeds 5 crore.

Provided that where the goods against an invoice are received in lots or instalments, the registered person shall be entitled to take credit upon receipt of the last lot or instalment.

(a) he is in possession of a tax invoice or debit note issued by a supplier registered under this Act;
(b) he has received the goods or services or both.

Section 17 - Apportionment of credit and blocked credits

(5) Notwithstanding anything contained in sub-section (1) of section 16 and subsection (1) of section 18, input tax credit shall not be available in respect of the following, namely:—

(a) motor vehicles for transportation of persons having approved seating capacity of not more than thirteen persons (including the driver), except when they are used for making the following taxable supplies, namely:—
    """
    
    processor = LegalDocumentProcessor()
    chunks = processor.splitter.split_legal_text(sample_text, "GST")
    
    print(f"Generated {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  Section: {chunk.section_number}")
        print(f"  Type: {chunk.chunk_type}")
        print(f"  Turnover Threshold: {chunk.turnover_threshold}")
        print(f"  Text Preview: {chunk.text[:100]}...")
        print()

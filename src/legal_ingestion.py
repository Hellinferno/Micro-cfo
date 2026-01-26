#!/usr/bin/env python3
"""
Phase 1: Structure-Aware Legal Document Ingestion
Converts legal PDFs into smart chunks with metadata
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass


def detect_law_type_from_filename(filename: str) -> str:
    """
    Detect law type from filename patterns.
    
    Args:
        filename: The filename to analyze (can be full path or just filename)
    
    Returns:
        str: One of "GST", "Income Tax", "Corporate Law", "Subsidy Scheme", or "General"
    
    Examples:
        >>> detect_law_type_from_filename("CGST_Act_2017.pdf")
        'GST'
        >>> detect_law_type_from_filename("Income_Tax_Act_1961.pdf")
        'Income Tax'
        >>> detect_law_type_from_filename("Companies_Act_2013.pdf")
        'Corporate Law'
        >>> detect_law_type_from_filename("PLI_Textiles_Guidelines.pdf")
        'Subsidy Scheme'
        >>> detect_law_type_from_filename("random_document.pdf")
        'General'
    """
    # Extract just the filename from a full path (handle both / and \ separators)
    import os
    filename_only = os.path.basename(filename)
    
    # Convert to uppercase and normalize separators for case-insensitive matching
    # Replace underscores and hyphens with spaces for consistent matching
    filename_normalized = filename_only.upper().replace("_", " ").replace("-", " ")
    
    # Check for GST patterns (CGST, IGST)
    if "CGST" in filename_normalized or "IGST" in filename_normalized:
        return "GST"
    
    # Check for Income Tax patterns (Income Tax, IT Act)
    if "INCOME TAX" in filename_normalized or "IT ACT" in filename_normalized:
        return "Income Tax"
    
    # Check for Corporate Law patterns (Companies Act, MCA)
    if "COMPANIES ACT" in filename_normalized or "MCA" in filename_normalized:
        return "Corporate Law"
    
    # Check for Subsidy Scheme patterns (PLI, Scheme)
    if "PLI" in filename_normalized or "SCHEME" in filename_normalized:
        return "Subsidy Scheme"
    
    # Default to General if no match
    return "General"


def extract_metadata_from_text(text: str, law_type: str = "GST") -> Dict[str, Optional[any]]:
    """
    Extract metadata from legal text including turnover thresholds, sector tags, and effective dates.
    
    This function analyzes legal text to extract:
    - Turnover thresholds: Converts "turnover exceeding X crore" to numeric rupees (X * 10000000)
    - Sector tags: Identifies industry sectors through keyword matching
    - Effective dates: Extracts dates in formats like "w.e.f. DD-MM-YYYY" and converts to ISO format
    
    Args:
        text: Legal text to analyze
        law_type: Type of law (used for context-specific extraction)
    
    Returns:
        Dict with keys:
            - turnover_threshold: int or None (threshold in rupees)
            - sector_tag: str or None (Textile, Manufacturing, Technology, Trading)
            - effective_date: str or None (ISO format YYYY-MM-DD)
    
    Examples:
        >>> text = "Any person whose turnover exceeding 5 crore in the textile sector"
        >>> metadata = extract_metadata_from_text(text)
        >>> metadata['turnover_threshold']
        50000000
        >>> metadata['sector_tag']
        'Textile'
        
        >>> text = "This provision shall apply w.e.f. 01-04-2023"
        >>> metadata = extract_metadata_from_text(text)
        >>> metadata['effective_date']
        '2023-04-01'
    
    Validates Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    metadata = {
        'turnover_threshold': None,
        'sector_tag': None,
        'effective_date': None
    }
    
    if not text:
        return metadata
    
    # Extract turnover threshold
    # Patterns to match:
    # - "turnover exceeding 5 crore"
    # - "turnover exceeds Rs. 50 crore"
    # - "aggregate turnover of 5 crore"
    # - "turnover of more than 50 crore"
    turnover_patterns = [
        r'turnover\s+(?:exceeding|exceeds|above|of\s+more\s+than)\s+(?:Rs\.?\s*)?(\d+(?:\.\d+)?)\s*crore',
        r'aggregate\s+turnover\s+(?:of|exceeding|exceeds)\s+(?:Rs\.?\s*)?(\d+(?:\.\d+)?)\s*crore',
        r'turnover\s+of\s+(?:Rs\.?\s*)?(\d+(?:\.\d+)?)\s*crore\s+or\s+more'
    ]
    
    for pattern in turnover_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            crores = float(match.group(1))
            metadata['turnover_threshold'] = int(crores * 10000000)  # Convert crores to rupees
            break
    
    # Extract sector tags using keyword matching
    # Priority order: Textile > Manufacturing > Technology > Trading
    sector_keywords = {
        'Textile': ['textile', 'garment', 'fabric', 'apparel', 'clothing', 'weaving', 'spinning'],
        'Manufacturing': ['manufacturing', 'production', 'factory', 'industrial', 'producer', 'manufacture'],
        'Technology': ['software', 'IT', 'technology', 'digital', 'computer', 'information technology'],
        'Trading': ['trading', 'commerce', 'merchant', 'dealer', 'wholesale', 'retail', 'trade']
    }
    
    # Check each sector in priority order
    for sector, keywords in sector_keywords.items():
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                metadata['sector_tag'] = sector
                break
        if metadata['sector_tag']:
            break
    
    # Extract effective dates
    # Patterns to match:
    # - "w.e.f. 01-04-2023"
    # - "with effect from 01-04-2023"
    # - "from 01/04/2023"
    # - "effective from 01-04-2023"
    date_patterns = [
        r'w\.e\.f\.\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'with\s+effect\s+from\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'effective\s+from\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'from\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            # Convert to ISO format: YYYY-MM-DD
            metadata['effective_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            break
    
    return metadata


def clean_pdf_text(text: str) -> str:
    """
    Clean extracted PDF text by removing repetitive headers/footers, page numbers, and excessive whitespace.
    
    This function handles common issues with government PDF layouts:
    - Repetitive headers and footers that appear on every page
    - Page numbers in various formats
    - Excessive whitespace (multiple spaces, blank lines)
    - Non-printable characters
    
    Args:
        text: Raw text extracted from PDF
    
    Returns:
        str: Cleaned text with headers/footers, page numbers, and excessive whitespace removed
    
    Examples:
        >>> text = "Header Text\\nPage 1\\nActual content\\nFooter Text\\n\\n\\nPage 2\\nMore content"
        >>> cleaned = clean_pdf_text(text)
        >>> "Actual content" in cleaned
        True
    """
    if not text or not text.strip():
        return ""
    
    lines = text.split('\n')
    
    # Step 1: Detect and remove repetitive headers/footers
    # Count frequency of each line to identify repetitive content
    line_frequency = {}
    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped) > 5:  # Only consider non-empty lines with meaningful content
            line_frequency[stripped] = line_frequency.get(stripped, 0) + 1
    
    # Identify repetitive lines (appear 3 or more times - likely headers/footers)
    repetitive_lines = {line for line, count in line_frequency.items() if count >= 3}
    
    # Step 2: Remove page numbers (various formats)
    # Common page number patterns:
    # - Standalone numbers: "1", "2", "123"
    # - With prefix: "Page 1", "Pg. 2"
    # - With separators: "- 1 -", "| 2 |"
    # - Roman numerals: "i", "ii", "iii", "iv", "v"
    page_number_pattern = re.compile(
        r'^\s*(?:'
        r'(?:page|pg\.?)\s*\d+|'  # "Page 1", "Pg. 2"
        r'\d+\s*$|'  # Standalone numbers at end of line
        r'[-|]\s*\d+\s*[-|]|'  # "- 1 -", "| 2 |"
        r'[ivxlcdm]+\s*$'  # Roman numerals
        r')\s*$',
        re.IGNORECASE
    )
    
    # Step 3: Filter lines
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines (we'll normalize whitespace later)
        if not stripped:
            continue
        
        # Skip repetitive headers/footers
        if stripped in repetitive_lines:
            continue
        
        # Skip page numbers
        if page_number_pattern.match(stripped):
            continue
        
        # Skip very short lines that are likely artifacts (but keep legal markers like "(a)", "(b)")
        if len(stripped) < 3 and not re.match(r'\([a-z0-9]+\)', stripped):
            continue
        
        cleaned_lines.append(line)
    
    # Step 4: Join lines and normalize whitespace
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Remove multiple consecutive spaces (but preserve single spaces)
    cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
    
    # Remove excessive blank lines (more than 2 consecutive newlines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # Remove non-printable characters (except newlines, tabs, and common punctuation)
    cleaned_text = re.sub(r'[^\x20-\x7E\n\t\u0900-\u097F]', '', cleaned_text)
    
    # Final trim
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text


@dataclass
class LegalChunk:
    """
    Structure-aware legal text chunk with comprehensive metadata.
    
    This dataclass represents a single chunk of legal text that has been extracted
    from a legal document with structure awareness. Each chunk preserves legal
    context through metadata including section numbers, turnover thresholds,
    sector tags, and effective dates.
    
    Attributes:
        text: The actual legal text content of the chunk
        law_type: Type of law (GST, Income Tax, Corporate Law, Subsidy Scheme, General)
        section_number: Section or rule identifier (e.g., "16", "5A", "12B")
        turnover_threshold: Business turnover threshold in rupees (e.g., 50000000 for 5 crore)
        sector_tag: Industry sector classification (Textile, Manufacturing, Technology, Trading)
        effective_date: Date when the provision becomes effective (ISO format: YYYY-MM-DD)
        chunk_type: Type of chunk - "main" (section/rule), "proviso" (proviso clause), 
                   or "sub_clause" (sub-clause like (a), (b), (c))
        source_file: Original PDF filename this chunk was extracted from
        file_hash: SHA256 hash of the source file for duplicate detection
    
    Usage:
        >>> chunk = LegalChunk(
        ...     text="Section 16 - Input Tax Credit...",
        ...     law_type="GST",
        ...     section_number="16",
        ...     turnover_threshold=50000000,
        ...     sector_tag="Manufacturing",
        ...     chunk_type="main"
        ... )
        >>> chunk.section_number
        '16'
        >>> chunk.turnover_threshold
        50000000
    
    Validates Requirements: 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5
    """
    text: str
    law_type: str
    section_number: Optional[str] = None
    turnover_threshold: Optional[float] = None
    sector_tag: Optional[str] = None
    effective_date: Optional[str] = None
    chunk_type: str = "main"  # main, proviso, sub_clause
    source_file: Optional[str] = None  # Original PDF filename
    file_hash: Optional[str] = None  # SHA256 hash of source file

class LegalTextSplitter:
    """
    CA-Logic Text Splitter for Legal Documents.
    
    This class implements structure-aware chunking of legal documents, preserving
    the hierarchical structure of sections, rules, provisos, and sub-clauses.
    It follows Chartered Accountant (CA) logic for legal interpretation, ensuring
    that legal context is maintained across chunks.
    
    Key Features:
        - Detects section and rule boundaries (e.g., "Section 16", "Rule 5")
        - Identifies proviso clauses ("Provided that", "Provided further that")
        - Recognizes sub-clauses ((a), (b), (c), etc.)
        - Extracts metadata (turnover thresholds, sector tags, effective dates)
        - Preserves legal hierarchy and context
    
    Pattern Matching:
        - SECTION_PATTERN: Matches "Section X" or "Section XA" patterns
        - RULE_PATTERN: Matches "Rule X" or "Rule XA" patterns
        - NOTIFICATION_PATTERN: Matches "Notification No." patterns
        - PROVISO_PATTERN: Matches proviso clauses
        - SUB_CLAUSE_PATTERN: Matches sub-clauses like (a), (b), (1), (2)
    
    Metadata Extraction:
        - TURNOVER_PATTERN: Extracts turnover thresholds in crores
        - SECTOR_PATTERNS: Identifies industry sectors (textile, manufacturing, etc.)
        - DATE_PATTERN: Extracts dates in DD-MM-YYYY or DD/MM/YYYY format
    
    Usage:
        >>> splitter = LegalTextSplitter()
        >>> chunks = splitter.split_legal_text(legal_text, law_type="GST")
        >>> for chunk in chunks:
        ...     print(f"Section {chunk.section_number}: {chunk.text[:50]}...")
    
    Validates Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    # Patterns that start a new chunk
    SECTION_PATTERN = re.compile(r'^Section\s+(\d+[A-Z]*)', re.MULTILINE | re.IGNORECASE)
    RULE_PATTERN = re.compile(r'^Rule\s+(\d+[A-Z]*)', re.MULTILINE | re.IGNORECASE)
    NOTIFICATION_PATTERN = re.compile(r'^Notification\s+No\.', re.MULTILINE | re.IGNORECASE)
    
    # Patterns that should append to previous chunk
    # Matches "Provided that" and "Provided further that" (and similar variations)
    PROVISO_PATTERN = re.compile(r'^\s*Provided\s+(?:further\s+)?that', re.MULTILINE | re.IGNORECASE)
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
        Split legal text into structure-aware chunks preserving legal hierarchy.
        
        This method analyzes legal text line-by-line to identify structural boundaries
        (sections, rules, notifications) and hierarchical elements (provisos, sub-clauses).
        It creates LegalChunk objects that preserve the legal context and metadata.
        
        Algorithm:
            1. Split text into lines for line-by-line analysis
            2. For each line, check if it starts a new section/rule/notification
            3. If yes, save the previous chunk and start a new one
            4. If it's a proviso or sub-clause, append to the current chunk
            5. Otherwise, add the line to the current chunk
            6. Extract metadata for each chunk (turnover, sector, dates)
        
        Args:
            text: Legal document text to split into chunks
            law_type: Type of law (GST, Income Tax, Corporate Law, etc.)
                     Used for context-specific metadata extraction
        
        Returns:
            List[LegalChunk]: List of legal chunks with metadata
                Each chunk contains:
                - text: The chunk content
                - law_type: Type of law
                - section_number: Section/rule identifier (if applicable)
                - chunk_type: "main", "proviso", or "sub_clause"
                - turnover_threshold: Extracted threshold in rupees (if applicable)
                - sector_tag: Industry sector (if applicable)
                - effective_date: ISO format date (if applicable)
        
        Examples:
            >>> splitter = LegalTextSplitter()
            >>> text = "Section 16 - Input Tax Credit\\n(1) Every registered person..."
            >>> chunks = splitter.split_legal_text(text, "GST")
            >>> chunks[0].section_number
            '16'
            >>> chunks[0].chunk_type
            'main'
        
        Validates Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
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
        """
        Create a LegalChunk with extracted metadata.
        
        This method now uses the enhanced extract_metadata_from_text() function
        to extract comprehensive metadata including turnover thresholds, sector tags,
        and effective dates. The extracted metadata is merged with existing metadata
        from the legacy patterns.
        
        Args:
            text: The chunk text content
            law_type: Type of law (GST, Income Tax, etc.)
            section_number: Section identifier if available
        
        Returns:
            LegalChunk: Chunk with comprehensive metadata
        
        Validates Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
        """
        chunk = LegalChunk(
            text=text,
            law_type=law_type,
            section_number=section_number
        )
        
        # Use enhanced metadata extraction function
        extracted_metadata = extract_metadata_from_text(text, law_type)
        
        # Merge extracted metadata with chunk
        # Priority: enhanced extraction > legacy patterns
        if extracted_metadata['turnover_threshold'] is not None:
            chunk.turnover_threshold = extracted_metadata['turnover_threshold']
        else:
            # Fallback to legacy pattern if enhanced extraction didn't find anything
            turnover_match = self.TURNOVER_PATTERN.search(text)
            if turnover_match:
                crores = float(turnover_match.group(1))
                chunk.turnover_threshold = crores * 10000000  # Convert to rupees
        
        if extracted_metadata['sector_tag'] is not None:
            chunk.sector_tag = extracted_metadata['sector_tag']
        else:
            # Fallback to legacy patterns if enhanced extraction didn't find anything
            for sector, pattern in self.SECTOR_PATTERNS.items():
                if pattern.search(text):
                    chunk.sector_tag = sector
                    break
        
        if extracted_metadata['effective_date'] is not None:
            chunk.effective_date = extracted_metadata['effective_date']
        else:
            # Fallback to legacy pattern if enhanced extraction didn't find anything
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
    """
    Process PDF and text documents to extract legal chunks with structure awareness.
    
    This class orchestrates the complete document processing pipeline:
    1. Auto-detects law type from filename
    2. Extracts text from PDF with page-by-page progress reporting
    3. Cleans extracted text (removes headers, footers, page numbers)
    4. Splits text into structure-aware chunks using LegalTextSplitter
    5. Extracts metadata for each chunk (turnover, sector, dates)
    
    Features:
        - Automatic law type detection from filename patterns
        - Robust PDF text extraction with error handling
        - Text cleaning to remove PDF artifacts
        - Structure-aware chunking preserving legal hierarchy
        - Comprehensive metadata extraction
        - Detailed progress reporting during processing
    
    Error Handling:
        - Handles missing files gracefully
        - Continues processing if individual pages fail
        - Logs warnings for empty content
        - Returns empty list on critical errors
    
    Usage:
        >>> processor = LegalDocumentProcessor()
        >>> chunks = processor.process_pdf("CGST_Act_2017.pdf")
        >>> print(f"Created {len(chunks)} chunks")
        >>> for chunk in chunks:
        ...     if chunk.turnover_threshold:
        ...         print(f"Section {chunk.section_number}: {chunk.turnover_threshold}")
    
    Validates Requirements: 3.1, 4.2, 4.4, 4.5, 5.1-5.5, 6.1-6.5, 9.2
    """
    
    def __init__(self):
        """
        Initialize the legal document processor.
        
        Creates an instance of LegalTextSplitter for structure-aware chunking.
        """
        self.splitter = LegalTextSplitter()
    
    def process_pdf(self, pdf_path: str, law_type: str = None) -> List[LegalChunk]:
        """
        Process a PDF file and return smart chunks with enhanced error handling.
        
        Args:
            pdf_path: Path to the PDF file to process
            law_type: Type of law (GST, Income Tax, etc.). If None, auto-detected from filename.
        
        Returns:
            List[LegalChunk]: List of processed legal chunks with metadata
        
        Features:
            - Auto-detects law type from filename if not provided
            - Applies text cleaning after extraction
            - Handles empty content with warning and skip
            - Handles extraction errors gracefully
            - Provides detailed progress reporting during extraction
        
        Validates Requirements: 3.1, 4.4, 4.5, 9.2
        """
        import logging
        import os
        
        # Configure logging if not already configured
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        
        try:
            from PyPDF2 import PdfReader
            
            # Auto-detect law type from filename if not provided
            if law_type is None:
                filename = os.path.basename(pdf_path)
                law_type = detect_law_type_from_filename(filename)
                logger.info(f"Auto-detected law type '{law_type}' from filename: {filename}")
            
            # Extract text from PDF with page-by-page progress reporting
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            logger.info(f"  Extracting text from {total_pages} pages...")
            
            full_text = ""
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    # Log progress for every page (Requirement 9.2)
                    logger.info(f"    Processing page {page_num}/{total_pages}")
                    
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                except Exception as page_error:
                    # Handle extraction errors for individual pages gracefully
                    logger.warning(f"    Error extracting text from page {page_num}/{total_pages}: {page_error}")
                    continue
            
            logger.info(f"  ✓ Text extraction complete ({total_pages} pages processed)")
            
            # Apply text cleaning after extraction
            logger.info(f"  Cleaning extracted text...")
            cleaned_text = clean_pdf_text(full_text)
            logger.info(f"  ✓ Text cleaning complete")
            
            # Handle empty content with warning and skip
            if not cleaned_text or not cleaned_text.strip():
                logger.warning(f"Empty content after extraction and cleaning for {pdf_path}, skipping document")
                return []
            
            # Split into legal chunks
            logger.info(f"  Chunking text with structure-aware splitting...")
            chunks = self.splitter.split_legal_text(cleaned_text, law_type)
            logger.info(f"  ✓ Created {len(chunks)} legal chunks")
            
            return chunks
        
        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            return []
        except Exception as e:
            # Handle extraction errors gracefully
            logger.error(f"Error processing PDF {pdf_path}: {type(e).__name__}: {e}")
            return []
    
    def process_text_file(self, text_path: str, law_type: str = "GST") -> List[LegalChunk]:
        """
        Process a plain text file and return structure-aware legal chunks.
        
        This method processes plain text files (as opposed to PDFs) containing
        legal content. It's useful for processing text files that have already
        been extracted from PDFs or for testing with sample legal text.
        
        Args:
            text_path: Path to the text file to process
            law_type: Type of law (GST, Income Tax, Corporate Law, etc.)
                     Defaults to "GST" if not specified
        
        Returns:
            List[LegalChunk]: List of processed legal chunks with metadata
                Returns empty list if file not found or processing fails
        
        Error Handling:
            - Returns empty list if file not found
            - Logs error message for any processing failures
            - Handles encoding issues gracefully
        
        Usage:
            >>> processor = LegalDocumentProcessor()
            >>> chunks = processor.process_text_file("sample_gst_text.txt", "GST")
            >>> print(f"Processed {len(chunks)} chunks from text file")
        
        Note:
            Unlike process_pdf(), this method does not apply text cleaning
            since text files are assumed to be pre-cleaned.
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

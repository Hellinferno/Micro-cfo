#!/usr/bin/env python3
"""
Phase 1: Scheme-Aware Ingestion for Government Subsidies
Processes government scheme documents with eligibility-focused chunking
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class SchemeChunk:
    """Smart chunk for government schemes with eligibility metadata"""
    text: str
    scheme_name: str
    law_type: str = "Subsidy Scheme"  # Type of law (GST, Income Tax, Corporate Law, Subsidy Scheme, General)
    section_number: Optional[str] = None  # Section or rule identifier for compatibility with LegalVectorDB
    target_sector: Optional[str] = None
    min_investment: Optional[float] = None
    max_investment: Optional[float] = None
    benefit_type: Optional[str] = None
    benefit_percentage: Optional[float] = None
    max_benefit_amount: Optional[float] = None
    location_restriction: Optional[str] = None
    chunk_type: str = "main"  # eligibility, objective, quantum, application
    effective_date: Optional[str] = None
    turnover_threshold: Optional[float] = None  # Business turnover threshold for compatibility
    sector_tag: Optional[str] = None  # Industry sector classification for compatibility
    source_file: Optional[str] = None  # Original source filename
    file_hash: Optional[str] = None  # SHA256 hash of source file

class SchemeSplitter:
    """Scheme-Aware Text Splitter for Government Subsidy Documents"""
    
    # Patterns that start a new chunk for schemes
    ELIGIBILITY_PATTERN = re.compile(r'^Eligibility\s*(?:Criteria|Conditions?|Requirements?)?', re.MULTILINE | re.IGNORECASE)
    OBJECTIVE_PATTERN = re.compile(r'^Objective\s*(?:of\s+the\s+Scheme)?', re.MULTILINE | re.IGNORECASE)
    QUANTUM_PATTERN = re.compile(r'^Quantum\s+of\s+Assistance', re.MULTILINE | re.IGNORECASE)
    APPLICATION_PATTERN = re.compile(r'^Application\s+Process', re.MULTILINE | re.IGNORECASE)
    SCHEME_NAME_PATTERN = re.compile(r'^(?:Scheme|Programme)\s*:?\s*(.+)', re.MULTILINE | re.IGNORECASE)
    
    # Metadata extraction patterns
    SECTOR_PATTERNS = {
        'textile': re.compile(r'\b(textile|fabric|garment|apparel|cotton|silk|jute|handloom|powerloom)\b', re.IGNORECASE),
        'manufacturing': re.compile(r'\b(manufacturing|factory|production|industrial|msme|sme)\b', re.IGNORECASE),
        'agriculture': re.compile(r'\b(agriculture|farming|agri|crop|livestock|dairy|fisheries)\b', re.IGNORECASE),
        'technology': re.compile(r'\b(software|technology|IT|information\s+technology|startup|innovation)\b', re.IGNORECASE),
        'food_processing': re.compile(r'\b(food\s+processing|fpo|pmfme|agro\s+processing)\b', re.IGNORECASE),
        'renewable_energy': re.compile(r'\b(solar|wind|renewable\s+energy|green\s+energy|biomass)\b', re.IGNORECASE),
    }
    
    # Investment amount patterns
    INVESTMENT_PATTERNS = [
        re.compile(r'investment\s+(?:above|exceeding|more\s+than|minimum\s+of)\s+(?:Rs\.?\s*)?(\d+(?:\.\d+)?)\s*(lakh|crore|thousand)?', re.IGNORECASE),
        re.compile(r'project\s+cost\s+(?:above|exceeding|more\s+than|minimum\s+of)\s+(?:Rs\.?\s*)?(\d+(?:\.\d+)?)\s*(lakh|crore|thousand)?', re.IGNORECASE),
        re.compile(r'capital\s+expenditure\s+(?:above|exceeding|more\s+than|minimum\s+of)\s+(?:Rs\.?\s*)?(\d+(?:\.\d+)?)\s*(lakh|crore|thousand)?', re.IGNORECASE),
    ]
    
    # Benefit patterns
    BENEFIT_PATTERNS = {
        'capital_subsidy': re.compile(r'capital\s+subsidy', re.IGNORECASE),
        'interest_subvention': re.compile(r'interest\s+(?:subvention|subsidy)', re.IGNORECASE),
        'tax_exemption': re.compile(r'tax\s+(?:exemption|benefit|incentive)', re.IGNORECASE),
        'credit_guarantee': re.compile(r'credit\s+guarantee', re.IGNORECASE),
        'grant': re.compile(r'\bgrant\b', re.IGNORECASE),
    }
    
    PERCENTAGE_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*%', re.IGNORECASE)
    AMOUNT_PATTERN = re.compile(r'(?:Rs\.?\s*|₹\s*)(\d+(?:,\d+)*(?:\.\d+)?)\s*(lakh|crore|thousand)?', re.IGNORECASE)
    
    def split_scheme_text(self, text: str, scheme_name: str = "Unknown Scheme") -> List[SchemeChunk]:
        """
        Split scheme text into smart chunks preserving eligibility structure
        """
        chunks = []
        current_chunk = []
        current_chunk_type = "main"
        
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a new section
            eligibility_match = self.ELIGIBILITY_PATTERN.match(line)
            objective_match = self.OBJECTIVE_PATTERN.match(line)
            quantum_match = self.QUANTUM_PATTERN.match(line)
            application_match = self.APPLICATION_PATTERN.match(line)
            
            if eligibility_match or objective_match or quantum_match or application_match:
                # Save previous chunk if exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append(self._create_scheme_chunk(chunk_text, scheme_name, current_chunk_type))
                
                # Start new chunk
                current_chunk = [line]
                if eligibility_match:
                    current_chunk_type = "eligibility"
                elif objective_match:
                    current_chunk_type = "objective"
                elif quantum_match:
                    current_chunk_type = "quantum"
                elif application_match:
                    current_chunk_type = "application"
            else:
                # Regular line - add to current chunk
                if current_chunk or line.strip():
                    current_chunk.append(line)
            
            i += 1
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(self._create_scheme_chunk(chunk_text, scheme_name, current_chunk_type))
        
        return chunks
    
    def _create_scheme_chunk(self, text: str, scheme_name: str, chunk_type: str) -> SchemeChunk:
        """Create a SchemeChunk with extracted metadata"""
        chunk = SchemeChunk(
            text=text,
            scheme_name=scheme_name,
            chunk_type=chunk_type
        )
        
        # Extract target sector
        for sector, pattern in self.SECTOR_PATTERNS.items():
            if pattern.search(text):
                chunk.target_sector = sector
                break
        
        # Extract investment thresholds
        for pattern in self.INVESTMENT_PATTERNS:
            match = pattern.search(text)
            if match:
                amount = float(match.group(1))
                unit = match.group(2).lower() if match.group(2) else 'rupees'
                
                # Convert to rupees
                if unit == 'thousand':
                    amount *= 1000
                elif unit == 'lakh':
                    amount *= 100000
                elif unit == 'crore':
                    amount *= 10000000
                
                chunk.min_investment = amount
                break
        
        # Extract benefit type
        for benefit_type, pattern in self.BENEFIT_PATTERNS.items():
            if pattern.search(text):
                chunk.benefit_type = benefit_type
                break
        
        # Extract benefit percentage
        percentage_match = self.PERCENTAGE_PATTERN.search(text)
        if percentage_match:
            chunk.benefit_percentage = float(percentage_match.group(1))
        
        # Extract maximum benefit amount
        amount_matches = self.AMOUNT_PATTERN.findall(text)
        if amount_matches:
            for amount_str, unit in amount_matches:
                try:
                    amount = float(amount_str.replace(',', ''))
                    unit = unit.lower() if unit else 'rupees'
                    
                    if unit == 'lakh':
                        amount *= 100000
                    elif unit == 'crore':
                        amount *= 10000000
                    elif unit == 'thousand':
                        amount *= 1000
                    
                    # Take the largest amount as max benefit
                    if not chunk.max_benefit_amount or amount > chunk.max_benefit_amount:
                        chunk.max_benefit_amount = amount
                except ValueError:
                    continue
        
        return chunk


class SchemeDocumentProcessor:
    """Process scheme documents and extract structured data"""
    
    def __init__(self):
        self.splitter = SchemeSplitter()
    
    def process_scheme_text(self, text: str, scheme_name: str = "Unknown Scheme") -> List[SchemeChunk]:
        """
        Process scheme text and return smart chunks
        """
        return self.splitter.split_scheme_text(text, scheme_name)
    
    def extract_scheme_metadata(self, text: str) -> Dict[str, any]:
        """
        Extract comprehensive metadata from scheme text
        """
        metadata = {
            'target_sector': None,
            'min_investment': None,
            'max_investment': None,
            'benefit_type': None,
            'benefit_percentage': None,
            'max_benefit_amount': None,
            'location_restriction': None
        }
        
        # Use the splitter's extraction logic
        temp_chunk = self.splitter._create_scheme_chunk(text, "temp", "main")
        
        metadata['target_sector'] = temp_chunk.target_sector
        metadata['min_investment'] = temp_chunk.min_investment
        metadata['benefit_type'] = temp_chunk.benefit_type
        metadata['benefit_percentage'] = temp_chunk.benefit_percentage
        metadata['max_benefit_amount'] = temp_chunk.max_benefit_amount
        
        return metadata


# Example usage and testing
if __name__ == "__main__":
    # Test with sample scheme text
    sample_scheme_text = """
Scheme: Production Linked Incentive (PLI) for Textiles

Objective
To promote manufacturing of Man-Made Fibre (MMF) apparel, MMF fabrics and 10 segments/products of technical textiles in the country.

Eligibility Criteria
1. The applicant should be a company incorporated in India
2. Minimum investment of Rs. 300 crore for MMF apparel and fabrics
3. Minimum investment of Rs. 100 crore for technical textiles
4. The company should achieve minimum turnover as prescribed

Quantum of Assistance
- Incentive @ 15% on incremental sales for MMF apparel and fabrics
- Incentive @ 11% on incremental sales for technical textiles
- Maximum incentive of Rs. 500 crore per company over 5 years
- Capital subsidy up to 25% of project cost

Application Process
Applications to be submitted online through the designated portal with all required documents and bank guarantee.
    """
    
    processor = SchemeDocumentProcessor()
    chunks = processor.process_scheme_text(sample_scheme_text, "PLI Textiles")
    
    print(f"Generated {len(chunks)} scheme chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i} ({chunk.chunk_type}):")
        print(f"  Scheme: {chunk.scheme_name}")
        print(f"  Sector: {chunk.target_sector}")
        print(f"  Min Investment: ₹{chunk.min_investment:,.0f}" if chunk.min_investment else "  Min Investment: None")
        print(f"  Benefit Type: {chunk.benefit_type}")
        print(f"  Benefit %: {chunk.benefit_percentage}%" if chunk.benefit_percentage else "  Benefit %: None")
        print(f"  Max Benefit: ₹{chunk.max_benefit_amount:,.0f}" if chunk.max_benefit_amount else "  Max Benefit: None")
        print(f"  Text Preview: {chunk.text[:100]}...")
        print()
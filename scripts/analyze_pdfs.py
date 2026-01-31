#!/usr/bin/env python3
"""
PDF Analysis Script - Compare two CFO project PDFs
"""

import PyPDF2
import sys
from pathlib import Path

def extract_pdf_text(pdf_path):
    """Extract all text from a PDF file"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num, page in enumerate(reader.pages):
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.extract_text()
        return text, len(reader.pages)

def analyze_pdfs():
    """Analyze and compare the two PDFs"""
    pdf1_path = Path("d:/CFO/CFO/Idea .pdf")
    pdf2_path = Path("d:/CFO/CFO/micro-cfo.pdf")
    
    print("="*80)
    print("PDF ANALYSIS: Micro-CFO Project Documentation")
    print("="*80)
    
    # Extract content from both PDFs
    print("\n1. Extracting PDF 1: Idea .pdf...")
    text1, pages1 = extract_pdf_text(pdf1_path)
    print(f"   - Pages: {pages1}")
    print(f"   - Characters: {len(text1)}")
    
    print("\n2. Extracting PDF 2: micro-cfo.pdf...")
    text2, pages2 = extract_pdf_text(pdf2_path)
    print(f"   - Pages: {pages2}")
    print(f"   - Characters: {len(text2)}")
    
    # Save extracted content
    output_dir = Path("d:/CFO/docs/pdf_analysis")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "idea_pdf_content.txt", "w", encoding="utf-8") as f:
        f.write(text1)
    
    with open(output_dir / "micro_cfo_pdf_content.txt", "w", encoding="utf-8") as f:
        f.write(text2)
    
    print(f"\n3. Content saved to: {output_dir}")
    
    # Basic content analysis
    print("\n" + "="*80)
    print("CONTENT PREVIEW - Idea .pdf")
    print("="*80)
    print(text1[:2000])
    
    print("\n" + "="*80)
    print("CONTENT PREVIEW - micro-cfo.pdf")
    print("="*80)
    print(text2[:2000])
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nFull content saved to:")
    print(f"  - {output_dir / 'idea_pdf_content.txt'}")
    print(f"  - {output_dir / 'micro_cfo_pdf_content.txt'}")

if __name__ == "__main__":
    try:
        analyze_pdfs()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""
Legal Document Ingestion Script
Ingests tax and legal PDFs into the vector database for Agent B (Legal Sentinel)
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from legal_ingestion import LegalDocumentProcessor, LegalChunk
from vector_database import LegalVectorDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Document configurations with their law types
DOCUMENT_CONFIGS = {
    # Tax Laws
    "Income-tax-Act-2025.pdf": {
        "law_type": "Income Tax",
        "description": "Income Tax Act 2025 - Updated tax legislation"
    },
    "GST-Acts-and-Rules-Bare-Law-11-04-2025.pdf": {
        "law_type": "GST",
        "description": "GST Acts and Rules Bare Law - April 2025 Edition"
    },
    "CGST_Act_2017.pdf": {
        "law_type": "GST",
        "description": "Central Goods and Services Tax Act 2017"
    },
    "IGST_Act_2017.pdf": {
        "law_type": "GST", 
        "description": "Integrated Goods and Services Tax Act 2017"
    },
    
    # Corporate Laws
    "Companies_Act_2013.pdf": {
        "law_type": "Corporate Law",
        "description": "Companies Act 2013"
    },
    "Companies Act 2013 as amended upto 01.04.2021_.pdf": {
        "law_type": "Corporate Law",
        "description": "Companies Act 2013 (Amended up to April 2021)"
    },
    "LLP_Act_PDF_Version_2_.pdf": {
        "law_type": "Corporate Law",
        "description": "Limited Liability Partnership Act"
    },
    "Partnership Act 1932_.pdf": {
        "law_type": "Corporate Law",
        "description": "Indian Partnership Act 1932"
    },
    "The competion Act_.pdf": {
        "law_type": "Corporate Law",
        "description": "The Competition Act - Antitrust legislation"
    },
    
    # Professional Acts
    "Cost_and_works_Accountants_Act_1959_.pdf": {
        "law_type": "Professional Law",
        "description": "Cost and Works Accountants Act 1959"
    },
    
    # Notifications (GST/Tax related)
    "NOT38578CF3B232A694DBEAB2A9CE71848DCA1.pdf": {
        "law_type": "GST",
        "description": "GST/Tax Notification"
    },
    "NOT3821EAEF90E037B4061A91775A5525510C3.pdf": {
        "law_type": "GST",
        "description": "GST/Tax Notification"
    },
    "380MD14012026DAD56B73DC944F02AEA4530EC779AD7F.pdf": {
        "law_type": "Income Tax",
        "description": "Income Tax Notification/Circular"
    },
    "381MD140120267212A1D4EF8349448E9416EF8F2D19B5.pdf": {
        "law_type": "Income Tax",
        "description": "Income Tax Notification/Circular"
    },
    "383MD14012026559E41DD96224880B75EDB2B96E4BD8B.pdf": {
        "law_type": "Income Tax",
        "description": "Income Tax Notification/Circular"
    },
    "384MD14012026E275757688DE4E68AF9813B3B9491E4B.pdf": {
        "law_type": "Income Tax",
        "description": "Income Tax Notification/Circular"
    }
}


def ingest_legal_documents(
    docs_dir: str = None,
    db_path: str = None,
    force_reingest: bool = False
) -> dict:
    """
    Ingest all legal documents from the specified directory into the vector database.
    
    Args:
        docs_dir: Directory containing legal PDFs (defaults to data/initial_acts)
        db_path: Path to the vector database (defaults to legal_db)
        force_reingest: If True, re-ingest even if documents already exist
        
    Returns:
        Dictionary with ingestion statistics
    """
    # Set defaults
    if docs_dir is None:
        docs_dir = project_root / "data" / "initial_acts"
    else:
        docs_dir = Path(docs_dir)
    
    if db_path is None:
        db_path = str(project_root / "legal_db")
    
    logger.info(f"📚 Legal Document Ingestion Starting")
    logger.info(f"   Documents directory: {docs_dir}")
    logger.info(f"   Vector database: {db_path}")
    
    # Initialize processor and database
    processor = LegalDocumentProcessor()
    vector_db = LegalVectorDB(db_path=db_path)
    
    stats = {
        "total_documents": 0,
        "documents_processed": 0,
        "documents_skipped": 0,
        "documents_failed": 0,
        "total_chunks": 0,
        "errors": []
    }
    
    # Find all PDF files
    pdf_files = list(docs_dir.glob("*.pdf"))
    stats["total_documents"] = len(pdf_files)
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {docs_dir}")
        return stats
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    for pdf_path in pdf_files:
        filename = pdf_path.name
        
        # Get configuration for this document
        config = DOCUMENT_CONFIGS.get(filename, {})
        law_type = config.get("law_type")
        description = config.get("description", filename)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📄 Processing: {filename}")
        logger.info(f"   Type: {law_type or 'Auto-detect'}")
        logger.info(f"   Description: {description}")
        
        try:
            # Process the PDF
            chunks = processor.process_pdf(str(pdf_path), law_type=law_type)
            
            if not chunks:
                logger.warning(f"   ⚠️  No chunks extracted from {filename}")
                stats["documents_skipped"] += 1
                continue
            
            logger.info(f"   ✅ Extracted {len(chunks)} chunks")
            
            # Add chunks to vector database
            vector_db.add_chunks(chunks)
            
            stats["documents_processed"] += 1
            stats["total_chunks"] += len(chunks)
            
            logger.info(f"   ✅ Added to vector database")
            
        except Exception as e:
            logger.error(f"   ❌ Error processing {filename}: {str(e)}")
            stats["documents_failed"] += 1
            stats["errors"].append({
                "file": filename,
                "error": str(e)
            })
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 INGESTION SUMMARY")
    logger.info(f"   Total documents: {stats['total_documents']}")
    logger.info(f"   Successfully processed: {stats['documents_processed']}")
    logger.info(f"   Skipped (empty): {stats['documents_skipped']}")
    logger.info(f"   Failed: {stats['documents_failed']}")
    logger.info(f"   Total chunks created: {stats['total_chunks']}")
    
    if stats["errors"]:
        logger.warning(f"\n⚠️  Errors encountered:")
        for error in stats["errors"]:
            logger.warning(f"   - {error['file']}: {error['error']}")
    
    # Get database stats
    try:
        db_stats = vector_db.get_stats()
        logger.info(f"\n📈 Database Statistics:")
        logger.info(f"   Total chunks in DB: {db_stats.get('total_chunks', 'N/A')}")
        logger.info(f"   Law types: {db_stats.get('law_types', 'N/A')}")
    except Exception as e:
        logger.warning(f"Could not retrieve DB stats: {e}")
    
    return stats


def verify_ingestion(db_path: str = None) -> bool:
    """
    Verify that documents have been properly ingested.
    
    Args:
        db_path: Path to the vector database
        
    Returns:
        True if verification passes, False otherwise
    """
    if db_path is None:
        db_path = str(project_root / "legal_db")
    
    logger.info(f"🔍 Verifying ingestion...")
    
    try:
        vector_db = LegalVectorDB(db_path=db_path)
        
        # Test queries for different law types
        test_queries = [
            ("GST input tax credit", "GST"),
            ("income tax deduction section 80C", "Income Tax"),
            ("company director liability", "Corporate Law")
        ]
        
        passed = 0
        for query, expected_type in test_queries:
            results = vector_db.hybrid_search(
                query=query,
                n_results=3,
                law_type=expected_type
            )
            
            if results:
                logger.info(f"   ✅ '{query}' - Found {len(results)} results")
                passed += 1
            else:
                logger.warning(f"   ⚠️  '{query}' - No results found")
        
        logger.info(f"\n   Verification: {passed}/{len(test_queries)} queries returned results")
        return passed >= len(test_queries) // 2
        
    except Exception as e:
        logger.error(f"   ❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest legal documents into vector database")
    parser.add_argument("--docs-dir", type=str, help="Directory containing PDF documents")
    parser.add_argument("--db-path", type=str, help="Path to vector database")
    parser.add_argument("--force", action="store_true", help="Force re-ingestion of all documents")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing ingestion")
    
    args = parser.parse_args()
    
    if args.verify_only:
        success = verify_ingestion(db_path=args.db_path)
        sys.exit(0 if success else 1)
    
    # Run ingestion
    stats = ingest_legal_documents(
        docs_dir=args.docs_dir,
        db_path=args.db_path,
        force_reingest=args.force
    )
    
    # Run verification
    verify_ingestion(db_path=args.db_path)
    
    # Exit with error if any documents failed
    if stats["documents_failed"] > 0:
        sys.exit(1)

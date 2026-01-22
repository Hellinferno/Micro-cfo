"""
Legal Data Seed Processor

This module orchestrates the end-to-end pipeline from downloaded PDFs to
populated vector database. It processes legal documents with structure-aware
chunking and stores them with embeddings for semantic search.

Key Features:
- Idempotent processing (skip already-processed documents)
- Progress tracking and reporting
- Comprehensive error handling
- Detailed processing statistics
"""

import os
import sys
import time
import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add parent directory to path to import legal_ingestion and vector_database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from legal_ingestion import LegalDocumentProcessor
from vector_database import LegalVectorDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DocumentReport:
    """
    Report for a single document processing operation.
    
    Attributes:
        filename: Name of the processed file
        law_type: Detected or assigned law type
        chunks_created: Number of legal chunks created from the document
        processing_time: Time taken to process the document (seconds)
        success: Whether processing completed successfully
        error_message: Error message if processing failed
    """
    filename: str
    law_type: str
    chunks_created: int
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    
    def __str__(self) -> str:
        """Format report as human-readable string."""
        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        result = f"{status} | {self.filename} | {self.law_type}"
        
        if self.success:
            result += f" | {self.chunks_created} chunks | {self.processing_time:.2f}s"
        else:
            result += f" | Error: {self.error_message}"
        
        return result


@dataclass
class ProcessingReport:
    """
    Overall processing report for batch operations.
    
    Attributes:
        total_documents: Total number of documents attempted
        successful_documents: Number of successfully processed documents
        failed_documents: Number of failed documents
        total_chunks_created: Total chunks created across all documents
        total_processing_time: Total time spent processing (seconds)
        document_reports: Individual reports for each document
    """
    total_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    total_chunks_created: int = 0
    total_processing_time: float = 0.0
    document_reports: List[DocumentReport] = field(default_factory=list)
    
    def add_document_report(self, report: DocumentReport) -> None:
        """
        Add a document report and update aggregate statistics.
        
        Args:
            report: Document report to add
        """
        self.document_reports.append(report)
        self.total_documents += 1
        self.total_processing_time += report.processing_time
        
        if report.success:
            self.successful_documents += 1
            self.total_chunks_created += report.chunks_created
        else:
            self.failed_documents += 1
    
    def __str__(self) -> str:
        """Format report as human-readable string."""
        lines = [
            "=" * 80,
            "LEGAL DATA SEEDING REPORT",
            "=" * 80,
            "",
            "Summary:",
            f"  Total Documents:     {self.total_documents}",
            f"  Successful:          {self.successful_documents}",
            f"  Failed:              {self.failed_documents}",
            f"  Total Chunks:        {self.total_chunks_created}",
            f"  Total Time:          {self.total_processing_time:.2f}s",
            "",
            "Document Details:",
            "-" * 80,
        ]
        
        for report in self.document_reports:
            lines.append(f"  {report}")
        
        lines.extend([
            "-" * 80,
            f"Report generated at: {datetime.now().isoformat()}",
            "=" * 80,
        ])
        
        return "\n".join(lines)


@dataclass
class ProcessingMetadata:
    """
    Metadata tracked during processing for idempotency.
    
    This metadata is stored in the vector database to detect duplicate
    processing attempts and enable safe re-execution of the seeding pipeline.
    
    Attributes:
        file_path: Path to the processed file
        file_hash: SHA256 hash of file content for duplicate detection
        processing_timestamp: ISO format timestamp of processing
        chunks_created: Number of chunks created from this document
        law_type: Detected law type
    """
    file_path: str
    file_hash: str
    processing_timestamp: str
    chunks_created: int
    law_type: str
    
    def to_dict(self) -> Dict[str, any]:
        """
        Convert metadata to dictionary for storage.
        
        Returns:
            Dict: Dictionary representation of metadata
        """
        return {
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'processing_timestamp': self.processing_timestamp,
            'chunks_created': self.chunks_created,
            'law_type': self.law_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'ProcessingMetadata':
        """
        Create metadata instance from dictionary.
        
        Args:
            data: Dictionary containing metadata fields
            
        Returns:
            ProcessingMetadata: New instance
        """
        return cls(
            file_path=data['file_path'],
            file_hash=data['file_hash'],
            processing_timestamp=data['processing_timestamp'],
            chunks_created=data['chunks_created'],
            law_type=data['law_type']
        )
    
    def save_to_db(self, db: LegalVectorDB) -> None:
        """
        Save metadata to vector database for duplicate detection.
        
        Args:
            db: LegalVectorDB instance to save to
            
        Validates Requirement: 8.5
        """
        db.save_processing_metadata(self.to_dict())
    
    @classmethod
    def load_from_db(cls, db: LegalVectorDB, file_path: str) -> Optional['ProcessingMetadata']:
        """
        Load metadata from vector database.
        
        Args:
            db: LegalVectorDB instance to load from
            file_path: Path to the file to check
            
        Returns:
            ProcessingMetadata instance if found, None otherwise
            
        Validates Requirement: 8.5
        """
        metadata_dict = db.load_processing_metadata(file_path)
        
        if metadata_dict is None:
            return None
        
        return cls.from_dict(metadata_dict)


class ProgressTracker:
    """
    Track and display processing progress.
    
    Provides user-friendly progress updates during long-running operations.
    """
    
    def __init__(self, total_items: int, operation_name: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            total_items: Total number of items to process
            operation_name: Name of the operation being tracked
        """
        self.total_items = total_items
        self.current_item = 0
        self.operation_name = operation_name
        self.start_time = time.time()
    
    def update(self, current: int, message: str = "") -> None:
        """
        Update progress and display message.
        
        Args:
            current: Current item number (1-indexed)
            message: Optional message to display
        """
        self.current_item = current
        percentage = (current / self.total_items) * 100 if self.total_items > 0 else 0
        elapsed = time.time() - self.start_time
        
        progress_msg = f"[{current}/{self.total_items}] ({percentage:.1f}%) {self.operation_name}"
        if message:
            progress_msg += f": {message}"
        
        logger.info(progress_msg)
    
    def complete(self, summary: str = "") -> None:
        """
        Mark processing as complete and display summary.
        
        Args:
            summary: Optional summary message
        """
        elapsed = time.time() - self.start_time
        completion_msg = f"{self.operation_name} complete in {elapsed:.2f}s"
        if summary:
            completion_msg += f" - {summary}"
        
        logger.info(completion_msg)


class SeedDataProcessor:
    """
    Orchestrates PDF processing and database population.
    
    This class manages the complete pipeline from downloaded PDFs to
    populated vector database, including:
    - Document processing with legal ingestion pipeline
    - Duplicate detection and idempotent operations
    - Progress tracking and reporting
    - Error handling and recovery
    """
    
    def __init__(
        self,
        data_dir: str = "./data/initial_acts/",
        db_path: str = "./legal_db/"
    ):
        """
        Initialize processor with data and database paths.
        
        Args:
            data_dir: Directory containing downloaded PDF files
            db_path: Path to vector database storage
            
        Raises:
            RuntimeError: If database initialization fails
            ImportError: If required modules cannot be imported
            
        Validates Requirement: 10.3
        """
        self.data_dir = data_dir
        self.db_path = db_path
        
        logger.info(f"SeedDataProcessor initializing...")
        logger.info(f"  Data directory: {data_dir}")
        logger.info(f"  Database path: {db_path}")
        
        # Initialize Legal Document Processor
        try:
            logger.info("Initializing Legal Document Processor...")
            self.legal_processor = LegalDocumentProcessor()
            logger.info("✓ Legal Document Processor initialized successfully")
        except ImportError as e:
            error_msg = f"Failed to import LegalDocumentProcessor: {e}"
            logger.error(error_msg)
            logger.error("Please ensure legal_ingestion.py is available in the parent directory")
            raise ImportError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize LegalDocumentProcessor: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        
        # Initialize Vector Database
        try:
            logger.info("Initializing Vector Database...")
            logger.info("  This may take a moment as the embedding model loads...")
            self.vector_db = LegalVectorDB(db_path=db_path)
            logger.info("✓ Vector Database initialized successfully")
        except ImportError as e:
            error_msg = f"Failed to import LegalVectorDB: {e}"
            logger.error(error_msg)
            logger.error("Please ensure vector_database.py is available in the parent directory")
            raise ImportError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize Vector Database at '{db_path}': {e}"
            logger.error(error_msg)
            logger.error("Common causes:")
            logger.error("  - ChromaDB not installed (pip install chromadb)")
            logger.error("  - Sentence transformers not installed (pip install sentence-transformers)")
            logger.error("  - Insufficient disk space or permissions")
            logger.error("  - Corrupted database files (try deleting the legal_db directory)")
            raise RuntimeError(error_msg) from e
        
        logger.info("✓ SeedDataProcessor initialization complete")
    
    def _get_file_hash(self, pdf_path: str) -> str:
        """
        Generate SHA256 hash of file for duplicate detection.
        
        This hash is used to detect if a file has been modified since it was
        last processed. By comparing hashes, we can implement idempotent
        processing - only reprocessing files that have actually changed.
        
        The file is read in 4KB chunks to efficiently handle large PDF files
        without loading the entire file into memory.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            str: Hexadecimal hash string (64 characters for SHA256)
        """
        sha256_hash = hashlib.sha256()
        
        with open(pdf_path, "rb") as f:
            # Read file in 4KB chunks to handle large files efficiently
            # iter(lambda: f.read(4096), b"") creates an iterator that reads
            # 4096 bytes at a time until it reaches the end (empty bytes b"")
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        # Return hexadecimal representation of the hash
        return sha256_hash.hexdigest()
    
    def _is_already_processed(self, pdf_path: str) -> bool:
        """
        Check if document has already been ingested using hash-based duplicate detection.
        
        This method implements idempotent processing by:
        1. Calculating the current file's SHA256 hash
        2. Looking up processing metadata from the database
        3. Comparing the stored hash with the current hash
        
        If the hashes match, the file hasn't changed and we skip reprocessing.
        If the hashes differ, the file was modified and needs reprocessing.
        If no metadata exists, the file hasn't been processed yet.
        
        This allows safe re-execution of the seeding pipeline without creating
        duplicate chunks in the database.
        
        Args:
            pdf_path: Path to PDF file to check
            
        Returns:
            bool: True if already processed with same hash, False otherwise
            
        Validates Requirements: 8.2, 8.5
        """
        try:
            # Step 1: Calculate current file hash for comparison
            current_hash = self._get_file_hash(pdf_path)
            
            # Step 2: Try to load processing metadata from database
            # This metadata was stored during previous processing runs
            metadata = ProcessingMetadata.load_from_db(self.vector_db, pdf_path)
            
            # Step 3: Check if metadata exists
            if metadata is None:
                # No metadata found - document hasn't been processed before
                logger.debug(f"No processing metadata found for {pdf_path}")
                return False
            
            # Step 4: Compare file hashes to detect changes
            if metadata.file_hash == current_hash:
                # Hashes match - file unchanged since last processing
                # Safe to skip reprocessing (idempotency)
                logger.info(f"Document {pdf_path} already processed with matching hash")
                logger.info(f"  Processed at: {metadata.processing_timestamp}")
                logger.info(f"  Chunks created: {metadata.chunks_created}")
                logger.info(f"  Law type: {metadata.law_type}")
                return True
            
            # Step 5: Hashes differ - file has been modified
            # Need to reprocess to capture the changes
            logger.info(f"Document {pdf_path} found but hash differs - will reprocess")
            logger.info(f"  Old hash: {metadata.file_hash[:16]}...")  # Show first 16 chars
            logger.info(f"  New hash: {current_hash[:16]}...")
            return False
            logger.info(f"Document {pdf_path} found but hash differs - will reprocess")
            logger.info(f"  Old hash: {metadata.file_hash[:16]}...")
            logger.info(f"  New hash: {current_hash[:16]}...")
            return False
            
        except Exception as e:
            # If there's an error checking, assume not processed to be safe
            logger.warning(f"Error checking if {pdf_path} already processed: {e}")
            return False
    
    def _store_chunks_with_progress(self, chunks: List) -> None:
        """
        Store chunks in vector database with detailed progress reporting.
        
        This method provides percentage-based progress updates during the storage
        operation, which can be time-consuming for large documents due to embedding
        generation.
        
        Args:
            chunks: List of LegalChunk objects to store
            
        Validates Requirement: 9.4
        """
        if not chunks:
            return
        
        total_chunks = len(chunks)
        
        # For small numbers of chunks, store all at once
        if total_chunks <= 10:
            logger.info(f"    Storing {total_chunks} chunks...")
            self.vector_db.add_chunks(chunks)
            logger.info(f"    ✓ Storage complete (100%)")
            return
        
        # For larger numbers, store in batches with progress reporting
        batch_size = max(1, total_chunks // 10)  # Aim for ~10 progress updates
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            batch_end = min(i + batch_size, total_chunks)
            
            # Calculate and log progress percentage
            progress_pct = (batch_end / total_chunks) * 100
            logger.info(f"    Storing chunks {i+1}-{batch_end}/{total_chunks} ({progress_pct:.1f}%)")
            
            # Store batch
            self.vector_db.add_chunks(batch)
        
        logger.info(f"    ✓ Storage complete (100%)")
    
    def process_single_document(self, pdf_path: str) -> DocumentReport:
        """
        Process a single PDF and return statistics.
        
        This method orchestrates the complete processing pipeline:
        1. Check if file exists
        2. Check if document already processed (idempotency)
        3. Detect law type from filename
        4. Process PDF with legal ingestion pipeline
        5. Generate embeddings and store in vector database
        6. Store processing metadata for duplicate detection
        
        Args:
            pdf_path: Path to PDF file to process
            
        Returns:
            DocumentReport: Processing statistics and status
            
        Validates Requirements: 7.1, 7.2, 7.3, 7.4, 8.2
        """
        filename = os.path.basename(pdf_path)
        start_time = time.time()
        
        logger.info(f"Processing: {filename}")
        
        try:
            # Check if file exists first
            if not os.path.exists(pdf_path):
                error_msg = f"File not found: {pdf_path}"
                logger.error(f"  ✗ {error_msg}")
                return DocumentReport(
                    filename=filename,
                    law_type="Unknown",
                    chunks_created=0,
                    processing_time=time.time() - start_time,
                    success=False,
                    error_message=error_msg
                )
            
            # Check if already processed (idempotency)
            if self._is_already_processed(pdf_path):
                logger.info(f"Skipping {filename} - already processed")
                return DocumentReport(
                    filename=filename,
                    law_type="Skipped",
                    chunks_created=0,
                    processing_time=time.time() - start_time,
                    success=True,
                    error_message=None
                )
            
            # Import detect_law_type_from_filename from legal_ingestion
            from legal_ingestion import detect_law_type_from_filename
            
            # Detect law type from filename
            law_type = detect_law_type_from_filename(filename)
            logger.info(f"  Detected law type: {law_type}")
            
            # Process PDF using legal ingestion pipeline
            logger.info(f"  Processing PDF with legal ingestion pipeline...")
            chunks = self.legal_processor.process_pdf(pdf_path, law_type)
            
            # Handle empty chunks
            if not chunks or len(chunks) == 0:
                logger.warning(f"  No chunks created from {filename} - empty or invalid PDF")
                return DocumentReport(
                    filename=filename,
                    law_type=law_type,
                    chunks_created=0,
                    processing_time=time.time() - start_time,
                    success=False,
                    error_message="No chunks created - empty or invalid PDF"
                )
            
            logger.info(f"  ✓ Created {len(chunks)} chunks")
            
            # Generate embeddings and store in vector database with progress reporting
            logger.info(f"  Storing chunks in vector database...")
            self._store_chunks_with_progress(chunks)
            logger.info(f"  ✓ Successfully stored {len(chunks)} chunks")
            
            # Create and store processing metadata for idempotency
            file_hash = self._get_file_hash(pdf_path)
            metadata = ProcessingMetadata(
                file_path=pdf_path,
                file_hash=file_hash,
                processing_timestamp=datetime.now().isoformat(),
                chunks_created=len(chunks),
                law_type=law_type
            )
            metadata.save_to_db(self.vector_db)
            logger.info(f"  ✓ Saved processing metadata")
            
            # Return success report
            processing_time = time.time() - start_time
            logger.info(f"  ✓ Completed in {processing_time:.2f}s")
            
            return DocumentReport(
                filename=filename,
                law_type=law_type,
                chunks_created=len(chunks),
                processing_time=processing_time,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            logger.error(f"  ✗ {error_msg}")
            logger.exception("Full traceback:")
            return DocumentReport(
                filename=filename,
                law_type="Unknown",
                chunks_created=0,
                processing_time=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
    
    def process_all_documents(self) -> ProcessingReport:
        """
        Process all PDFs in data directory and populate database.
        
        This method orchestrates batch processing of all legal documents:
        1. Scans data directory for PDF files
        2. Processes each document using process_single_document()
        3. Tracks progress with ProgressTracker
        4. Aggregates statistics in ProcessingReport
        
        Returns:
            ProcessingReport: Overall processing statistics
            
        Validates Requirements: 7.5, 8.4
        """
        report = ProcessingReport()
        
        logger.info("Starting batch document processing")
        logger.info(f"Scanning directory: {self.data_dir}")
        
        # Find all PDF files
        pdf_files = list(Path(self.data_dir).glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        if not pdf_files:
            logger.warning("No PDF files found to process")
            return report
        
        # Process each document
        tracker = ProgressTracker(len(pdf_files), "Document Processing")
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            tracker.update(idx, pdf_path.name)
            doc_report = self.process_single_document(str(pdf_path))
            report.add_document_report(doc_report)
        
        tracker.complete(f"{report.successful_documents} successful, {report.failed_documents} failed")
        
        return report
    
    def generate_report(self, report: ProcessingReport) -> str:
        """
        Generate human-readable processing report.
        
        Args:
            report: Processing report to format
            
        Returns:
            str: Formatted report string
        """
        return str(report)


def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Process legal documents and populate vector database'
    )
    parser.add_argument(
        '--data-dir',
        default='./data/initial_acts/',
        help='Directory containing PDF files (default: ./data/initial_acts/)'
    )
    parser.add_argument(
        '--db-path',
        default='./legal_db/',
        help='Path to vector database (default: ./legal_db/)'
    )
    
    args = parser.parse_args()
    
    # Create processor and process all documents
    processor = SeedDataProcessor(
        data_dir=args.data_dir,
        db_path=args.db_path
    )
    
    report = processor.process_all_documents()
    
    # Display report
    print("\n" + processor.generate_report(report))
    
    # Exit with error code if any processing failed
    if report.failed_documents > 0:
        exit(1)


if __name__ == '__main__':
    main()

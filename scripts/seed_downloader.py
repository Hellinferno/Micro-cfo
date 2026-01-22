"""
Legal Document Seed Downloader

This module handles downloading foundational legal documents from official
government sources. It includes robust error handling for SSL certificate issues,
network timeouts, and HTTP errors.

Key Features:
- Automatic download from configured government sources
- Idempotent operations (skip existing files)
- SSL error recovery with fallback
- Network timeout handling with exponential backoff
- Comprehensive logging and progress reporting
"""

import os
import time
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
import requests
from requests.exceptions import SSLError, Timeout, RequestException


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LegalDocumentSource:
    """
    Represents a legal document source with download metadata.
    
    Attributes:
        url: Download URL for the legal document
        filename: Local filename to save the document as
        description: Human-readable description of the document
        law_type: Expected law type for validation (GST, Income Tax, etc.)
    """
    url: str
    filename: str
    description: str
    law_type: str
    
    def validate_url(self) -> bool:
        """
        Validate URL format and basic structure.
        
        Returns:
            bool: True if URL appears valid, False otherwise
        """
        return self.url.startswith('http://') or self.url.startswith('https://')
    
    def get_local_path(self, base_dir: str) -> Path:
        """
        Get full local path for downloaded file.
        
        Args:
            base_dir: Base directory for downloads
            
        Returns:
            Path: Full path where file should be saved
        """
        return Path(base_dir) / self.filename


# Configuration: Legal document sources to download
LEGAL_SOURCES = [
    LegalDocumentSource(
        url="https://cbic-gst.gov.in/pdf/cgst-act.pdf",
        filename="CGST_Act_2017.pdf",
        description="Central Goods and Services Tax Act 2017",
        law_type="GST"
    ),
    LegalDocumentSource(
        url="https://cbic-gst.gov.in/pdf/igst-act.pdf",
        filename="IGST_Act_2017.pdf",
        description="Integrated Goods and Services Tax Act 2017",
        law_type="GST"
    ),
    LegalDocumentSource(
        url="https://incometaxindia.gov.in/pages/acts/income-tax-act.pdf",
        filename="Income_Tax_Act_1961.pdf",
        description="Income Tax Act 1961",
        law_type="Income Tax"
    ),
    LegalDocumentSource(
        url="https://www.indiacode.nic.in/bitstream/123456789/2114/1/A2013-18.pdf",
        filename="Companies_Act_2013.pdf",
        description="Companies Act 2013",
        law_type="Corporate Law"
    ),
    LegalDocumentSource(
        url="https://texprocil.org/pli-scheme-guidelines.pdf",
        filename="PLI_Textiles_Guidelines.pdf",
        description="Production Linked Incentive Scheme for Textiles",
        law_type="Subsidy Scheme"
    )
]


class SeedDownloader:
    """
    Handles downloading of legal documents from government sources.
    
    Features:
    - Idempotent downloads (skip existing files)
    - SSL error recovery
    - Network timeout handling with exponential backoff
    - Comprehensive error logging
    """
    
    def __init__(self, output_dir: str = "./data/initial_acts/"):
        """
        Initialize downloader with output directory.
        
        Args:
            output_dir: Directory to save downloaded files
            
        Raises:
            OSError: If directory creation fails
        """
        self.output_dir = output_dir
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """
        Create output directory if it doesn't exist.
        
        Raises:
            OSError: If directory creation fails
        """
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Output directory ready: {self.output_dir}")
        except OSError as e:
            logger.error(f"Failed to create directory {self.output_dir}: {str(e)}")
            raise
    
    def download_document(self, source: LegalDocumentSource) -> bool:
        """
        Download a single document with retry logic.
        
        Args:
            source: Legal document source to download
            
        Returns:
            bool: True if download successful, False otherwise
        """
        local_path = source.get_local_path(self.output_dir)
        
        # Check if file already exists (idempotency)
        if local_path.exists():
            logger.info(f"File already exists, skipping: {source.filename}")
            return True
        
        # Validate URL
        if not source.validate_url():
            logger.error(f"Invalid URL format: {source.url}")
            return False
        
        logger.info(f"Downloading: {source.description}")
        logger.info(f"URL: {source.url}")
        
        try:
            # Attempt download with retry logic
            response = self._retry_with_backoff(
                lambda: self._download_with_ssl_fallback(source.url)
            )
            
            if response is None:
                return False
            
            # Save file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            file_size = local_path.stat().st_size
            logger.info(f"Successfully downloaded: {source.filename} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {source.filename}: {str(e)}")
            return False
    
    def _download_with_ssl_fallback(self, url: str) -> requests.Response:
        """
        Download with SSL error recovery.
        
        Government websites often have SSL certificate issues (expired, self-signed,
        or misconfigured certificates). This method attempts a secure download first,
        then falls back to an insecure connection if SSL verification fails.
        
        Args:
            url: URL to download from
            
        Returns:
            requests.Response: Response object
            
        Raises:
            RequestException: If download fails after SSL fallback
        """
        try:
            # First attempt: Secure download with SSL verification enabled
            # This is the preferred method for security
            response = requests.get(url, timeout=30, verify=True)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
            return response
        except SSLError:
            # SSL verification failed - common with government websites
            # Retry without SSL verification as a fallback
            # Note: This is less secure but necessary for accessing government PDFs
            logger.warning(f"SSL verification failed for {url}, retrying without verification")
            response = requests.get(url, timeout=30, verify=False)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
            return response
    
    def _retry_with_backoff(
        self, 
        func: Callable[[], requests.Response], 
        max_retries: int = 3
    ) -> Optional[requests.Response]:
        """
        Execute function with exponential backoff retry logic.
        
        This implements a robust retry strategy for handling transient network failures:
        - Attempt 1: Immediate execution
        - Attempt 2: Wait 1 second (2^0), then retry
        - Attempt 3: Wait 2 seconds (2^1), then retry
        - Attempt 4: Wait 4 seconds (2^2), then retry
        
        The exponential backoff prevents overwhelming the server and gives time
        for transient issues (network congestion, server load) to resolve.
        
        Args:
            func: Function to execute (should return requests.Response)
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Optional[requests.Response]: Response if successful, None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                # Attempt to execute the function
                return func()
            except Timeout:
                # Network timeout occurred - server didn't respond in time
                if attempt < max_retries - 1:
                    # Calculate exponential backoff: 2^attempt seconds
                    # attempt=0 → 1s, attempt=1 → 2s, attempt=2 → 4s
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Timeout on attempt {attempt + 1}/{max_retries}, "
                        f"retrying in {wait_time}s"
                    )
                    time.sleep(wait_time)  # Wait before retrying
                else:
                    # All retries exhausted - give up
                    logger.error(f"Failed after {max_retries} timeout attempts")
                    return None
            except RequestException as e:
                # Other network error (connection refused, DNS failure, etc.)
                logger.error(f"Request failed on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    # Wait with exponential backoff before retrying
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    # All retries exhausted - give up
                    return None
        
        # Should never reach here, but return None as safety fallback
        return None
    
    def download_all(self, sources: List[LegalDocumentSource]) -> Dict[str, bool]:
        """
        Download all documents and return success status.
        
        Args:
            sources: List of legal document sources to download
            
        Returns:
            Dict[str, bool]: Mapping of filename to success status
        """
        results = {}
        successful = 0
        failed = 0
        
        logger.info(f"Starting download of {len(sources)} documents")
        
        for source in sources:
            success = self.download_document(source)
            results[source.filename] = success
            
            if success:
                successful += 1
            else:
                failed += 1
        
        # Summary report
        logger.info("=" * 60)
        logger.info("Download Summary:")
        logger.info(f"  Total documents: {len(sources)}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info("=" * 60)
        
        return results


def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download foundational legal documents from government sources'
    )
    parser.add_argument(
        '--output-dir',
        default='./data/initial_acts/',
        help='Directory to save downloaded files (default: ./data/initial_acts/)'
    )
    
    args = parser.parse_args()
    
    # Create downloader and download all configured sources
    downloader = SeedDownloader(output_dir=args.output_dir)
    results = downloader.download_all(LEGAL_SOURCES)
    
    # Exit with error code if any downloads failed
    if not all(results.values()):
        exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Unified Storage Manager for MicroCFO
Handles both S3 and local filesystem storage with automatic fallback
"""

import logging
import os
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
from datetime import datetime
import tempfile

from s3_storage import get_s3_manager, is_s3_enabled

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Unified storage manager that handles both S3 and local filesystem
    Automatically uses S3 if configured, falls back to local storage
    """
    
    def __init__(self):
        """Initialize storage manager"""
        self.use_s3 = is_s3_enabled()
        
        if self.use_s3:
            try:
                self.s3_manager = get_s3_manager()
                logger.info("✅ Storage manager initialized with S3")
            except Exception as e:
                logger.error(f"Failed to initialize S3, falling back to local storage: {e}")
                self.use_s3 = False
        
        if not self.use_s3:
            # Setup local storage directory
            self.local_storage_dir = Path(os.getenv('LOCAL_STORAGE_DIR', 'file_storage'))
            self.local_storage_dir.mkdir(exist_ok=True, parents=True)
            logger.info(f"✅ Storage manager initialized with local filesystem: {self.local_storage_dir}")
    
    def save_file(
        self,
        file_path: Path,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Save file to storage (S3 or local)
        
        Args:
            file_path: Path to file to save
            user_id: User ID for organizing files
            metadata: Additional metadata
            
        Returns:
            Dictionary with storage details
        """
        if self.use_s3:
            return self._save_to_s3(file_path, user_id, metadata)
        else:
            return self._save_to_local(file_path, user_id, metadata)
    
    def save_fileobj(
        self,
        file_obj: BinaryIO,
        filename: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Save file object to storage
        
        Args:
            file_obj: File-like object
            filename: Original filename
            user_id: User ID
            metadata: Additional metadata
            
        Returns:
            Dictionary with storage details
        """
        if self.use_s3:
            return self._save_fileobj_to_s3(file_obj, filename, user_id, metadata)
        else:
            return self._save_fileobj_to_local(file_obj, filename, user_id, metadata)
    
    def get_file(self, storage_key: str) -> bytes:
        """
        Get file content from storage
        
        Args:
            storage_key: Storage key (S3 key or local path)
            
        Returns:
            File content as bytes
        """
        if self.use_s3:
            return self.s3_manager.get_file_object(storage_key)
        else:
            file_path = self.local_storage_dir / storage_key
            with open(file_path, 'rb') as f:
                return f.read()
    
    def get_file_to_path(self, storage_key: str, local_path: Path) -> None:
        """
        Download file from storage to local path
        
        Args:
            storage_key: Storage key
            local_path: Local path to save file
        """
        if self.use_s3:
            self.s3_manager.download_file(storage_key, local_path)
        else:
            source_path = self.local_storage_dir / storage_key
            import shutil
            shutil.copy2(source_path, local_path)
    
    def delete_file(self, storage_key: str) -> None:
        """
        Delete file from storage
        
        Args:
            storage_key: Storage key
        """
        if self.use_s3:
            self.s3_manager.delete_file(storage_key)
        else:
            file_path = self.local_storage_dir / storage_key
            if file_path.exists():
                file_path.unlink()
    
    def file_exists(self, storage_key: str) -> bool:
        """
        Check if file exists in storage
        
        Args:
            storage_key: Storage key
            
        Returns:
            True if file exists
        """
        if self.use_s3:
            return self.s3_manager.file_exists(storage_key)
        else:
            file_path = self.local_storage_dir / storage_key
            return file_path.exists()
    
    def generate_download_url(self, storage_key: str, expiration: int = 3600) -> str:
        """
        Generate download URL for file
        
        Args:
            storage_key: Storage key
            expiration: URL expiration in seconds
            
        Returns:
            Download URL (presigned for S3, local path for filesystem)
        """
        if self.use_s3:
            return self.s3_manager.generate_presigned_url(storage_key, expiration)
        else:
            # For local storage, return the storage key
            # The application should handle serving this file
            return f"/files/{storage_key}"
    
    def _save_to_s3(
        self,
        file_path: Path,
        user_id: Optional[str],
        metadata: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Save file to S3"""
        result = self.s3_manager.upload_file(file_path, user_id, metadata)
        return {
            'storage_type': 's3',
            'storage_key': result['s3_key'],
            'bucket': result['bucket'],
            'region': result['region'],
            'encryption': result['encryption'],
            'uploaded_at': result['uploaded_at']
        }
    
    def _save_fileobj_to_s3(
        self,
        file_obj: BinaryIO,
        filename: str,
        user_id: Optional[str],
        metadata: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Save file object to S3"""
        result = self.s3_manager.upload_fileobj(file_obj, filename, user_id, metadata)
        return {
            'storage_type': 's3',
            'storage_key': result['s3_key'],
            'bucket': result['bucket'],
            'region': result['region'],
            'encryption': result['encryption'],
            'uploaded_at': result['uploaded_at']
        }
    
    def _save_to_local(
        self,
        file_path: Path,
        user_id: Optional[str],
        metadata: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Save file to local filesystem"""
        import uuid
        import shutil
        
        # Generate storage key
        file_id = str(uuid.uuid4())
        ext = file_path.suffix.lower()
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        
        if user_id:
            storage_key = f"invoices/{user_id}/{date_prefix}/{file_id}{ext}"
        else:
            storage_key = f"invoices/anonymous/{date_prefix}/{file_id}{ext}"
        
        # Create directory structure
        dest_path = self.local_storage_dir / storage_key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(file_path, dest_path)
        
        logger.info(f"File saved to local storage: {storage_key}")
        
        return {
            'storage_type': 'local',
            'storage_key': storage_key,
            'local_path': str(dest_path),
            'uploaded_at': datetime.now().isoformat()
        }
    
    def _save_fileobj_to_local(
        self,
        file_obj: BinaryIO,
        filename: str,
        user_id: Optional[str],
        metadata: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Save file object to local filesystem"""
        import uuid
        
        # Generate storage key
        file_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower()
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        
        if user_id:
            storage_key = f"invoices/{user_id}/{date_prefix}/{file_id}{ext}"
        else:
            storage_key = f"invoices/anonymous/{date_prefix}/{file_id}{ext}"
        
        # Create directory structure
        dest_path = self.local_storage_dir / storage_key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(dest_path, 'wb') as f:
            f.write(file_obj.read())
        
        logger.info(f"File object saved to local storage: {storage_key}")
        
        return {
            'storage_type': 'local',
            'storage_key': storage_key,
            'local_path': str(dest_path),
            'uploaded_at': datetime.now().isoformat()
        }


# Global storage manager instance
_storage_manager: Optional[StorageManager] = None


def get_storage_manager() -> StorageManager:
    """Get or create global storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager


if __name__ == "__main__":
    # Test storage manager
    print("Testing storage manager...")
    
    manager = get_storage_manager()
    print(f"Storage type: {'S3' if manager.use_s3 else 'Local'}")
    
    if manager.use_s3:
        print(f"S3 Bucket: {manager.s3_manager.bucket_name}")
        print(f"S3 Region: {manager.s3_manager.region}")
        print(f"Encryption: {manager.s3_manager.encryption_type}")
    else:
        print(f"Local storage directory: {manager.local_storage_dir}")

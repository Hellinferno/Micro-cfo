#!/usr/bin/env python3
"""
S3 Storage Module for MicroCFO
Handles secure file storage in AWS S3 with Server-Side Encryption
"""

import os
import logging
import uuid
import mimetypes
from typing import Optional, BinaryIO, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

logger = logging.getLogger(__name__)


class S3StorageManager:
    """
    Manages file storage in AWS S3 with Server-Side Encryption
    
    Features:
    - Server-Side Encryption (SSE-S3 or SSE-KMS)
    - Presigned URLs for secure downloads
    - Automatic content type detection
    - Versioning support
    - Lifecycle management
    """
    
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        encryption_type: str = "AES256",
        kms_key_id: Optional[str] = None
    ):
        """
        Initialize S3 storage manager
        
        Args:
            bucket_name: S3 bucket name (from env if not provided)
            region: AWS region (from env if not provided)
            encryption_type: Encryption type ('AES256' for SSE-S3 or 'aws:kms' for SSE-KMS)
            kms_key_id: KMS key ID for SSE-KMS encryption
        """
        # Get configuration from environment
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        self.encryption_type = encryption_type
        self.kms_key_id = kms_key_id or os.getenv('KMS_KEY_ID')
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME must be provided or set in environment")
        
        # Configure boto3 client
        config = Config(
            region_name=self.region,
            signature_version='s3v4',
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            }
        )
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client('s3', config=config)
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def _get_encryption_params(self) -> Dict[str, str]:
        """
        Get encryption parameters for S3 operations
        
        Returns:
            Dictionary of encryption parameters
        """
        params = {'ServerSideEncryption': self.encryption_type}
        
        if self.encryption_type == 'aws:kms' and self.kms_key_id:
            params['SSEKMSKeyId'] = self.kms_key_id
        
        return params
    
    def _generate_s3_key(self, filename: str, user_id: Optional[str] = None) -> str:
        """
        Generate S3 object key with organized structure
        
        Args:
            filename: Original filename
            user_id: User ID for organizing files
            
        Returns:
            S3 object key
        """
        # Extract file extension
        ext = Path(filename).suffix.lower()
        
        # Generate unique ID
        file_id = str(uuid.uuid4())
        
        # Organize by date and user
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        
        if user_id:
            return f"invoices/{user_id}/{date_prefix}/{file_id}{ext}"
        else:
            return f"invoices/anonymous/{date_prefix}/{file_id}{ext}"
    
    def upload_file(
        self,
        file_path: Path,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to S3 with encryption
        
        Args:
            file_path: Path to file to upload
            user_id: User ID for organizing files
            metadata: Additional metadata to store with file
            
        Returns:
            Dictionary with upload details (s3_key, bucket, url, etc.)
        """
        try:
            # Generate S3 key
            s3_key = self._generate_s3_key(file_path.name, user_id)
            
            # Detect content type
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Prepare metadata
            file_metadata = {
                'original-filename': file_path.name,
                'upload-timestamp': datetime.now().isoformat(),
            }
            if user_id:
                file_metadata['user-id'] = user_id
            if metadata:
                file_metadata.update(metadata)
            
            # Get encryption parameters
            encryption_params = self._get_encryption_params()
            
            # Upload file
            with open(file_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType=content_type,
                    Metadata=file_metadata,
                    **encryption_params
                )
            
            logger.info(f"File uploaded successfully: {s3_key}")
            
            return {
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'region': self.region,
                'content_type': content_type,
                'encryption': self.encryption_type,
                'uploaded_at': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise
    
    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        filename: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file object to S3 with encryption
        
        Args:
            file_obj: File-like object to upload
            filename: Original filename
            user_id: User ID for organizing files
            metadata: Additional metadata to store with file
            
        Returns:
            Dictionary with upload details
        """
        try:
            # Generate S3 key
            s3_key = self._generate_s3_key(filename, user_id)
            
            # Detect content type
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Prepare metadata
            file_metadata = {
                'original-filename': filename,
                'upload-timestamp': datetime.now().isoformat(),
            }
            if user_id:
                file_metadata['user-id'] = user_id
            if metadata:
                file_metadata.update(metadata)
            
            # Get encryption parameters
            encryption_params = self._get_encryption_params()
            
            # Upload file object
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_obj,
                ContentType=content_type,
                Metadata=file_metadata,
                **encryption_params
            )
            
            logger.info(f"File object uploaded successfully: {s3_key}")
            
            return {
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'region': self.region,
                'content_type': content_type,
                'encryption': self.encryption_type,
                'uploaded_at': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise
    
    def download_file(self, s3_key: str, local_path: Path) -> None:
        """
        Download file from S3 to local path
        
        Args:
            s3_key: S3 object key
            local_path: Local path to save file
        """
        try:
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=s3_key,
                Filename=str(local_path)
            )
            logger.info(f"File downloaded successfully: {s3_key}")
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            raise
    
    def get_file_object(self, s3_key: str) -> bytes:
        """
        Get file content as bytes
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File content as bytes
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"S3 get object failed: {e}")
            raise
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        http_method: str = 'GET'
    ) -> str:
        """
        Generate presigned URL for secure file access
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method ('GET' or 'PUT')
            
        Returns:
            Presigned URL
        """
        try:
            method_map = {
                'GET': 'get_object',
                'PUT': 'put_object'
            }
            
            url = self.s3_client.generate_presigned_url(
                ClientMethod=method_map.get(http_method, 'get_object'),
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"Presigned URL generated for: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(self, s3_key: str) -> None:
        """
        Delete file from S3
        
        Args:
            s3_key: S3 object key
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"File deleted successfully: {s3_key}")
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            raise
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def get_file_metadata(self, s3_key: str) -> Dict[str, Any]:
        """
        Get file metadata from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dictionary with file metadata
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'encryption': response.get('ServerSideEncryption'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise
    
    def list_user_files(self, user_id: str, max_keys: int = 1000) -> list:
        """
        List all files for a specific user
        
        Args:
            user_id: User ID
            max_keys: Maximum number of keys to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            prefix = f"invoices/{user_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    's3_key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            raise


# Global S3 storage manager instance
_s3_manager: Optional[S3StorageManager] = None


def get_s3_manager() -> S3StorageManager:
    """Get or create global S3 storage manager instance"""
    global _s3_manager
    if _s3_manager is None:
        _s3_manager = S3StorageManager()
    return _s3_manager


def is_s3_enabled() -> bool:
    """Check if S3 storage is enabled"""
    return os.getenv('S3_BUCKET_NAME') is not None


if __name__ == "__main__":
    # Test S3 storage
    print("Testing S3 storage...")
    
    # Check if S3 is configured
    if not is_s3_enabled():
        print("❌ S3 not configured. Set S3_BUCKET_NAME environment variable.")
        exit(1)
    
    try:
        manager = get_s3_manager()
        print(f"✅ S3 manager initialized for bucket: {manager.bucket_name}")
        print(f"   Region: {manager.region}")
        print(f"   Encryption: {manager.encryption_type}")
    except Exception as e:
        print(f"❌ Failed to initialize S3 manager: {e}")
        exit(1)

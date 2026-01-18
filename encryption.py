#!/usr/bin/env python3
"""
Encryption Module for MicroCFO
Provides encryption/decryption for sensitive data at rest
"""

import os
import base64
import logging
from typing import Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from sqlalchemy.types import TypeDecorator, String, Text
from sqlalchemy import LargeBinary

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Manages encryption keys and provides encryption/decryption services
    
    Uses Fernet (symmetric encryption) with AES-128 in CBC mode
    Keys are derived from a master key using PBKDF2
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            master_key: Master encryption key (base64 encoded)
                       If not provided, reads from ENCRYPTION_KEY env var
        """
        # Get master key from environment or parameter
        key_str = master_key or os.getenv('ENCRYPTION_KEY')
        
        if not key_str:
            # Generate a new key if none exists (development only)
            logger.warning("No ENCRYPTION_KEY found, generating new key (NOT FOR PRODUCTION)")
            key_str = Fernet.generate_key().decode('utf-8')
            logger.warning(f"Generated key: {key_str}")
            logger.warning("Set this as ENCRYPTION_KEY environment variable")
        
        # Ensure key is bytes
        if isinstance(key_str, str):
            key_bytes = key_str.encode('utf-8')
        else:
            key_bytes = key_str
        
        # Validate key format
        try:
            self.fernet = Fernet(key_bytes)
            logger.info("Encryption manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError(f"Invalid encryption key: {e}")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        if plaintext is None:
            return None
        
        try:
            # Convert to bytes
            plaintext_bytes = plaintext.encode('utf-8')
            
            # Encrypt
            encrypted_bytes = self.fernet.encrypt(plaintext_bytes)
            
            # Return as base64 string
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string
        
        Args:
            ciphertext: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if ciphertext is None:
            return None
        
        try:
            # Convert to bytes
            ciphertext_bytes = ciphertext.encode('utf-8')
            
            # Decrypt
            decrypted_bytes = self.fernet.decrypt(ciphertext_bytes)
            
            # Return as string
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """
        Encrypt binary data
        
        Args:
            data: Binary data to encrypt
            
        Returns:
            Encrypted binary data
        """
        if data is None:
            return None
        
        try:
            return self.fernet.encrypt(data)
        except Exception as e:
            logger.error(f"Binary encryption failed: {e}")
            raise
    
    def decrypt_bytes(self, data: bytes) -> bytes:
        """
        Decrypt binary data
        
        Args:
            data: Encrypted binary data
            
        Returns:
            Decrypted binary data
        """
        if data is None:
            return None
        
        try:
            return self.fernet.decrypt(data)
        except Exception as e:
            logger.error(f"Binary decryption failed: {e}")
            raise


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create global encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy custom type for encrypted string columns
    
    Automatically encrypts data on write and decrypts on read
    Stores encrypted data as TEXT in database
    
    Usage:
        vendor_name = Column(EncryptedString(255))
    """
    
    impl = Text
    cache_ok = True
    
    def __init__(self, length: Optional[int] = None, *args, **kwargs):
        """
        Initialize encrypted string type
        
        Args:
            length: Maximum length of plaintext (for validation)
        """
        self.length = length
        super().__init__(*args, **kwargs)
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Encrypt value before storing in database
        
        Args:
            value: Plaintext value
            dialect: SQLAlchemy dialect
            
        Returns:
            Encrypted value
        """
        if value is None:
            return None
        
        # Validate length if specified
        if self.length and len(value) > self.length:
            raise ValueError(f"Value exceeds maximum length of {self.length}")
        
        # Encrypt
        manager = get_encryption_manager()
        return manager.encrypt(value)
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Decrypt value after reading from database
        
        Args:
            value: Encrypted value
            dialect: SQLAlchemy dialect
            
        Returns:
            Decrypted plaintext value
        """
        if value is None:
            return None
        
        # Decrypt
        manager = get_encryption_manager()
        return manager.decrypt(value)


class EncryptedText(TypeDecorator):
    """
    SQLAlchemy custom type for encrypted text columns
    
    Similar to EncryptedString but for longer text fields
    
    Usage:
        email_content = Column(EncryptedText)
    """
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt value before storing"""
        if value is None:
            return None
        
        manager = get_encryption_manager()
        return manager.encrypt(value)
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt value after reading"""
        if value is None:
            return None
        
        manager = get_encryption_manager()
        return manager.decrypt(value)


class EncryptedNumeric(TypeDecorator):
    """
    SQLAlchemy custom type for encrypted numeric columns
    
    Encrypts numeric values (stored as strings internally)
    
    Usage:
        total_amount = Column(EncryptedNumeric(15, 2))
    """
    
    impl = Text
    cache_ok = True
    
    def __init__(self, precision: int = 15, scale: int = 2, *args, **kwargs):
        """
        Initialize encrypted numeric type
        
        Args:
            precision: Total number of digits
            scale: Number of decimal places
        """
        self.precision = precision
        self.scale = scale
        super().__init__(*args, **kwargs)
    
    def process_bind_param(self, value: Optional[Any], dialect) -> Optional[str]:
        """Encrypt numeric value before storing"""
        if value is None:
            return None
        
        # Convert to string
        value_str = str(value)
        
        # Encrypt
        manager = get_encryption_manager()
        return manager.encrypt(value_str)
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[float]:
        """Decrypt and convert back to numeric"""
        if value is None:
            return None
        
        # Decrypt
        manager = get_encryption_manager()
        decrypted = manager.decrypt(value)
        
        # Convert back to float
        try:
            return float(decrypted)
        except ValueError:
            logger.error(f"Failed to convert decrypted value to float: {decrypted}")
            return None


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key
    
    Returns:
        Base64 encoded encryption key
    """
    key = Fernet.generate_key()
    return key.decode('utf-8')


def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
    """
    Derive an encryption key from a password using PBKDF2
    
    Args:
        password: Password to derive key from
        salt: Salt for key derivation (generated if not provided)
        
    Returns:
        Tuple of (base64 encoded key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return key.decode('utf-8'), salt


# Utility functions for testing
def test_encryption():
    """Test encryption/decryption functionality"""
    manager = get_encryption_manager()
    
    # Test string encryption
    plaintext = "Sensitive data 123"
    encrypted = manager.encrypt(plaintext)
    decrypted = manager.decrypt(encrypted)
    
    assert plaintext == decrypted, "String encryption/decryption failed"
    logger.info("✅ String encryption test passed")
    
    # Test binary encryption
    binary_data = b"Binary sensitive data"
    encrypted_binary = manager.encrypt_bytes(binary_data)
    decrypted_binary = manager.decrypt_bytes(encrypted_binary)
    
    assert binary_data == decrypted_binary, "Binary encryption/decryption failed"
    logger.info("✅ Binary encryption test passed")
    
    logger.info("✅ All encryption tests passed")


if __name__ == "__main__":
    # Generate a new key for setup
    print("Generating new encryption key...")
    key = generate_encryption_key()
    print(f"\nEncryption Key (save this securely):")
    print(key)
    print("\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key}")
    
    # Test encryption
    print("\nTesting encryption...")
    os.environ['ENCRYPTION_KEY'] = key
    test_encryption()

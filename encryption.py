"""Compatibility shim for Alembic migrations.

Exports get_encryption_manager from src.encryption so migrations can import
`from encryption import get_encryption_manager`.
"""

from src.encryption import get_encryption_manager  # re-export

__all__ = ["get_encryption_manager"]

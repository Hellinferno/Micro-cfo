"""
Pytest configuration and fixtures for test suite
Ensures proper database cleanup between test runs
"""

import os
import pytest
from sqlalchemy import create_engine


def _create_cleanup_engine(test_db_url):
    """
    Helper function to create an engine for database cleanup.
    
    Args:
        test_db_url: Database URL string in SQLAlchemy format
                     (e.g., 'sqlite:///:memory:', 'sqlite:///path/to/db.sqlite',
                      'postgresql://user:pass@host:port/dbname')
        
    Returns:
        SQLAlchemy engine instance configured appropriately for the database type
    """
    if test_db_url.startswith('sqlite://'):
        return create_engine(test_db_url, connect_args={"check_same_thread": False})
    else:
        return create_engine(test_db_url)


def _cleanup_database(test_db_url, phase="session"):
    """
    Helper function to clean up database by dropping all tables.
    Only cleans persistent databases; skips in-memory SQLite databases.
    
    Args:
        test_db_url: Database URL string in SQLAlchemy format
        phase: Description of when cleanup is happening (for logging)
    """
    # Only clean up if using a persistent database (not in-memory)
    if not test_db_url.startswith('sqlite:///:memory:'):
        try:
            from src.database import Base
            
            # Create engine for cleanup
            engine = _create_cleanup_engine(test_db_url)
            
            # Drop all tables to ensure clean state
            Base.metadata.drop_all(bind=engine)
            engine.dispose()
            print(f"\n✓ Database cleaned up at {phase}: {test_db_url}")
        except Exception as e:
            print(f"\n⚠ Warning: Could not clean up database at {phase}: {e}")


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and before performing collection
    and entering the run test loop. Ensures database is clean at the start of test session.
    """
    # Get DATABASE_URL from environment or use in-memory SQLite
    test_db_url = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
    _cleanup_database(test_db_url, phase="session start")


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before returning the exit status.
    Ensures database is cleaned up after test session.
    """
    # Get DATABASE_URL from environment or use in-memory SQLite
    test_db_url = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
    _cleanup_database(test_db_url, phase="session end")

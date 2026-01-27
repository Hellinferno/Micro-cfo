"""
Pytest configuration and fixtures for test suite
Ensures proper database cleanup between test runs
"""

import os
import pytest
from sqlalchemy import create_engine


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and before performing collection
    and entering the run test loop. Ensures database is clean at the start of test session.
    """
    # Get DATABASE_URL from environment or use in-memory SQLite
    test_db_url = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
    
    # Only clean up if using a persistent database (not in-memory)
    if ':memory:' not in test_db_url:
        try:
            from src.database import Base
            
            # Create engine for cleanup
            if test_db_url.startswith('sqlite'):
                engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
            else:
                engine = create_engine(test_db_url)
            
            # Drop all tables to ensure clean state
            Base.metadata.drop_all(bind=engine)
            engine.dispose()
            print(f"\n✓ Database cleaned up at session start: {test_db_url}")
        except Exception as e:
            print(f"\n⚠ Warning: Could not clean up database at session start: {e}")


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before returning the exit status.
    Ensures database is cleaned up after test session.
    """
    # Get DATABASE_URL from environment or use in-memory SQLite
    test_db_url = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
    
    # Only clean up if using a persistent database (not in-memory)
    if ':memory:' not in test_db_url:
        try:
            from src.database import Base
            
            # Create engine for cleanup
            if test_db_url.startswith('sqlite'):
                engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
            else:
                engine = create_engine(test_db_url)
            
            # Drop all tables after tests
            Base.metadata.drop_all(bind=engine)
            engine.dispose()
            print(f"\n✓ Database cleaned up at session end: {test_db_url}")
        except Exception as e:
            print(f"\n⚠ Warning: Could not clean up database at session end: {e}")

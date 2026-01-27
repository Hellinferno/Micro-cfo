"""
Pytest configuration and shared fixtures for all tests
Provides centralized database setup with proper cleanup
"""

import os
import sys
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Base


# Use in-memory SQLite for unit tests (fast and isolated)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """
    Create a test database engine for the entire test session.
    Uses in-memory SQLite with proper configuration for testing.
    """
    # Create engine with SQLite-specific settings for better test isolation
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={
            "check_same_thread": False,  # Allow multi-threaded access
        },
        poolclass=StaticPool,  # Use static pool for in-memory DB
        echo=False,  # Set to True for SQL debugging
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    yield test_engine
    
    # Cleanup
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Create a fresh database session for each test function.
    Properly cleans up tables before and after each test to prevent
    index conflicts and ensure test isolation.
    """
    # Drop all tables and indexes to ensure clean slate
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables fresh
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        # Cleanup after test
        session.rollback()
        session.close()
        
        # Drop all tables and indexes to prevent conflicts with next test
        Base.metadata.drop_all(bind=engine)


# Alias for backward compatibility with existing tests
@pytest.fixture(scope="function")
def test_db(db_session):
    """
    Alias for db_session fixture to maintain compatibility
    with existing test code.
    """
    return db_session

"""
Database configuration and session management
SQLAlchemy setup for PostgreSQL integration
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
import logging

logger = logging.getLogger(__name__)

# Database URL from environment, allowing fallbacks via individual settings
_explicit_database_url = os.getenv('DATABASE_URL')

if _explicit_database_url:
    DATABASE_URL = _explicit_database_url
else:
    db_user = os.getenv('POSTGRES_USER', 'microcfo')
    db_password = os.getenv('POSTGRES_PASSWORD', 'changeme')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'microcfo')

    if db_user == 'root':
        logger.warning("Database user is set to 'root'. Expected dedicated user like 'microcfo'.")

    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False,          # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db() -> Session:
    """
    FastAPI dependency for database sessions
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Context manager for database sessions
    Usage: with get_db_context() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def reset_db():
    """Drop and recreate all database tables - USE WITH CAUTION"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables recreated successfully")
    except Exception as e:
        logger.error(f"Failed to reset database tables: {e}")
        raise

def check_db_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

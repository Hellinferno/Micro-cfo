"""
Test suite for PostgreSQL database integration
Tests models, CRUD operations, and database functionality
"""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
import uuid

# Ensure project root is on the path for imports during test collection
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Base, get_db_context
from src.models import User, UserProfile, Invoice, LegalQuery, SubsidyApplication, Negotiation, AuditLog
from src.crud import (
    create_user, get_user_by_email, get_user_by_id, update_user,
    create_user_profile, get_user_profile, update_user_profile,
    create_invoice, get_invoice, get_user_invoices, update_invoice,
    create_legal_query, get_legal_query, get_user_legal_queries,
    create_subsidy_application, get_subsidy_application, get_user_subsidy_applications,
    create_negotiation, get_negotiation, get_user_negotiations,
    create_audit_log, get_audit_logs
)

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """Create test database and session with proper cleanup"""
    # Use environment DATABASE_URL if set (for CI), otherwise use in-memory SQLite
    test_db_url = os.getenv('DATABASE_URL', TEST_DATABASE_URL)
    
    # Configure engine based on database type
    if test_db_url.startswith('sqlite://'):
        engine = create_engine(
            test_db_url,
            connect_args={"check_same_thread": False},
            poolclass=None
        )
    else:
        # PostgreSQL or other databases
        engine = create_engine(test_db_url, poolclass=None)
    
    # Ensure clean state: drop all tables before creating
    # This prevents "index already exists" errors by starting fresh
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        # Clean up after test
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user"""
    user = create_user(
        db=test_db,
        email="test@example.com",
        password="testpassword123",
        full_name="Test User",
        company_name="Test Company",
        business_sector="Technology",
        turnover_tier="5-20Cr"
    )
    return user

class TestUserOperations:
    """Test user CRUD operations"""
    
    def test_create_user(self, test_db):
        """Test user creation"""
        user = create_user(
            db=test_db,
            email="newuser@example.com",
            password="password123",
            full_name="New User",
            company_name="New Company"
        )
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_verified is False
    
    def test_get_user_by_email(self, test_db, test_user):
        """Test retrieving user by email"""
        user = get_user_by_email(test_db, "test@example.com")
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    def test_get_user_by_id(self, test_db, test_user):
        """Test retrieving user by ID"""
        user = get_user_by_id(test_db, test_user.id)
        
        assert user is not None
        assert user.email == test_user.email
    
    def test_update_user(self, test_db, test_user):
        """Test updating user"""
        updated_user = update_user(
            test_db,
            test_user.id,
            full_name="Updated Name",
            company_name="Updated Company"
        )
        
        assert updated_user.full_name == "Updated Name"
        assert updated_user.company_name == "Updated Company"
    
    def test_user_relationships(self, test_db, test_user):
        """Test user relationships are set up correctly"""
        assert hasattr(test_user, 'profile')
        assert hasattr(test_user, 'invoices')
        assert hasattr(test_user, 'legal_queries')
        assert hasattr(test_user, 'subsidy_applications')
        assert hasattr(test_user, 'negotiations')

class TestUserProfileOperations:
    """Test user profile CRUD operations"""
    
    def test_create_user_profile(self, test_db, test_user):
        """Test profile creation"""
        profile = create_user_profile(
            db=test_db,
            user_id=test_user.id,
            business_type="Manufacturing",
            gst_number="27AABCU9603R1ZM",
            pan_number="AABCU9603R",
            preferences={"language": "en", "notifications": True}
        )
        
        assert profile.id is not None
        assert profile.user_id == test_user.id
        assert profile.gst_number == "27AABCU9603R1ZM"
        assert profile.preferences["language"] == "en"
    
    def test_get_user_profile(self, test_db, test_user):
        """Test retrieving user profile"""
        create_user_profile(
            db=test_db,
            user_id=test_user.id,
            gst_number="27AABCU9603R1ZM"
        )
        
        profile = get_user_profile(test_db, test_user.id)
        
        assert profile is not None
        assert profile.user_id == test_user.id
    
    def test_update_user_profile(self, test_db, test_user):
        """Test updating user profile"""
        create_user_profile(db=test_db, user_id=test_user.id)
        
        updated_profile = update_user_profile(
            test_db,
            test_user.id,
            gst_number="NEW_GST_NUMBER",
            pan_number="NEW_PAN"
        )
        
        assert updated_profile.gst_number == "NEW_GST_NUMBER"
        assert updated_profile.pan_number == "NEW_PAN"

class TestInvoiceOperations:
    """Test invoice CRUD operations"""
    
    def test_create_invoice(self, test_db, test_user):
        """Test invoice creation"""
        invoice = create_invoice(
            db=test_db,
            user_id=test_user.id,
            invoice_number="INV-2024-001",
            vendor_name="ABC Suppliers",
            invoice_date=date(2024, 1, 15),
            total_amount=50000.00,
            tax_amount=9000.00,
            status="processed",
            extracted_data={"confidence": 0.95}
        )
        
        assert invoice.id is not None
        assert invoice.invoice_number == "INV-2024-001"
        assert invoice.vendor_name == "ABC Suppliers"
        assert float(invoice.total_amount) == 50000.00
        assert invoice.extracted_data["confidence"] == 0.95
    
    def test_get_invoice(self, test_db, test_user):
        """Test retrieving invoice"""
        created_invoice = create_invoice(
            db=test_db,
            user_id=test_user.id,
            invoice_number="INV-001"
        )
        
        invoice = get_invoice(test_db, created_invoice.id)
        
        assert invoice is not None
        assert invoice.id == created_invoice.id
    
    def test_get_user_invoices(self, test_db, test_user):
        """Test retrieving user's invoices"""
        # Create multiple invoices
        for i in range(5):
            create_invoice(
                db=test_db,
                user_id=test_user.id,
                invoice_number=f"INV-{i}",
                status="pending" if i % 2 == 0 else "processed"
            )
        
        # Get all invoices
        all_invoices = get_user_invoices(test_db, test_user.id)
        assert len(all_invoices) == 5
        
        # Get pending invoices
        pending_invoices = get_user_invoices(test_db, test_user.id, status="pending")
        assert len(pending_invoices) == 3
    
    def test_update_invoice(self, test_db, test_user):
        """Test updating invoice"""
        invoice = create_invoice(
            db=test_db,
            user_id=test_user.id,
            status="pending"
        )
        
        updated_invoice = update_invoice(
            test_db,
            invoice.id,
            status="processed",
            total_amount=75000.00
        )
        
        assert updated_invoice.status == "processed"
        assert float(updated_invoice.total_amount) == 75000.00

class TestLegalQueryOperations:
    """Test legal query CRUD operations"""
    
    def test_create_legal_query(self, test_db, test_user):
        """Test legal query creation"""
        query = create_legal_query(
            db=test_db,
            user_id=test_user.id,
            query_text="GST compliance for exports",
            response_text="Section 16 applies...",
            risk_level="MEDIUM",
            relevant_sections={"sections": ["Section 16"]}
        )
        
        assert query.id is not None
        assert query.query_text == "GST compliance for exports"
        assert query.risk_level == "MEDIUM"
    
    def test_get_user_legal_queries(self, test_db, test_user):
        """Test retrieving user's legal queries"""
        # Create multiple queries
        for i in range(3):
            create_legal_query(
                db=test_db,
                user_id=test_user.id,
                query_text=f"Query {i}"
            )
        
        queries = get_user_legal_queries(test_db, test_user.id)
        assert len(queries) == 3

class TestSubsidyApplicationOperations:
    """Test subsidy application CRUD operations"""
    
    def test_create_subsidy_application(self, test_db, test_user):
        """Test subsidy application creation"""
        application = create_subsidy_application(
            db=test_db,
            user_id=test_user.id,
            scheme_name="Export Promotion Scheme",
            eligibility_status="eligible",
            application_status="draft"
        )
        
        assert application.id is not None
        assert application.scheme_name == "Export Promotion Scheme"
        assert application.application_status == "draft"
    
    def test_get_user_subsidy_applications(self, test_db, test_user):
        """Test retrieving user's subsidy applications"""
        # Create applications
        for i in range(4):
            create_subsidy_application(
                db=test_db,
                user_id=test_user.id,
                scheme_name=f"Scheme {i}",
                application_status="draft" if i % 2 == 0 else "submitted"
            )
        
        # Get all applications
        all_apps = get_user_subsidy_applications(test_db, test_user.id)
        assert len(all_apps) == 4
        
        # Get draft applications
        draft_apps = get_user_subsidy_applications(test_db, test_user.id, status="draft")
        assert len(draft_apps) == 2

class TestNegotiationOperations:
    """Test negotiation CRUD operations"""
    
    def test_create_negotiation(self, test_db, test_user):
        """Test negotiation creation"""
        negotiation = create_negotiation(
            db=test_db,
            user_id=test_user.id,
            vendor_name="XYZ Vendor",
            negotiation_type="payment_extension",
            email_content="Dear Vendor...",
            status="draft"
        )
        
        assert negotiation.id is not None
        assert negotiation.vendor_name == "XYZ Vendor"
        assert negotiation.negotiation_type == "payment_extension"
    
    def test_get_user_negotiations(self, test_db, test_user):
        """Test retrieving user's negotiations"""
        # Create negotiations
        for i in range(3):
            create_negotiation(
                db=test_db,
                user_id=test_user.id,
                vendor_name=f"Vendor {i}",
                negotiation_type="payment_extension",
                email_content="Email content"
            )
        
        negotiations = get_user_negotiations(test_db, test_user.id)
        assert len(negotiations) == 3

class TestAuditLogOperations:
    """Test audit log CRUD operations"""
    
    def test_create_audit_log(self, test_db, test_user):
        """Test audit log creation"""
        log = create_audit_log(
            db=test_db,
            user_id=test_user.id,
            action="invoice_created",
            resource_type="invoice",
            resource_id=uuid.uuid4(),
            details={"amount": 50000},
            ip_address="192.168.1.1"
        )
        
        assert log.id is not None
        assert log.action == "invoice_created"
        assert log.details["amount"] == 50000
    
    def test_get_audit_logs(self, test_db, test_user):
        """Test retrieving audit logs"""
        # Create logs
        for i in range(5):
            create_audit_log(
                db=test_db,
                user_id=test_user.id,
                action=f"action_{i}",
                resource_type="invoice" if i % 2 == 0 else "query"
            )
        
        # Get all logs
        all_logs = get_audit_logs(test_db)
        assert len(all_logs) == 5
        
        # Get user logs
        user_logs = get_audit_logs(test_db, user_id=test_user.id)
        assert len(user_logs) == 5
        
        # Get invoice logs
        invoice_logs = get_audit_logs(test_db, resource_type="invoice")
        assert len(invoice_logs) == 3

class TestDatabaseIntegration:
    """Test database integration features"""
    
    def test_cascade_delete(self, test_db, test_user):
        """Test cascade delete on user deletion"""
        # Create related records
        create_invoice(test_db, test_user.id, invoice_number="INV-001")
        create_legal_query(test_db, test_user.id, query_text="Test query")
        
        # Delete user
        test_db.delete(test_user)
        test_db.commit()
        
        # Verify related records are deleted
        invoices = get_user_invoices(test_db, test_user.id)
        assert len(invoices) == 0
    
    def test_jsonb_fields(self, test_db, test_user):
        """Test JSONB field storage and retrieval"""
        invoice = create_invoice(
            db=test_db,
            user_id=test_user.id,
            extracted_data={
                "line_items": [
                    {"description": "Item 1", "amount": 1000},
                    {"description": "Item 2", "amount": 2000}
                ],
                "confidence": 0.95,
                "metadata": {"source": "gemini"}
            }
        )
        
        retrieved = get_invoice(test_db, invoice.id)
        assert retrieved.extracted_data["confidence"] == 0.95
        assert len(retrieved.extracted_data["line_items"]) == 2
    
    def test_timestamps(self, test_db, test_user):
        """Test automatic timestamp generation"""
        invoice = create_invoice(test_db, test_user.id)
        
        assert invoice.created_at is not None
        assert invoice.updated_at is not None
        assert isinstance(invoice.created_at, datetime)

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

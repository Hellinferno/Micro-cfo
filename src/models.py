"""
SQLAlchemy ORM Models for MicroCFO
Maps to PostgreSQL database schema with encryption for sensitive data
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Numeric, Text,
    ForeignKey, Index, DECIMAL, Integer, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
from src.encryption import EncryptedString, EncryptedText, EncryptedNumeric
import uuid
import sys

# Ensure a single module instance is used regardless of import path
if __name__ == "models":
    sys.modules.setdefault("src.models", sys.modules[__name__])
elif __name__ == "src.models":
    sys.modules.setdefault("models", sys.modules[__name__])

class User(Base):
    """User model for authentication and profile"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_name = Column(String(255))
    business_sector = Column(String(100))
    turnover_tier = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")
    legal_queries = relationship("LegalQuery", back_populates="user", cascade="all, delete-orphan")
    subsidy_applications = relationship("SubsidyApplication", back_populates="user", cascade="all, delete-orphan")
    negotiations = relationship("Negotiation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(email='{self.email}', company='{self.company_name}')>"

class UserProfile(Base):
    """Extended user profile with business details and encrypted sensitive data"""
    __tablename__ = 'user_profiles'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    business_type = Column(String(100))
    gst_number = Column(EncryptedString(50))  # Encrypted - sensitive tax ID
    pan_number = Column(EncryptedString(20))  # Encrypted - sensitive tax ID
    registered_address = Column(EncryptedText)  # Encrypted - PII
    preferences = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}')>"

class Invoice(Base):
    """Invoice records from Agent A (Visual Auditor) with encrypted sensitive data"""
    __tablename__ = 'invoices'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    invoice_number = Column(EncryptedString(100))  # Encrypted
    vendor_name = Column(EncryptedString(255))  # Encrypted
    invoice_date = Column(Date)
    due_date = Column(Date)
    total_amount = Column(EncryptedNumeric(15, 2))  # Encrypted
    tax_amount = Column(EncryptedNumeric(15, 2))  # Encrypted
    currency = Column(String(10), default='INR')
    status = Column(String(50), default='pending', index=True)
    file_path = Column(EncryptedText)  # Encrypted S3 key
    extracted_data = Column(JSONB)  # Consider encrypting if contains PII
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice(id='{self.id}', status='{self.status}')>"

class LegalQuery(Base):
    """Legal compliance queries from Agent B (Legal Sentinel)"""
    __tablename__ = 'legal_queries'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text)
    risk_level = Column(String(20))
    relevant_sections = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="legal_queries")
    
    def __repr__(self):
        return f"<LegalQuery(user_id='{self.user_id}', risk='{self.risk_level}')>"

class SubsidyApplication(Base):
    """Subsidy applications from Agent C (Subsidy Hunter)"""
    __tablename__ = 'subsidy_applications'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    scheme_name = Column(String(255))
    scheme_description = Column(Text)
    eligibility_status = Column(String(50))
    application_status = Column(String(50), default='draft')
    applied_date = Column(Date)
    scheme_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subsidy_applications")
    
    def __repr__(self):
        return f"<SubsidyApplication(scheme='{self.scheme_name}', status='{self.application_status}')>"

class Negotiation(Base):
    """Negotiation emails from Agent D (Negotiator) with encrypted content"""
    __tablename__ = 'negotiations'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    vendor_name = Column(EncryptedString(255))  # Encrypted
    negotiation_type = Column(String(100))
    email_content = Column(EncryptedText)  # Encrypted - sensitive business communication
    status = Column(String(50), default='draft')
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="negotiations")
    
    def __repr__(self):
        return f"<Negotiation(id='{self.id}', type='{self.negotiation_type}')>"

class AuditLog(Base):
    """Audit trail for all user actions"""
    __tablename__ = 'audit_logs'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', resource='{self.resource_type}')>"

class WorkflowState(Base):
    """Tracks the state of complex, multi-step agent workflows (The Brain's Memory)"""
    __tablename__ = "workflow_states"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(50)) # e.g., "AUDIT_COMPLETE", "NEGOTIATION_SUGGESTED"
    current_step = Column(String(100)) # "waiting_for_user_approval"
    context_data = Column(JSONB, default={}) # Stores data passed between agents
    history = Column(JSONB, default=[]) # Audit trail of AI decisions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice")

    def __repr__(self):
        return f"<WorkflowState(status='{self.status}', step='{self.current_step}')>"

class VendorProfile(Base):
    """Vendor CRM profile for AI negotiation strategy (The Memory)"""
    __tablename__ = "vendor_profiles"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), index=True)
    average_spend_monthly = Column(Float, default=0.0)
    negotiation_hardness_score = Column(Float, default=5.0) # 1-10 (AI estimated)
    last_negotiation_date = Column(DateTime(timezone=True))
    successful_tactics = Column(Text) # e.g., "Responds well to bulk discount offers"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<VendorProfile(name='{self.name}', hardness='{self.negotiation_hardness_score}')>"


# Create indexes
Index('idx_invoices_user_status', Invoice.user_id, Invoice.status)
Index('idx_legal_queries_user_created', LegalQuery.user_id, LegalQuery.created_at)
Index('idx_subsidy_apps_user_status', SubsidyApplication.user_id, SubsidyApplication.application_status)

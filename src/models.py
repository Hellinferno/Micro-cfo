"""
SQLAlchemy ORM Models for MicroCFO
Maps to PostgreSQL database schema with encryption for sensitive data
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Numeric, Text,
    ForeignKey, Index, DECIMAL, Integer, Float, JSON
)
from sqlalchemy.dialects.postgresql import UUID, INET
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
    phone_number = Column(String(20), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_name = Column(String(255))
    business_sector = Column(String(100))
    turnover_tier = Column(String(50))
    role = Column(String(50), default="owner")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")
    businesses = relationship("BusinessProfile", back_populates="owner", cascade="all, delete-orphan")
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
    preferences = Column(JSON, default={})  # Use JSON for SQLite/Postgres compatibility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}')>"

class BusinessProfile(Base):
    """Business profile used by Legislative Sentinel and Subsidy Hunter"""
    __tablename__ = "business_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    business_name = Column(String(255))
    industry_type = Column(String(100))
    turnover_range = Column(String(50))
    gstin = Column(EncryptedString(50))  # Encrypted GSTIN
    location_state = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="businesses")
    invoices = relationship("Invoice", back_populates="business", cascade="all, delete-orphan")
    subsidy_matches = relationship("SubsidyMatch", back_populates="business", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BusinessProfile(business_name='{self.business_name}', owner_id='{self.owner_id}')>"

class Invoice(Base):
    """Invoice records from Agent A (Visual Auditor) with encrypted sensitive data"""
    __tablename__ = 'invoices'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey('business_profiles.id', ondelete='SET NULL'), nullable=True, index=True)
    invoice_number = Column(EncryptedString(100))  # Encrypted
    vendor_name = Column(EncryptedString(255))  # Encrypted
    invoice_date = Column(Date)
    due_date = Column(Date)
    total_amount = Column(EncryptedNumeric(15, 2))  # Encrypted
    tax_amount = Column(EncryptedNumeric(15, 2))  # Encrypted
    currency = Column(String(10), default='INR')
    status = Column(String(50), default='pending', index=True)
    file_path = Column(EncryptedText)  # Encrypted S3 key
    image_url = Column(EncryptedText)  # Encrypted cloud URL
    category = Column(String(50))  # Business, Personal, Capital Goods
    compliance_status = Column(String(50))  # Clean, Flagged, Review Needed
    audit_notes = Column(Text)
    is_verified = Column(Boolean, default=False)
    extracted_data = Column(JSON)  # Consider encrypting if contains PII
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    business = relationship("BusinessProfile", back_populates="invoices")
    
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
    relevant_sections = Column(JSON)
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
    scheme_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subsidy_applications")
    
    def __repr__(self):
        return f"<SubsidyApplication(scheme='{self.scheme_name}', status='{self.application_status}')>"

class SubsidyMatch(Base):
    """Subsidy opportunities matched to a business profile"""
    __tablename__ = "subsidy_matches"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey('business_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    scheme_name = Column(String(255))
    match_score = Column(Float)
    status = Column(String(50), default="New")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    business = relationship("BusinessProfile", back_populates="subsidy_matches")

    def __repr__(self):
        return f"<SubsidyMatch(scheme='{self.scheme_name}', status='{self.status}')>"

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
    details = Column(JSON)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', resource='{self.resource_type}')>"

class UsageLog(Base):
    """LLM usage and cost tracking per request"""
    __tablename__ = "usage_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    route = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=True)
    model_used = Column(String(100))
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Numeric(12, 6), default=0)
    duration_ms = Column(Float, default=0.0)
    request_id = Column(String(100))
    meta_info = Column(JSON)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<UsageLog(route='{self.route}', cost='{self.total_cost_usd}')>"

class WorkflowState(Base):
    """Tracks the state of complex, multi-step agent workflows (The Brain's Memory)"""
    __tablename__ = "workflow_states"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(50)) # e.g., "AUDIT_COMPLETE", "NEGOTIATION_SUGGESTED"
    current_step = Column(String(100)) # "waiting_for_user_approval"
    context_data = Column(JSON, default={}) # Stores data passed between agents
    history = Column(JSON, default=[]) # Audit trail of AI decisions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice")

    def __repr__(self):
        return f"<WorkflowState(status='{self.status}', step='{self.current_step}')>"

class GoldenDataset(Base):
    """Human-corrected AI outputs for model improvement"""
    __tablename__ = "golden_dataset"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True, index=True)
    model_used = Column(String(100))
    original_data = Column(JSON, nullable=False)
    corrected_data = Column(JSON, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User")
    invoice = relationship("Invoice")

    def __repr__(self):
        return f"<GoldenDataset(id='{self.id}', model='{self.model_used}')>"

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


class ProactiveNotification(Base):
    """
    Proactive intelligence notifications for users
    Stores subsidy matches, law change alerts, and compliance reminders
    """
    __tablename__ = "proactive_notifications"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # 'subsidy_match', 'law_change', 'compliance_reminder'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default='medium')  # 'high', 'medium', 'low'
    action_url = Column(String(500))
    related_data = Column(JSON)  # Stores schemes, sections, metadata
    is_read = Column(Boolean, default=False, index=True)
    is_dismissed = Column(Boolean, default=False)
    triggered_by_invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
    triggered_invoice = relationship("Invoice")
    
    def __repr__(self):
        return f"<ProactiveNotification(type='{self.alert_type}', user='{self.user_id}')>"


class LawChangeMonitor(Base):
    """
    Tracks law changes and which users have been notified
    Enables incremental monitoring without re-alerting for same changes
    """
    __tablename__ = "law_change_monitors"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    law_type = Column(String(50), nullable=False, index=True)  # 'GST', 'Income Tax', 'Companies Act'
    section_number = Column(String(100))
    change_summary = Column(Text)
    source_url = Column(String(500))
    effective_date = Column(Date)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    hash_signature = Column(String(64), unique=True)  # SHA256 hash to detect duplicates
    
    def __repr__(self):
        return f"<LawChangeMonitor(law='{self.law_type}', section='{self.section_number}')>"


class UserLawSubscription(Base):
    """
    Tracks which law types/sections a user wants to monitor
    Enables personalized law change notifications
    """
    __tablename__ = "user_law_subscriptions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    law_type = Column(String(50), nullable=False)  # 'GST', 'Income Tax', 'Companies Act', 'All'
    specific_sections = Column(JSON)  # Optional: specific sections to monitor
    turnover_threshold_alert = Column(Boolean, default=True)  # Alert when turnover thresholds change
    sector_specific_alert = Column(Boolean, default=True)  # Alert for sector-specific changes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserLawSubscription(user='{self.user_id}', law='{self.law_type}')>"


# Create indexes
Index('idx_invoices_user_status', Invoice.user_id, Invoice.status)
Index('idx_invoices_business_status', Invoice.business_id, Invoice.status)
Index('idx_business_owner', BusinessProfile.owner_id)
Index('idx_legal_queries_user_created', LegalQuery.user_id, LegalQuery.created_at)
Index('idx_subsidy_apps_user_status', SubsidyApplication.user_id, SubsidyApplication.application_status)
Index('idx_usage_logs_user_created', UsageLog.user_id, UsageLog.created_at)
Index('idx_golden_dataset_user_created', GoldenDataset.user_id, GoldenDataset.created_at)
Index('idx_proactive_notifications_user_unread', ProactiveNotification.user_id, ProactiveNotification.is_read)
Index('idx_proactive_notifications_user_type', ProactiveNotification.user_id, ProactiveNotification.alert_type)
Index('idx_law_change_hash', LawChangeMonitor.hash_signature)
Index('idx_user_law_sub_user_law', UserLawSubscription.user_id, UserLawSubscription.law_type)

"""
CRUD operations for database models
Create, Read, Update, Delete functions for all entities
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid

from src.models import (
    User, UserProfile, Invoice, LegalQuery,
    SubsidyApplication, Negotiation, AuditLog
)
from src.auth import get_password_hash

# ============================================
# User CRUD Operations
# ============================================

def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    company_name: Optional[str] = None,
    business_sector: Optional[str] = None,
    turnover_tier: Optional[str] = None
) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        company_name=company_name,
        business_sector=business_sector,
        turnover_tier=turnover_tier
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def update_user(db: Session, user_id: uuid.UUID, **kwargs) -> Optional[User]:
    """Update user fields"""
    user = get_user_by_id(db, user_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    """Delete user (soft delete by setting is_active=False)"""
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = False
        db.commit()
        return True
    return False

# ============================================
# User Profile CRUD Operations
# ============================================

def create_user_profile(
    db: Session,
    user_id: uuid.UUID,
    business_type: Optional[str] = None,
    gst_number: Optional[str] = None,
    pan_number: Optional[str] = None,
    registered_address: Optional[str] = None,
    preferences: Optional[Dict] = None
) -> UserProfile:
    """Create user profile"""
    profile = UserProfile(
        user_id=user_id,
        business_type=business_type,
        gst_number=gst_number,
        pan_number=pan_number,
        registered_address=registered_address,
        preferences=preferences or {}
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def get_user_profile(db: Session, user_id: uuid.UUID) -> Optional[UserProfile]:
    """Get user profile"""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

def update_user_profile(db: Session, user_id: uuid.UUID, **kwargs) -> Optional[UserProfile]:
    """Update user profile"""
    profile = get_user_profile(db, user_id)
    if profile:
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        db.commit()
        db.refresh(profile)
    return profile

# ============================================
# Invoice CRUD Operations
# ============================================

def create_invoice(
    db: Session,
    user_id: uuid.UUID,
    invoice_number: Optional[str] = None,
    vendor_name: Optional[str] = None,
    invoice_date: Optional[date] = None,
    due_date: Optional[date] = None,
    total_amount: Optional[float] = None,
    tax_amount: Optional[float] = None,
    currency: str = 'INR',
    status: str = 'pending',
    file_path: Optional[str] = None,
    extracted_data: Optional[Dict] = None
) -> Invoice:
    """Create invoice record"""
    invoice = Invoice(
        user_id=user_id,
        invoice_number=invoice_number,
        vendor_name=vendor_name,
        invoice_date=invoice_date,
        due_date=due_date,
        total_amount=total_amount,
        tax_amount=tax_amount,
        currency=currency,
        status=status,
        file_path=file_path,
        extracted_data=extracted_data
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

def get_invoice(db: Session, invoice_id: uuid.UUID) -> Optional[Invoice]:
    """Get invoice by ID"""
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()

def get_user_invoices(
    db: Session,
    user_id: uuid.UUID,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Invoice]:
    """Get user's invoices with optional filtering"""
    query = db.query(Invoice).filter(Invoice.user_id == user_id)
    if status:
        query = query.filter(Invoice.status == status)
    return query.order_by(desc(Invoice.created_at)).limit(limit).offset(offset).all()

def update_invoice(db: Session, invoice_id: uuid.UUID, **kwargs) -> Optional[Invoice]:
    """Update invoice"""
    invoice = get_invoice(db, invoice_id)
    if invoice:
        for key, value in kwargs.items():
            if hasattr(invoice, key):
                setattr(invoice, key, value)
        db.commit()
        db.refresh(invoice)
    return invoice

def delete_invoice(db: Session, invoice_id: uuid.UUID) -> bool:
    """Delete invoice"""
    invoice = get_invoice(db, invoice_id)
    if invoice:
        db.delete(invoice)
        db.commit()
        return True
    return False

# ============================================
# Legal Query CRUD Operations
# ============================================

def create_legal_query(
    db: Session,
    user_id: uuid.UUID,
    query_text: str,
    response_text: Optional[str] = None,
    risk_level: Optional[str] = None,
    relevant_sections: Optional[Dict] = None
) -> LegalQuery:
    """Create legal query record"""
    query = LegalQuery(
        user_id=user_id,
        query_text=query_text,
        response_text=response_text,
        risk_level=risk_level,
        relevant_sections=relevant_sections
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query

def get_legal_query(db: Session, query_id: uuid.UUID) -> Optional[LegalQuery]:
    """Get legal query by ID"""
    return db.query(LegalQuery).filter(LegalQuery.id == query_id).first()

def get_user_legal_queries(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0
) -> List[LegalQuery]:
    """Get user's legal queries"""
    return db.query(LegalQuery).filter(
        LegalQuery.user_id == user_id
    ).order_by(desc(LegalQuery.created_at)).limit(limit).offset(offset).all()

# ============================================
# Subsidy Application CRUD Operations
# ============================================

def create_subsidy_application(
    db: Session,
    user_id: uuid.UUID,
    scheme_name: str,
    scheme_description: Optional[str] = None,
    eligibility_status: Optional[str] = None,
    application_status: str = 'draft',
    applied_date: Optional[date] = None,
    scheme_data: Optional[Dict] = None
) -> SubsidyApplication:
    """Create subsidy application"""
    application = SubsidyApplication(
        user_id=user_id,
        scheme_name=scheme_name,
        scheme_description=scheme_description,
        eligibility_status=eligibility_status,
        application_status=application_status,
        applied_date=applied_date,
        scheme_data=scheme_data
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

def get_subsidy_application(db: Session, app_id: uuid.UUID) -> Optional[SubsidyApplication]:
    """Get subsidy application by ID"""
    return db.query(SubsidyApplication).filter(SubsidyApplication.id == app_id).first()

def get_user_subsidy_applications(
    db: Session,
    user_id: uuid.UUID,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[SubsidyApplication]:
    """Get user's subsidy applications"""
    query = db.query(SubsidyApplication).filter(SubsidyApplication.user_id == user_id)
    if status:
        query = query.filter(SubsidyApplication.application_status == status)
    return query.order_by(desc(SubsidyApplication.created_at)).limit(limit).offset(offset).all()

def update_subsidy_application(
    db: Session,
    app_id: uuid.UUID,
    **kwargs
) -> Optional[SubsidyApplication]:
    """Update subsidy application"""
    application = get_subsidy_application(db, app_id)
    if application:
        for key, value in kwargs.items():
            if hasattr(application, key):
                setattr(application, key, value)
        db.commit()
        db.refresh(application)
    return application

# ============================================
# Negotiation CRUD Operations
# ============================================

def create_negotiation(
    db: Session,
    user_id: uuid.UUID,
    vendor_name: str,
    negotiation_type: str,
    email_content: str,
    status: str = 'draft'
) -> Negotiation:
    """Create negotiation record"""
    negotiation = Negotiation(
        user_id=user_id,
        vendor_name=vendor_name,
        negotiation_type=negotiation_type,
        email_content=email_content,
        status=status
    )
    db.add(negotiation)
    db.commit()
    db.refresh(negotiation)
    return negotiation

def get_negotiation(db: Session, negotiation_id: uuid.UUID) -> Optional[Negotiation]:
    """Get negotiation by ID"""
    return db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()

def get_user_negotiations(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0
) -> List[Negotiation]:
    """Get user's negotiations"""
    return db.query(Negotiation).filter(
        Negotiation.user_id == user_id
    ).order_by(desc(Negotiation.created_at)).limit(limit).offset(offset).all()

def update_negotiation(
    db: Session,
    negotiation_id: uuid.UUID,
    **kwargs
) -> Optional[Negotiation]:
    """Update negotiation"""
    negotiation = get_negotiation(db, negotiation_id)
    if negotiation:
        for key, value in kwargs.items():
            if hasattr(negotiation, key):
                setattr(negotiation, key, value)
        db.commit()
        db.refresh(negotiation)
    return negotiation

# ============================================
# Audit Log CRUD Operations
# ============================================

def create_audit_log(
    db: Session,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """Create audit log entry"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_audit_logs(
    db: Session,
    user_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[AuditLog]:
    """Get audit logs with optional filtering"""
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    return query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset).all()

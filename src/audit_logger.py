#!/usr/bin/env python3
"""
Comprehensive Audit Logger for MicroCFO
Logs all user actions with Who, What, When, Where (IP), and How (details)
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session
from src.models import AuditLog
from src.database import get_db_context

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Enumeration of auditable actions"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    
    # Invoice Operations
    INVOICE_UPLOADED = "invoice_uploaded"
    INVOICE_VIEWED = "invoice_viewed"
    INVOICE_UPDATED = "invoice_updated"
    INVOICE_DELETED = "invoice_deleted"
    INVOICE_APPROVED = "invoice_approved"
    INVOICE_REJECTED = "invoice_rejected"
    INVOICE_EXPORTED = "invoice_exported"
    
    # Legal Operations
    LEGAL_QUERY = "legal_query"
    LEGAL_RISK_ASSESSED = "legal_risk_assessed"
    LEGAL_DOCUMENT_VIEWED = "legal_document_viewed"
    
    # Subsidy Operations
    SUBSIDY_SEARCHED = "subsidy_searched"
    SUBSIDY_APPLICATION_CREATED = "subsidy_application_created"
    SUBSIDY_APPLICATION_SUBMITTED = "subsidy_application_submitted"
    SUBSIDY_APPLICATION_UPDATED = "subsidy_application_updated"
    
    # Negotiation Operations
    NEGOTIATION_EMAIL_GENERATED = "negotiation_email_generated"
    NEGOTIATION_EMAIL_SENT = "negotiation_email_sent"
    NEGOTIATION_EMAIL_VIEWED = "negotiation_email_viewed"
    
    # User Profile Operations
    PROFILE_VIEWED = "profile_viewed"
    PROFILE_UPDATED = "profile_updated"
    SETTINGS_CHANGED = "settings_changed"
    
    # Data Export
    DATA_EXPORTED = "data_exported"
    REPORT_GENERATED = "report_generated"
    
    # Administrative
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_DEACTIVATED = "user_deactivated"
    USER_ACTIVATED = "user_activated"
    
    # Security Events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # System Events
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    WEBHOOK_CONFIGURED = "webhook_configured"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """
    Comprehensive audit logger for financial operations
    
    Logs every action with:
    - Who: User ID and email
    - What: Action type and description
    - When: Timestamp with timezone
    - Where: IP address and user agent
    - How: Detailed context and metadata
    """
    
    @staticmethod
    def log(
        action: AuditAction,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        session: Optional[Session] = None
    ) -> Optional[str]:
        """
        Log an audit event
        
        Args:
            action: Type of action performed
            user_id: ID of user who performed action
            user_email: Email of user (for context)
            resource_type: Type of resource affected (invoice, legal_query, etc.)
            resource_id: ID of affected resource
            details: Additional context and metadata
            ip_address: IP address of request
            user_agent: User agent string
            severity: Severity level of event
            session: Database session (creates new if not provided)
            
        Returns:
            Audit log ID if successful, None otherwise
        """
        try:
            # Prepare details with user email
            audit_details = details or {}
            if user_email:
                audit_details['user_email'] = user_email
            if severity != AuditSeverity.INFO:
                audit_details['severity'] = severity.value
            
            # Create audit log entry
            audit_entry = AuditLog(
                user_id=user_id,
                action=action.value,
                resource_type=resource_type,
                resource_id=resource_id,
                details=audit_details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Save to database
            if session:
                session.add(audit_entry)
                session.flush()
                audit_id = str(audit_entry.id)
            else:
                with get_db_context() as db:
                    db.add(audit_entry)
                    db.flush()
                    audit_id = str(audit_entry.id)
            
            # Log to application logger
            log_message = f"AUDIT: {action.value} | User: {user_id or 'anonymous'} | Resource: {resource_type}:{resource_id} | IP: {ip_address}"
            
            if severity == AuditSeverity.CRITICAL:
                logger.critical(log_message)
            elif severity == AuditSeverity.ERROR:
                logger.error(log_message)
            elif severity == AuditSeverity.WARNING:
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            return None
    
    @staticmethod
    def log_invoice_action(
        action: AuditAction,
        invoice_id: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """
        Log invoice-related action
        
        Args:
            action: Invoice action type
            invoice_id: Invoice ID
            user_id: User ID
            user_email: User email
            details: Additional details (vendor, amount, etc.)
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            Audit log ID
        """
        return AuditLogger.log(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="invoice",
            resource_id=invoice_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_legal_action(
        action: AuditAction,
        query_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """Log legal compliance action"""
        return AuditLogger.log(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="legal_query",
            resource_id=query_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_subsidy_action(
        action: AuditAction,
        application_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """Log subsidy-related action"""
        return AuditLogger.log(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="subsidy_application",
            resource_id=application_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_negotiation_action(
        action: AuditAction,
        negotiation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """Log negotiation-related action"""
        return AuditLogger.log(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="negotiation",
            resource_id=negotiation_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_auth_action(
        action: AuditAction,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO
    ) -> Optional[str]:
        """Log authentication-related action"""
        return AuditLogger.log(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="authentication",
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity
        )
    
    @staticmethod
    def log_security_event(
        action: AuditAction,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.WARNING
    ) -> Optional[str]:
        """Log security-related event"""
        return AuditLogger.log(
            action=action,
            user_id=user_id,
            resource_type="security",
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity
        )
    
    @staticmethod
    def get_user_activity(
        user_id: str,
        limit: int = 100,
        action_filter: Optional[str] = None
    ) -> list:
        """
        Get recent activity for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of records
            action_filter: Filter by action type
            
        Returns:
            List of audit log entries
        """
        try:
            with get_db_context() as db:
                query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
                
                if action_filter:
                    query = query.filter(AuditLog.action == action_filter)
                
                logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        'id': str(log.id),
                        'action': log.action,
                        'resource_type': log.resource_type,
                        'resource_id': str(log.resource_id) if log.resource_id else None,
                        'details': log.details,
                        'ip_address': log.ip_address,
                        'created_at': log.created_at.isoformat()
                    }
                    for log in logs
                ]
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return []
    
    @staticmethod
    def get_resource_history(
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> list:
        """
        Get audit history for a specific resource
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            limit: Maximum number of records
            
        Returns:
            List of audit log entries
        """
        try:
            with get_db_context() as db:
                logs = db.query(AuditLog).filter(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id
                ).order_by(AuditLog.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        'id': str(log.id),
                        'action': log.action,
                        'user_id': str(log.user_id) if log.user_id else None,
                        'details': log.details,
                        'ip_address': log.ip_address,
                        'created_at': log.created_at.isoformat()
                    }
                    for log in logs
                ]
        except Exception as e:
            logger.error(f"Failed to get resource history: {e}")
            return []


# Convenience functions for common operations
def log_invoice_upload(invoice_id: str, user_id: str, user_email: str, 
                       vendor: str, amount: float, ip_address: str, user_agent: str):
    """Log invoice upload with details"""
    return AuditLogger.log_invoice_action(
        action=AuditAction.INVOICE_UPLOADED,
        invoice_id=invoice_id,
        user_id=user_id,
        user_email=user_email,
        details={
            'vendor_name': vendor,
            'total_amount': amount,
            'action_description': f'Uploaded invoice from {vendor} for ₹{amount:,.2f}'
        },
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_invoice_approval(invoice_id: str, invoice_number: str, user_id: str, 
                        user_email: str, ip_address: str, user_agent: str):
    """Log invoice approval"""
    return AuditLogger.log_invoice_action(
        action=AuditAction.INVOICE_APPROVED,
        invoice_id=invoice_id,
        user_id=user_id,
        user_email=user_email,
        details={
            'invoice_number': invoice_number,
            'action_description': f'Approved Invoice #{invoice_number}'
        },
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_failed_login(email: str, ip_address: str, user_agent: str, reason: str):
    """Log failed login attempt"""
    return AuditLogger.log_auth_action(
        action=AuditAction.LOGIN_FAILED,
        user_email=email,
        details={
            'reason': reason,
            'action_description': f'Failed login attempt for {email}'
        },
        ip_address=ip_address,
        user_agent=user_agent,
        severity=AuditSeverity.WARNING
    )


if __name__ == "__main__":
    # Test audit logger
    print("Testing audit logger...")
    
    # Test invoice upload log
    audit_id = log_invoice_upload(
        invoice_id="test-invoice-123",
        user_id="test-user-456",
        user_email="test@example.com",
        vendor="Acme Corp",
        amount=15000.00,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0"
    )
    
    if audit_id:
        print(f"✅ Audit log created: {audit_id}")
    else:
        print("❌ Failed to create audit log")

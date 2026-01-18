# 📋 Audit Trail Quick Reference

## Quick Start

```bash
# Audit is enabled by default
# Set in .env if you want to disable:
AUDIT_ENABLED=true
```

## What Gets Logged

Every API request automatically logs:
- **Who**: User ID + Email
- **What**: Action type (invoice_uploaded, etc.)
- **When**: Timestamp (automatic)
- **Where**: IP address
- **How**: Request details, status code, duration

## Common Actions

```python
from audit_logger import AuditLogger, AuditAction

# Log invoice approval
AuditLogger.log_invoice_action(
    action=AuditAction.INVOICE_APPROVED,
    invoice_id="inv-123",
    user_id="user-456",
    user_email="user@example.com",
    details={'invoice_number': 'INV-001'},
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# Log failed login
from audit_logger import log_failed_login
log_failed_login(
    email="user@example.com",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    reason="Invalid password"
)
```

## API Endpoints

```bash
# List logs
GET /api/v1/audit/logs?page=1&user_id=user-123

# User activity
GET /api/v1/audit/user/{user_id}/activity

# Resource history
GET /api/v1/audit/resource/invoice/{invoice_id}/history

# Statistics
GET /api/v1/audit/stats?days=30

# Export
GET /api/v1/audit/export?format=csv
```

## Query Examples

```python
# Get user activity
from audit_logger import AuditLogger

activity = AuditLogger.get_user_activity(
    user_id="user-123",
    limit=100
)

# Get resource history
history = AuditLogger.get_resource_history(
    resource_type="invoice",
    resource_id="inv-123"
)
```

## SQL Queries

```sql
-- All actions by user
SELECT * FROM audit_logs 
WHERE user_id = 'user-123' 
ORDER BY created_at DESC;

-- Failed logins
SELECT * FROM audit_logs 
WHERE action = 'login_failed' 
  AND created_at > NOW() - INTERVAL '24 hours';

-- Resource history
SELECT * FROM audit_logs 
WHERE resource_type = 'invoice' 
  AND resource_id = 'inv-123'
ORDER BY created_at DESC;
```

## Action Types

```
Authentication: login, logout, login_failed
Invoices: invoice_uploaded, invoice_approved, invoice_rejected
Legal: legal_query, legal_risk_assessed
Subsidy: subsidy_searched, subsidy_application_created
Negotiation: negotiation_email_generated
Security: unauthorized_access, permission_denied
```

## Severity Levels

- **INFO**: Normal operations
- **WARNING**: Failed auth, permission denied
- **ERROR**: System errors
- **CRITICAL**: Security breaches

## Compliance

✅ SOX - Financial transaction audit trail
✅ GDPR - Right to access
✅ HIPAA - Access logging
✅ PCI DSS - Requirement 10

## Documentation

- **Full Guide**: AUDIT_TRAIL_IMPLEMENTATION.md
- **This File**: AUDIT_TRAIL_QUICK_REFERENCE.md

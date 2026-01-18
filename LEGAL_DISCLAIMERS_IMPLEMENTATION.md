# Legal Disclaimers & Guardrails Implementation

## Overview

This document describes the implementation of legal disclaimers and guardrails for MicroCFO to ensure users understand the limitations of AI assistance and prevent potentially harmful automated actions.

## Core Components

### 1. Legal Disclaimers System (`legal_disclaimers.py`)

Comprehensive disclaimer system with multiple disclaimer types:

#### Main Disclaimer
Prominently displayed disclaimer stating that Micro-CFO is an AI assistant, not a chartered accountant, lawyer, or financial advisor.

#### Specific Disclaimers
- **Legal Advice**: For legal compliance queries (Agent B)
- **Financial Advice**: For financial analysis and recommendations
- **Tax Advice**: For tax-related information
- **Negotiation**: For email drafts (Agent D)
- **Invoice Processing**: For OCR and data extraction (Agent A)
- **Subsidy Application**: For government scheme discovery (Agent C)

#### Short Disclaimers
Concise versions for UI elements and tooltips.

### 2. Guardrails System

Safety rules enforced throughout the application:

#### Negotiator Guardrails
- **Auto-send disabled**: NEVER automatically send emails
- **Draft-only mode**: Always generate drafts for user approval
- **User approval required**: All emails must be reviewed before sending

#### Invoice Processing Guardrails
- **Auto-approve disabled**: Never auto-approve invoices
- **Verification required**: Always require manual verification
- **High amount flagging**: Flag invoices over ₹50,000 threshold

#### Legal Query Guardrails
- **No legal advice**: Never provide legal advice
- **Show disclaimers**: Always display disclaimers
- **Recommend professionals**: Always recommend consulting professionals

## Implementation Details

### Backend Implementation

#### 1. Disclaimer Middleware (`middleware/disclaimer_middleware.py`)

Automatically appends disclaimers to API responses based on endpoint:

```python
ENDPOINT_DISCLAIMERS = {
    "/agents/negotiator": DisclaimerType.NEGOTIATION,
    "/agents/visual-auditor": DisclaimerType.INVOICE_PROCESSING,
    "/agents/legal-sentinel": DisclaimerType.LEGAL_ADVICE,
    "/agents/subsidy-hunter": DisclaimerType.SUBSIDY_APPLICATION,
}
```

**Features:**
- Automatic disclaimer injection for JSON responses
- Endpoint-based disclaimer type detection
- Non-intrusive (doesn't break existing responses)
- Can be disabled via environment variable

#### 2. Router Updates

All agent routers updated to include disclaimers in responses:

**Negotiator Router (`routers/negotiator.py`):**
- Enforces draft-only mode
- Includes negotiation disclaimer in response
- Logs guardrail enforcement
- Added `draft_only` flag to response model

**Visual Auditor Router (`routers/visual_auditor.py`):**
- Includes invoice processing disclaimer
- Warns about OCR accuracy
- Reminds users to verify extracted data

**Response Models Updated:**
```python
class GenerateDraftResponse(BaseModel):
    # ... existing fields ...
    disclaimer: str
    disclaimer_short: str
    draft_only: bool = True  # Always true for negotiator
```

### Frontend Implementation

#### 1. Disclaimer Component (`frontend/src/components/Disclaimer.jsx`)

Modal component for displaying full disclaimer:

**Features:**
- Prominent warning styling with amber colors
- Detailed explanation of limitations
- Checkbox for user acknowledgment
- Cannot be closed without accepting
- Stores acceptance in sessionStorage

**Sections:**
- Main disclaimer statement
- What users should always do
- Important limitations
- Liability disclaimer
- Acceptance checkbox

#### 2. Chat Page Updates (`frontend/src/pages/Chat.jsx`)

**Features:**
- Shows disclaimer modal on first visit
- Persistent disclaimer banner at top
- "View Full Disclaimer" button
- Session-based acceptance tracking
- Welcome message after acceptance

**Disclaimer Banner:**
```jsx
<div className="bg-amber-50 border-b border-amber-200">
  ⚠️ AI Assistant - Not a professional. Always verify outputs.
  <button>View Full Disclaimer</button>
</div>
```

## Usage Examples

### Backend - Getting Disclaimers

```python
from legal_disclaimers import (
    get_negotiator_disclaimer,
    get_invoice_disclaimer,
    get_legal_disclaimer
)

# In router endpoint
disclaimer_data = get_negotiator_disclaimer()
# Returns: {
#   "disclaimer": "Full disclaimer text...",
#   "disclaimer_short": "🤝 Draft only. Review before sending.",
#   "disclaimer_type": "negotiation",
#   "must_acknowledge": True
# }
```

### Backend - Checking Guardrails

```python
from legal_disclaimers import Guardrails, check_can_send_email

# Check if action is allowed
can_send, reason = check_can_send_email()
# Returns: (False, "Automatic email sending is disabled...")

# Check invoice approval
can_approve, reason = Guardrails.check_invoice_approval(
    amount=75000,
    auto_approve=True
)
# Returns: (False, "Invoice amount exceeds threshold...")
```

### Frontend - Showing Disclaimer

```jsx
import Disclaimer from '../components/Disclaimer';

const [showDisclaimer, setShowDisclaimer] = useState(false);

// Check if accepted
useEffect(() => {
  const accepted = sessionStorage.getItem('disclaimer_accepted');
  if (!accepted) {
    setShowDisclaimer(true);
  }
}, []);

// Handle acceptance
const handleDisclaimerAccept = () => {
  sessionStorage.setItem('disclaimer_accepted', 'true');
  setShowDisclaimer(false);
};

// Render
{showDisclaimer && (
  <Disclaimer 
    onAccept={handleDisclaimerAccept}
    onClose={null}  // Don't allow closing without accepting
  />
)}
```

## Configuration

### Environment Variables

```bash
# Enable/disable disclaimer middleware
DISCLAIMER_ENABLED=true  # Default: true

# Enable/disable audit logging
AUDIT_ENABLED=true  # Default: true
```

### Guardrail Configuration

Guardrails are configured in `legal_disclaimers.py`:

```python
# Negotiator guardrails
NEGOTIATOR_RULES = {
    "auto_send_enabled": False,  # NEVER auto-send emails
    "require_user_approval": True,
    "draft_only": True,
    "show_disclaimer": True,
}

# Invoice processing guardrails
INVOICE_RULES = {
    "auto_approve_enabled": False,
    "require_verification": True,
    "flag_high_amounts": True,
    "high_amount_threshold": 50000,  # ₹50,000
}
```

## Testing

### Test Disclaimers

```bash
# Run disclaimer system test
python legal_disclaimers.py

# Expected output:
# - Main disclaimer text
# - Negotiation disclaimer
# - Guardrails test results
```

### Test API Responses

```bash
# Test negotiator endpoint
curl -X POST http://localhost:8000/api/v1/agents/negotiator/generate-draft \
  -H "Content-Type: application/json" \
  -d '{...}'

# Response should include:
# - disclaimer field
# - disclaimer_short field
# - draft_only: true
```

### Test Frontend

1. Open application in browser
2. Clear sessionStorage: `sessionStorage.clear()`
3. Refresh page
4. Disclaimer modal should appear
5. Cannot proceed without accepting
6. After acceptance, banner remains visible

## Compliance Checklist

- [x] Main disclaimer prominently displayed
- [x] Specific disclaimers for each agent type
- [x] Negotiator NEVER auto-sends emails
- [x] All responses include appropriate disclaimers
- [x] Frontend shows disclaimer on first visit
- [x] Persistent disclaimer banner visible
- [x] Guardrails enforced in backend
- [x] User acceptance tracked
- [x] Professional consultation recommended

## Key Safety Features

### 1. Draft-Only Mode (Negotiator)
- All negotiation emails are drafts only
- User must manually review and send
- System logs guardrail enforcement
- Response includes `draft_only: true` flag

### 2. Verification Required (Invoice Processing)
- OCR results must be verified
- High-amount invoices flagged
- Disclaimers warn about accuracy
- No auto-approval allowed

### 3. Professional Recommendations
- All disclaimers recommend consulting professionals
- Specific recommendations per feature type
- Conservative approach to legal/financial advice
- Clear liability limitations

## Best Practices

### For Developers

1. **Always include disclaimers** in new agent endpoints
2. **Use guardrails** before performing sensitive actions
3. **Log guardrail enforcement** for audit trails
4. **Test disclaimer display** in UI components
5. **Never bypass guardrails** even for convenience

### For Users

1. **Read and understand** the main disclaimer
2. **Verify all AI outputs** with professionals
3. **Review drafts carefully** before sending
4. **Check extracted data** against original documents
5. **Consult experts** for legal/financial decisions

## Troubleshooting

### Disclaimer Not Showing

**Problem:** Disclaimer modal doesn't appear on first visit

**Solution:**
1. Check sessionStorage: `sessionStorage.getItem('disclaimer_accepted')`
2. Clear storage: `sessionStorage.clear()`
3. Refresh page
4. Check browser console for errors

### Disclaimer Not in API Response

**Problem:** API response missing disclaimer fields

**Solution:**
1. Check middleware is enabled: `DISCLAIMER_ENABLED=true`
2. Verify endpoint matches pattern in middleware
3. Check response is JSON with 200 status
4. Review server logs for middleware errors

### Guardrails Not Enforced

**Problem:** System allows prohibited actions

**Solution:**
1. Check guardrail configuration in `legal_disclaimers.py`
2. Verify guardrail checks in router code
3. Review audit logs for enforcement
4. Test with `check_can_send_email()` function

## Future Enhancements

### Planned Features

1. **Database Tracking**: Store disclaimer acceptance in database
2. **Version Control**: Track disclaimer version changes
3. **Periodic Re-acceptance**: Require re-acceptance after updates
4. **Customizable Disclaimers**: Allow customization per organization
5. **Multi-language Support**: Disclaimers in regional languages
6. **Audit Trail**: Log all disclaimer acceptances
7. **Admin Dashboard**: View acceptance rates and compliance

### Potential Improvements

1. **More Granular Guardrails**: Per-user or per-role settings
2. **Risk-based Disclaimers**: Different disclaimers based on risk level
3. **Interactive Tutorials**: Guide users through limitations
4. **Professional Directory**: Link to verified professionals
5. **Compliance Reports**: Generate compliance documentation

## References

### Related Files

- `legal_disclaimers.py` - Core disclaimer and guardrail system
- `middleware/disclaimer_middleware.py` - Automatic disclaimer injection
- `routers/negotiator.py` - Negotiator with draft-only mode
- `routers/visual_auditor.py` - Invoice processing with disclaimers
- `frontend/src/components/Disclaimer.jsx` - Disclaimer modal component
- `frontend/src/pages/Chat.jsx` - Chat page with disclaimer integration

### Related Documentation

- `AUDIT_TRAIL_COMPLETE.md` - Audit trail implementation
- `SECURITY_IMPLEMENTATION_COMPLETE.md` - Security features
- `ENCRYPTION_AND_STORAGE.md` - Data encryption
- `INTEGRATION_COMPLETE.md` - Frontend-backend integration

## Summary

The legal disclaimers and guardrails system ensures MicroCFO operates safely and transparently:

- **Clear Communication**: Users understand AI limitations
- **Safety First**: Guardrails prevent harmful automated actions
- **Professional Guidance**: Always recommends expert consultation
- **Compliance**: Meets legal and ethical requirements
- **User Control**: Users maintain full control over actions

This implementation protects both users and the organization while maintaining a positive user experience.

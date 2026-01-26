# Legal Disclaimers & Guardrails - Quick Reference

## Quick Start

### Backend - Add Disclaimer to Response

```python
from legal_disclaimers import get_negotiator_disclaimer

# In your router endpoint
disclaimer_data = get_negotiator_disclaimer()

response = YourResponse(
    # ... your fields ...
    disclaimer=disclaimer_data["disclaimer"],
    disclaimer_short=disclaimer_data["disclaimer_short"]
)
```

### Backend - Check Guardrails

```python
from legal_disclaimers import check_can_send_email, Guardrails

# Check if email can be sent
can_send, reason = check_can_send_email()
if not can_send:
    logger.info(f"Guardrail enforced: {reason}")

# Check invoice approval
can_approve, reason = Guardrails.check_invoice_approval(
    amount=75000,
    auto_approve=True
)
```

### Frontend - Show Disclaimer

```jsx
import Disclaimer from '../components/Disclaimer';

// In your component
const [showDisclaimer, setShowDisclaimer] = useState(false);

useEffect(() => {
  const accepted = sessionStorage.getItem('disclaimer_accepted');
  if (!accepted) setShowDisclaimer(true);
}, []);

const handleAccept = () => {
  sessionStorage.setItem('disclaimer_accepted', 'true');
  setShowDisclaimer(false);
};

// Render
{showDisclaimer && (
  <Disclaimer onAccept={handleAccept} onClose={null} />
)}
```

## Available Disclaimers

| Type | Function | Use Case |
|------|----------|----------|
| Negotiation | `get_negotiator_disclaimer()` | Agent D - Email drafts |
| Invoice | `get_invoice_disclaimer()` | Agent A - OCR processing |
| Legal | `get_legal_disclaimer()` | Agent B - Legal queries |
| General | `LegalDisclaimers.get_disclaimer(DisclaimerType.GENERAL)` | General use |

## Guardrail Rules

### Negotiator
- ❌ Auto-send emails: **DISABLED**
- ✅ Draft-only mode: **ENABLED**
- ✅ User approval: **REQUIRED**

### Invoice Processing
- ❌ Auto-approve: **DISABLED**
- ✅ Verification: **REQUIRED**
- ⚠️ High amount threshold: **₹50,000**

### Legal Queries
- ❌ Provide legal advice: **DISABLED**
- ✅ Show disclaimer: **ENABLED**
- ✅ Recommend professional: **ENABLED**

## Configuration

```bash
# .env file
DISCLAIMER_ENABLED=true  # Enable disclaimer middleware
AUDIT_ENABLED=true       # Enable audit logging
```

## Testing

```bash
# Test disclaimer system
python legal_disclaimers.py

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/agents/negotiator/generate-draft \
  -H "Content-Type: application/json" \
  -d '{"counterparty_name":"Vendor","amount":10000,...}'
```

## Key Files

- `legal_disclaimers.py` - Core system
- `middleware/disclaimer_middleware.py` - Auto-injection
- `frontend/src/components/Disclaimer.jsx` - UI component
- `routers/negotiator.py` - Example implementation

## Common Issues

### Disclaimer Not Showing
```javascript
// Clear session storage
sessionStorage.clear();
// Refresh page
```

### Guardrail Not Working
```python
# Check configuration
from legal_disclaimers import Guardrails
print(Guardrails.NEGOTIATOR_RULES)
```

## Main Disclaimer Text

> ⚠️ **IMPORTANT DISCLAIMER**
> 
> Micro-CFO is an AI assistant, not a chartered accountant, lawyer, or financial advisor.
> 
> All outputs must be verified by a qualified professional before taking any action.

## Remember

1. ✅ Always include disclaimers in responses
2. ✅ Check guardrails before sensitive actions
3. ✅ Log guardrail enforcement
4. ✅ Test disclaimer display
5. ❌ Never bypass guardrails

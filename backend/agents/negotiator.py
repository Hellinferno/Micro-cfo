"""
Negotiator Agent - Agent D
Generates negotiation emails and strategies
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class NegotiationRequest(BaseModel):
    invoice_data: Dict[str, Any]
    negotiation_context: str
    vendor_relationship: Optional[str] = "neutral"  # neutral, good, strained
    tone: Optional[str] = "professional"  # professional, firm, polite


class EmailDraft(BaseModel):
    subject: str
    body: str
    strategy_explanation: str


class Negotiator:
    """
    Agent D: Negotiator
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    @property
    def is_available(self) -> bool:
        return self.model is not None
    
    async def generate_email(self, request: NegotiationRequest) -> EmailDraft:
        """Generate a negotiation email based on invoice and context"""
        
        if not self.is_available:
            return self._mock_email(request)
        
        prompt = self._get_prompt(request)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"Negotiator error: {e}")
            return self._mock_email(request)
    
    def _get_prompt(self, request: NegotiationRequest) -> str:
        invoice = request.invoice_data
        
        return f"""You are an expert financial negotiator for an MSME. 
Draft a negotiation email to a vendor based on the following context.

**Vendor Details:**
- Name: {invoice.get('vendor_name', 'Vendor')}
- Invoice Amount: {invoice.get('total_amount', 'N/A')}
- Due Date: {invoice.get('due_date', 'N/A')}

**Context/Issue:**
{request.negotiation_context}

**Relationship:** {request.vendor_relationship}
**Desired Tone:** {request.tone}

**Output Requirement (JSON ONLY):**
{{
  "subject": "Email Subject Line",
  "body": "Full email body text...",
  "strategy_explanation": "Brief explanation of why this approach works (1-2 sentences)"
}}
"""

    def _parse_response(self, response_text: str) -> EmailDraft:
        import json
        try:
            text = response_text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            return EmailDraft(**data)
        except Exception as e:
            print(f"Parse error: {e}")
            return self._mock_email_response("Error parsing AI response", "Please try again.")

    def _mock_email(self, request: NegotiationRequest) -> EmailDraft:
        """Return a mock email when AI is unavailable"""
        return EmailDraft(
            subject=f"Regarding Invoice Payment - {request.invoice_data.get('invoice_number', 'PENDING')}",
            body=f"""Dear {request.invoice_data.get('vendor_name', 'Vendor Name')},

I hope this email finds you well.

{request.negotiation_context}

We value our relationship and request your understanding in this matter.

Best regards,
[Your Name]""",
            strategy_explanation="This is a mock response because the AI service is unavailable."
        )

    def _mock_email_response(self, subject, body) -> EmailDraft:
         return EmailDraft(
            subject=subject,
            body=body,
            strategy_explanation="Fallback response."
        )

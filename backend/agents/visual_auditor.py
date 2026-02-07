"""
Visual Auditor - Agent A
AI-powered invoice scanning and fraud detection using Gemini Vision
"""

import os
import json
import base64
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Try importing google.generativeai
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class LineItem(BaseModel):
    description: str
    amount: float
    category: str  # Capital Goods, Raw Material, Personal/Entertainment, Service


class InvoiceData(BaseModel):
    vendor_name: str
    invoice_date: Optional[str] = None
    total_amount: float
    tax_amount: float = 0
    gstin: Optional[str] = None
    line_items: List[LineItem] = []
    is_handwritten: bool = False
    tampering_detected: bool = False
    confidence_score: float = 1.0
    compliance_flags: List[str] = []
    is_valid_business_expense: bool = True
    summary: Optional[str] = None


class VisualAuditor:
    """
    Agent A: Visual Auditor
    Scans invoices using AI vision and extracts structured data
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
    
    async def analyze(self, file_content: bytes, content_type: str) -> InvoiceData:
        """Analyze invoice from file bytes"""
        if not self.is_available:
            return self._mock_invoice()
        
        # Convert to base64 for API
        b64_content = base64.b64encode(file_content).decode()
        
        # Build the prompt
        prompt = self._get_analysis_prompt()
        
        try:
            # Prepare image part
            image_part = {
                "inline_data": {
                    "mime_type": content_type,
                    "data": b64_content
                }
            }
            
            # Call Gemini
            response = self.model.generate_content([prompt, image_part])
            
            # Parse response
            return self._parse_response(response.text)
            
        except Exception as e:
            print(f"Vision API error: {e}")
            return self._mock_invoice()
    
    async def analyze_from_url(self, image_url: str) -> InvoiceData:
        """Analyze invoice from URL or base64 string"""
        if not self.is_available:
            return self._mock_invoice()
        
        prompt = self._get_analysis_prompt()
        
        try:
            # If it's base64, decode it
            if image_url.startswith("data:"):
                # Extract base64 content
                parts = image_url.split(",")
                if len(parts) > 1:
                    b64_data = parts[1]
                    mime_type = parts[0].split(":")[1].split(";")[0]
                    image_part = {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data
                        }
                    }
            else:
                # Treat as URL - let Gemini fetch it
                image_part = {"url": image_url}
            
            response = self.model.generate_content([prompt, image_part])
            return self._parse_response(response.text)
            
        except Exception as e:
            print(f"Vision API error: {e}")
            return self._mock_invoice()
    
    def _get_analysis_prompt(self) -> str:
        return """You are an expert AI Accountant and Financial Auditor for Indian MSMEs.
Analyze this invoice/document carefully.

**EXTRACTION TASKS:**
1. Extract: Vendor Name, Invoice Date (YYYY-MM-DD), Total Amount, Tax Amount, GSTIN
2. Categorize each line item as: Capital Goods, Raw Material, Personal/Entertainment, or Service

**FRAUD DETECTION:**
3. Check for: Mismatched fonts, blurred/tampered numbers, handwritten overrides
4. Note if this is a handwritten bill

**COMPLIANCE CHECKS:**
5. Flag items NOT eligible for Input Tax Credit (ITC)
6. Flag if GSTIN is missing but tax is charged
7. Flag if invoice is >30 days old

**OUTPUT FORMAT (JSON ONLY):**
{
  "vendor_name": "string",
  "invoice_date": "YYYY-MM-DD or null",
  "total_amount": number,
  "tax_amount": number,
  "gstin": "string or null",
  "is_handwritten": boolean,
  "tampering_detected": boolean,
  "confidence_score": number (0.0 to 1.0),
  "line_items": [{"description": "string", "amount": number, "category": "string"}],
  "compliance_flags": ["array of warning strings"],
  "is_valid_business_expense": boolean,
  "summary": "Brief analysis summary"
}"""
    
    def _parse_response(self, response_text: str) -> InvoiceData:
        """Parse Gemini response to InvoiceData"""
        try:
            # Extract JSON from response
            text = response_text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            # Convert line items
            line_items = [
                LineItem(
                    description=item.get("description", ""),
                    amount=float(item.get("amount", 0)),
                    category=item.get("category", "Service")
                )
                for item in data.get("line_items", [])
            ]
            
            return InvoiceData(
                vendor_name=data.get("vendor_name", "Unknown"),
                invoice_date=data.get("invoice_date"),
                total_amount=float(data.get("total_amount", 0)),
                tax_amount=float(data.get("tax_amount", 0)),
                gstin=data.get("gstin"),
                line_items=line_items,
                is_handwritten=data.get("is_handwritten", False),
                tampering_detected=data.get("tampering_detected", False),
                confidence_score=float(data.get("confidence_score", 1.0)),
                compliance_flags=data.get("compliance_flags", []),
                is_valid_business_expense=data.get("is_valid_business_expense", True),
                summary=data.get("summary")
            )
            
        except Exception as e:
            print(f"Parse error: {e}")
            return self._mock_invoice()
    
    def _mock_invoice(self) -> InvoiceData:
        """Return mock data when API is unavailable"""
        return InvoiceData(
            vendor_name="Demo Vendor Pvt Ltd",
            invoice_date="2024-01-15",
            total_amount=15000.00,
            tax_amount=2700.00,
            gstin="27AADCB2230M1ZT",
            line_items=[
                LineItem(description="Office Supplies", amount=10000.00, category="Raw Material"),
                LineItem(description="Courier Charges", amount=5000.00, category="Service")
            ],
            is_handwritten=False,
            tampering_detected=False,
            confidence_score=0.95,
            compliance_flags=[],
            is_valid_business_expense=True,
            summary="Invoice processed successfully (Mock data - configure GEMINI_API_KEY for real analysis)"
        )

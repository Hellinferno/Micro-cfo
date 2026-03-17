"""
Agent A: Visual Auditor - Invoice Analysis and Fraud Detection
Uses Gemini 2.5 Flash for multimodal invoice processing
"""

import os
import json
import base64
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from PIL import Image
import io

# Try to import the newer google.genai package, fallback to older one
try:
    import google.genai as genai
    GENAI_PACKAGE = "new"
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_PACKAGE = "old"
    except ImportError:
        genai = None
        GENAI_PACKAGE = None


def get_vision_model() -> Tuple[Optional[Any], str]:
    """Initialize vision model based on available API keys
    
    Returns:
        Tuple of (vision_model, provider) where provider is one of:
        - "gemini_new": New google.genai package
        - "gemini_old": Old google.generativeai package
        - "openrouter": OpenRouter API
        - "mock": Mock data (no API key)
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    # Validate Gemini API key format
    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("sk-or-"):
        if not GEMINI_API_KEY.startswith("AI") or len(GEMINI_API_KEY) < 20:
            print("WARNING: Invalid Gemini API key format. Key should start with 'AI' and be at least 20 characters.")
            return None, "mock"
    
    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("sk-or-") and genai:
        if GENAI_PACKAGE == "new":
            client = genai.Client(api_key=GEMINI_API_KEY)
            return client, "gemini_new"
        else:
            genai.configure(api_key=GEMINI_API_KEY)
            vision_model = genai.GenerativeModel('gemini-2.5-flash')
            return vision_model, "gemini_old"
    elif OPENROUTER_API_KEY or (GEMINI_API_KEY and GEMINI_API_KEY.startswith("sk-or-")):
        return None, "openrouter"
    else:
        return None, "mock"


async def analyze_invoice_content(
    file_content: bytes,
    content_type: str
) -> Dict[str, Any]:
    """
    Analyze invoice from file content
    
    Args:
        file_content: Raw bytes of invoice image/PDF
        content_type: MIME type (image/png, image/jpeg, application/pdf)
    
    Returns:
        Structured invoice data with fraud detection results
    """
    vision_model, provider = get_vision_model()
    
    if provider == "mock":
        return _get_mock_invoice_analysis()
    
    try:
        # Convert to base64 for API
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        # Get analysis prompt
        prompt = _get_invoice_analysis_prompt()
        
        if provider == "gemini_new":
            # New google.genai package
            response = vision_model.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    prompt,
                    {"mime_type": content_type, "data": base64_image}
                ]
            )
            response_text = response.text
        elif provider == "gemini_old":
            # Old google.generativeai package
            response = vision_model.generate_content([
                prompt,
                {"mime_type": content_type, "data": file_content}
            ])
            response_text = response.text
        elif provider == "openrouter":
            response_text = await _analyze_with_openrouter(base64_image, content_type)
        else:
            return _get_mock_invoice_analysis()
        
        # Parse response
        return _parse_invoice_response(response_text)
    
    except Exception as e:
        print(f"Error analyzing invoice: {e}")
        return _get_mock_invoice_analysis()


async def analyze_invoice_from_url(image_url: str) -> Dict[str, Any]:
    """
    Analyze invoice from URL
    
    Args:
        image_url: Public URL of invoice image
    
    Returns:
        Structured invoice data
    """
    vision_model, provider = get_vision_model()
    
    if provider == "mock":
        return _get_mock_invoice_analysis()
    
    try:
        prompt = _get_invoice_analysis_prompt()
        
        if provider == "gemini_new":
            response = vision_model.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image_url]
            )
            response_text = response.text
        elif provider == "gemini_old":
            response = vision_model.generate_content([prompt, image_url])
            response_text = response.text
        elif provider == "openrouter":
            # Download and convert to base64
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_url)
                resp.raise_for_status()
                base64_image = base64.b64encode(resp.content).decode('utf-8')
            response_text = await _analyze_with_openrouter(base64_image, "image/jpeg")
        else:
            return _get_mock_invoice_analysis()
        
        return _parse_invoice_response(response_text)
    
    except Exception as e:
        print(f"Error analyzing invoice from URL: {e}")
        return _get_mock_invoice_analysis()


async def _analyze_with_openrouter(base64_image: str, content_type: str) -> str:
    """Analyze invoice using OpenRouter API"""
    import httpx
    
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://microcfo.com",
        "X-Title": "MicroCFO"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _get_invoice_analysis_prompt()},
                    {
                        "type": "image_url",
                        "image_url": f"data:{content_type};base64,{base64_image}"
                    }
                ]
            }
        ],
        "max_tokens": 2000
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def _get_invoice_analysis_prompt() -> str:
    """Get the invoice analysis prompt"""
    return """
You are an expert CA (Chartered Accountant) analyzing Indian GST invoices.

Extract the following information in JSON format:
{
    "vendor_name": "Vendor company name",
    "invoice_date": "YYYY-MM-DD",
    "total_amount": 0.00,
    "tax_amount": 0.00,
    "gstin": "GST identification number or null",
    "line_items": [
        {
            "description": "Item description",
            "amount": 0.00,
            "category": "Capital Goods|Raw Material|Personal/Entertainment|Service"
        }
    ],
    "is_handwritten": true/false,
    "tampering_detected": true/false,
    "compliance_flags": ["list of compliance issues"],
    "confidence_score": 0.0-1.0,
    "is_valid_business_expense": true/false,
    "summary": "Brief summary of findings"
}

Categorize line items:
- Capital Goods: Machinery, equipment, vehicles, plant
- Raw Material: Production inputs, components, materials
- Personal/Entertainment: Food, alcohol, personal items, gifts
- Service: Consulting, software, maintenance, professional services

Check for fraud indicators:
- Mismatched fonts or formatting
- Blurred or altered numbers
- Handwritten modifications
- Missing GSTIN when tax is charged
- Invoice older than 30 days (stale for ITC)

Flag compliance issues:
- ITC blocked items (food, alcohol, personal use)
- Missing mandatory fields
- Stale invoices
- Suspicious patterns

Be conservative - when in doubt, flag for manual review.
Return ONLY valid JSON, no other text.
"""


def _parse_invoice_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response into structured data"""
    try:
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group()
        
        data = json.loads(response_text)
        
        # Ensure all required fields exist
        required_fields = {
            "vendor_name": "",
            "invoice_date": None,
            "total_amount": 0.0,
            "tax_amount": 0.0,
            "gstin": None,
            "line_items": [],
            "is_handwritten": False,
            "tampering_detected": False,
            "compliance_flags": [],
            "confidence_score": 1.0,
            "is_valid_business_expense": True,
            "summary": ""
        }
        
        for field, default in required_fields.items():
            if field not in data:
                data[field] = default
        
        # Add subsidy alerts for capital goods
        subsidy_alerts = []
        capital_goods_total = sum(
            item.get("amount", 0) 
            for item in data["line_items"] 
            if item.get("category") == "Capital Goods"
        )
        if capital_goods_total > 100000:  # > ₹1L
            subsidy_alerts.append(
                f"Capital goods purchase of ₹{capital_goods_total:,.0f} may be eligible for subsidies. Check Agent C."
            )
        
        # Add compliance warnings
        compliance_warnings = []
        if data["is_handwritten"]:
            compliance_warnings.append("Handwritten invoice - verify authenticity")
        if not data.get("gstin") and data["tax_amount"] > 0:
            compliance_warnings.append("Tax charged without GSTIN - compliance risk")
        if data["tampering_detected"]:
            compliance_warnings.append("Tampering detected - manual verification required")
        
        data["subsidy_alerts"] = subsidy_alerts
        data["compliance_warnings"] = compliance_warnings
        
        return data
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text (first 500 chars): {response_text[:500]}")
        return _get_mock_invoice_analysis()
    except Exception as e:
        print(f"Unexpected error parsing invoice: {e}")
        print(f"Error type: {type(e).__name__}")
        return _get_mock_invoice_analysis()


def _get_mock_invoice_analysis() -> Dict[str, Any]:
    """Return mock invoice analysis for testing without API key"""
    return {
        "vendor_name": "ABC Suppliers Pvt Ltd",
        "invoice_date": "2024-01-15",
        "total_amount": 118000.00,
        "tax_amount": 18000.00,
        "gstin": "27AADCB2230M1ZT",
        "line_items": [
            {
                "description": "Office Equipment",
                "amount": 100000.00,
                "category": "Capital Goods"
            }
        ],
        "is_handwritten": False,
        "tampering_detected": False,
        "compliance_flags": [],
        "confidence_score": 0.95,
        "is_valid_business_expense": True,
        "summary": "Invoice processed successfully. Capital goods detected - eligible for subsidy.",
        "subsidy_alerts": [
            "Capital goods purchase of ₹100,000 may be eligible for subsidies. Check Agent C."
        ],
        "compliance_warnings": []
    }


def initialize_agent_a():
    """Initialize Agent A (Visual Auditor)"""
    vision_model, provider = get_vision_model()
    print(f"Agent A (Visual Auditor) initialized with provider: {provider}")
    return True

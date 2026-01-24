#!/usr/bin/env python3
"""
MicroCFO MCP Server - Complete Implementation with Agent A Visual Auditor
A lightweight MCP server for AI-powered financial operations with Gemini 1.5 Flash
"""

import os
import json
import base64
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from fastmcp import FastMCP
import requests
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

# Initialize the MCP server
mcp = FastMCP("MicroCFO")

# Configure Vision API - Support both Gemini and OpenRouter
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize vision model
vision_model = None
vision_provider = None

if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("sk-or-") and genai:
    # Use Google Gemini
    if GENAI_PACKAGE == "new":
        # New google.genai package
        client = genai.Client(api_key=GEMINI_API_KEY)
        vision_model = client
        vision_provider = "gemini_new"
        print("Using Google Gemini 1.5 Flash (new SDK) for vision processing")
    else:
        # Old google.generativeai package
        genai.configure(api_key=GEMINI_API_KEY)
        vision_model = genai.GenerativeModel('gemini-2.5-flash')
        vision_provider = "gemini_old"
        print("Using Google Gemini 2.5 Flash (legacy SDK) for vision processing")
elif OPENROUTER_API_KEY or (GEMINI_API_KEY and GEMINI_API_KEY.startswith("sk-or-")):
    # Use OpenRouter (supports GPT-4V, Claude 3, etc.)
    api_key = OPENROUTER_API_KEY or GEMINI_API_KEY
    vision_provider = "openrouter"
    print("Using OpenRouter for vision processing")
else:
    print("No vision API key found. Agent A will use mock data.")
    print("Set GEMINI_API_KEY (Google) or OPENROUTER_API_KEY (OpenRouter)")

# Phase 2: Enhanced Pydantic Models

class LineItem(BaseModel):
    """Individual line item with category classification"""
    description: str
    amount: float
    category: str  # 'Capital Goods', 'Raw Material', 'Personal/Entertainment', 'Service'

class Invoice(BaseModel):
    """Enhanced schema for invoice data extraction (Agent A)"""
    vendor_name: str
    invoice_date: str
    total_amount: float
    tax_amount: float
    line_items: List[LineItem]
    gstin: Optional[str] = None
    # New auditor fields
    is_handwritten: bool = False
    tampering_detected: bool = False
    compliance_flags: List[str] = []
    confidence_score: float = 1.0

class RiskLevel(str, Enum):
    """Risk levels for compliance checks"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class LegalRisk(BaseModel):
    """Schema for compliance risk assessment (Agent B)"""
    risk_level: RiskLevel
    relevant_section: str
    compliant_action: str

class UserProfile(BaseModel):
    """User profile for context"""
    business_name: str
    turnover_tier: str  # e.g., "< 5Cr"
    gst_registration_type: str  # e.g., "Regular" or "Composition"
    industry_code: str

# Phase 4: Resources - Long-term Memory
@mcp.resource("microcfo://data/profile")
def get_user_profile() -> str:
    """Get user profile context"""
    # Mock profile for testing
    profile = UserProfile(
        business_name="Sample Business Ltd",
        turnover_tier="< 5Cr",
        gst_registration_type="Regular",
        industry_code="Textile"
    )
    return profile.model_dump_json(indent=2)

# Phase 3: Tool Endpoints

@mcp.tool()
def scan_invoice_document(image_url: str, use_mock: bool = False) -> Invoice:
    """
    Tool 1: The Visual Auditor (Agent A)
    Scans invoice document using Gemini 1.5 Flash and extracts structured data
    Enhanced with fraud detection, compliance checking, and proactive subsidy triggers
    
    Args:
        image_url: URL or base64 encoded image of the invoice (or text/markdown content)
        use_mock: If True, returns mock data for testing (default: False)
    """
    
    # Use mock data if requested or if no vision API is configured
    if use_mock or not vision_provider:
        return _get_mock_invoice()
    
    try:
        # Step 1: Load the content (Image or Text)
        content_obj, is_text = _load_content(image_url)
        
        # Step 2: The Auditor Prompt - Not just OCR, but intelligent analysis
        auditor_prompt = """You are a strict Financial Auditor for an Indian MSME. Analyze this invoice image.

**EXTRACTION TASKS:**
1. Extract: Vendor Name, Invoice Date (YYYY-MM-DD format), Total Amount, Tax Amount, and GSTIN
2. Line Items: For each item, extract description, amount, and categorize into:
   - 'Capital Goods' (machinery, equipment, plant, vehicles)
   - 'Raw Material' (inputs for production)
   - 'Personal/Entertainment' (food, alcohol, tobacco, personal items)
   - 'Service' (consulting, software, maintenance)

**FRAUD DETECTION:**
3. Tampering Check: Look for:
   - Mismatched fonts or font sizes
   - Blurred or pixelated numbers (especially amounts)
   - Handwritten overrides on printed numbers
   - Inconsistent alignment or spacing
   - Signs of digital manipulation
   Set 'tampering_detected' to true if ANY suspicious signs found

4. Handwriting Detection: Is this a handwritten bill? Set 'is_handwritten' accordingly

**COMPLIANCE CHECKS:**
5. ITC Eligibility: Flag items that are NOT eligible for Input Tax Credit:
   - Food, beverages (except for resale)
   - Alcohol, tobacco
   - Personal/entertainment expenses
   - Items for personal use
   Add to 'compliance_flags' array

6. GSTIN Validation: If GSTIN is missing but tax is charged, add "Missing GSTIN" to compliance_flags

7. Date Check: If invoice date is >30 days old, add "Stale Invoice - ITC Risk" to compliance_flags

**OUTPUT FORMAT (JSON):**
{
  "vendor_name": "string",
  "invoice_date": "YYYY-MM-DD",
  "total_amount": number,
  "tax_amount": number,
  "gstin": "string or null",
  "is_handwritten": boolean,
  "tampering_detected": boolean,
  "confidence_score": number (0.0 to 1.0),
  "line_items": [
    {
      "description": "string",
      "amount": number,
      "category": "Capital Goods|Raw Material|Personal/Entertainment|Service"
    }
  ],
  "compliance_flags": ["array of warning strings"]
}

Be conservative in your assessment. When in doubt, flag it."""

        # Step 3: Call Vision API based on provider
        if is_text:
             # Text-only processing
            prompt_parts = [auditor_prompt, f"\n\nINVOICE CONTENT:\n{content_obj}"]
            
            if vision_provider == "gemini_new":
                response = vision_model.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=[{'role': 'user', 'parts': [{'text': p} for p in prompt_parts]}]
                )
                response_text = response.text.strip()
            elif vision_provider == "gemini_old":
                response = vision_model.generate_content(prompt_parts)
                response_text = response.text.strip()
            # fallback for openrouter text
            elif vision_provider == "openrouter":
                 # Implementation for text-only openrouter call if needed
                 pass 

        elif vision_provider == "gemini_new":
            # New google.genai SDK
            response = vision_model.models.generate_content(
                model='gemini-1.5-flash',
                contents=[
                    {'role': 'user', 'parts': [
                        {'text': auditor_prompt},
                        {'inline_data': {
                            'mime_type': 'image/png',
                            'data': _image_to_base64(image)
                        }}
                    ]}
                ]
            )
            response_text = response.text.strip()
        elif vision_provider == "gemini_old":
            # Old google.generativeai SDK
            response = vision_model.generate_content([auditor_prompt, image])
            response_text = response.text.strip()
        elif vision_provider == "openrouter":
            response_text = _call_openrouter_vision(auditor_prompt, image)
        else:
            raise Exception("No vision provider configured")
        
        # Step 4: Parse the response
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        invoice_data = json.loads(response_text)
        
        # Convert to Invoice object
        invoice = Invoice(**invoice_data)
        
        # Step 5: Post-Processing Validations (Python-side safety checks)
        _apply_safety_validations(invoice)
        
        # Step 6: Orchestrator Triggers - Connect to other agents
        _trigger_orchestrator(invoice)
        
        return invoice
        
    except Exception as e:
        print(f"Error in scan_invoice_document: {str(e)}")
        # Fallback to mock data on error
        mock = _get_mock_invoice()
        mock.compliance_flags.append(f"Vision API Error: {str(e)}")
        return mock

def _call_openrouter_vision(prompt: str, image):
    """Call OpenRouter API for vision processing"""
    import httpx
    
    # Convert image to base64
    if hasattr(image, 'save'):
        # PIL Image
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_b64 = base64.b64encode(buffer.getvalue()).decode()
    else:
        # Already base64 or bytes
        if isinstance(image, bytes):
            image_b64 = base64.b64encode(image).decode()
        else:
            image_b64 = str(image)
    
    api_key = OPENROUTER_API_KEY or GEMINI_API_KEY
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use GPT-4V or Claude 3 for vision
    data = {
        "model": "openai/gpt-4o",  # or "anthropic/claude-3-sonnet"
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2000
    }
    
    with httpx.Client() as client:
        response = client.post("https://openrouter.ai/api/v1/chat/completions", 
                             headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]

def _image_to_base64(image):
    """Convert PIL Image to base64 string"""
    if hasattr(image, 'save'):
        # PIL Image
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    else:
        # Already base64 or bytes
        if isinstance(image, bytes):
            return base64.b64encode(image).decode()
        else:
            return str(image)

def _load_content(input_url: str):
    """Load content from URL or base64 string, auto-detecting image or text"""
    # Check for text mime types in data URL
    if input_url.startswith('data:text/markdown') or input_url.startswith('data:text/plain'):
        try:
             # Extract base64 content
            base64_data = input_url.split(',')[1]
            decoded_text = base64.b64decode(base64_data).decode('utf-8')
            return decoded_text, True
        except Exception as e:
            print(f"Error decoding text content: {e}")
            raise
            
    # Fallback to image loading
    return _load_image(input_url), False

def _load_image(image_url: str):
    """Load image from URL or base64 string"""
    if image_url.startswith('data:image'):
        # Base64 encoded image
        base64_data = image_url.split(',')[1]
        image_data = base64.b64decode(base64_data)
        return Image.open(io.BytesIO(image_data))
    elif image_url.startswith('http'):
        # URL
        response = requests.get(image_url)
        return Image.open(io.BytesIO(response.content))
    else:
        # Local file path
        return Image.open(image_url)

def _apply_safety_validations(invoice: Invoice):
    """Apply Python-side validation rules"""
    from datetime import datetime, timedelta
    
    # Validation 1: Missing GSTIN with tax charged
    if not invoice.gstin and invoice.tax_amount > 0:
        if "Missing GSTIN" not in invoice.compliance_flags:
            invoice.compliance_flags.append("Suspicious Vendor - Tax charged without GSTIN")
    
    # Validation 2: Date staleness check (ITC eligibility)
    try:
        invoice_date = datetime.strptime(invoice.invoice_date, "%Y-%m-%d")
        days_old = (datetime.now() - invoice_date).days
        
        if days_old > 30 and "Stale Invoice" not in str(invoice.compliance_flags):
            invoice.compliance_flags.append(f"Stale Invoice ({days_old} days old) - ITC claim may be rejected")
    except:
        pass
    
    # Validation 3: High-risk tampering
    if invoice.tampering_detected:
        invoice.compliance_flags.append("⚠️ CRITICAL: Tampering detected - Manual verification required")
    
    # Validation 4: Handwritten bills (lower reliability)
    if invoice.is_handwritten:
        invoice.compliance_flags.append("Handwritten bill - Verify amounts manually")

def _trigger_orchestrator(invoice: Invoice):
    """Orchestrator logic - Automatically trigger other agents based on invoice content"""
    
    # TRIGGER 1: Agent C (Subsidy Hunter) - Capital Goods Detection
    capital_goods_items = [item for item in invoice.line_items if item.category == "Capital Goods"]
    
    if capital_goods_items:
        total_capex = sum(item.amount for item in capital_goods_items)
        
        # Trigger subsidy search for purchases > ₹1 Lakh
        if total_capex > 100000:
            try:
                profile_data = get_user_profile()
                profile = json.loads(profile_data)
                user_sector = profile.get('industry_code', 'manufacturing')
                
                # Automatically call Agent C
                subsidy_result = find_applicable_subsidies(user_sector, total_capex)
                
                # Add alert to invoice
                alert_item = LineItem(
                    description=f"🎯 SUBSIDY ALERT: {subsidy_result[:150]}...",
                    amount=0.0,
                    category="Alert"
                )
                invoice.line_items.append(alert_item)
                
            except Exception as e:
                print(f"Subsidy trigger error: {e}")
    
    # TRIGGER 2: Agent B (Legal Sentinel) - Non-compliant items
    personal_items = [item for item in invoice.line_items if item.category == "Personal/Entertainment"]
    
    if personal_items:
        try:
            # Automatically check ITC eligibility
            compliance_check = check_compliance_law(
                f"Can I claim Input Tax Credit on {personal_items[0].description}?",
                ""
            )
            
            # Add warning to invoice
            warning = f"⚠️ ITC WARNING: {compliance_check.compliant_action}"
            if warning not in invoice.compliance_flags:
                invoice.compliance_flags.append(warning)
                
        except Exception as e:
            print(f"Compliance trigger error: {e}")

def _get_mock_invoice() -> Invoice:
    """Returns mock invoice data for testing"""
    return Invoice(
        vendor_name="ABC Machinery Pvt Ltd",
        invoice_date="2024-01-15",
        total_amount=590000.0,
        tax_amount=90000.0,
        line_items=[
            LineItem(description="Industrial Loom Machine", amount=500000.0, category="Capital Goods"),
            LineItem(description="Installation & Setup", amount=50000.0, category="Service"),
            LineItem(description="GST @ 18%", amount=90000.0, category="Service")
        ],
        gstin="27AABCU9603R1ZX",
        is_handwritten=False,
        tampering_detected=False,
        compliance_flags=[],
        confidence_score=0.95
    )

@mcp.tool()
def check_compliance_law(query: str, user_context: str = "") -> LegalRisk:
    """
    Tool 2: The Legislative Sentinel (Agent B)
    Structure-aware RAG system for legal compliance
    """
    try:
        from vector_database import LegalVectorDB
        import json
        
        # Step 1: Context Fetching - Get user profile
        profile_data = get_user_profile()
        profile = json.loads(profile_data)
        
        # Extract user turnover (convert to rupees)
        user_turnover = 0
        if "< 5Cr" in profile.get("turnover_tier", ""):
            user_turnover = 40000000  # 4 crores (below 5 crore threshold)
        elif "5-20Cr" in profile.get("turnover_tier", ""):
            user_turnover = 120000000  # 12 crores
        
        # Step 2: Initialize Vector DB and perform hybrid search
        vector_db = LegalVectorDB()
        
        # Perform hybrid search with context filtering
        search_results = vector_db.hybrid_search(
            query=query,
            n_results=5,
            law_type="GST",  # Can be made dynamic based on query
            max_turnover=user_turnover if user_turnover > 0 else None
        )
        
        # Step 3: Context Filter - Remove irrelevant chunks
        relevant_chunks = []
        for result in search_results:
            metadata = result['metadata']
            
            # Check turnover threshold applicability
            if metadata.get('turnover_threshold'):
                try:
                    threshold = float(metadata['turnover_threshold'])
                    if user_turnover > 0 and threshold > user_turnover:
                        # User is exempt from this provision
                        continue
                except ValueError:
                    pass
            
            relevant_chunks.append(result)
        
        # Step 4: Prompt Assembly and Risk Assessment
        if not relevant_chunks:
            return LegalRisk(
                risk_level=RiskLevel.LOW,
                relevant_section="No applicable provisions found",
                compliant_action=(
                    f"Based on your turnover tier ({profile.get('turnover_tier', 'unknown')}), "
                    "you may be exempt from the queried provisions. Consult a CA for confirmation."
                )
            )
        
        # Analyze the most relevant chunk
        top_result = relevant_chunks[0]
        text = top_result['text']
        metadata = top_result['metadata']
        
        # Determine risk level based on content analysis
        risk_level = RiskLevel.LOW
        if any(word in text.lower() for word in ['penalty', 'fine', 'prosecution', 'blocked', 'not available']):
            risk_level = RiskLevel.HIGH
        elif any(word in text.lower() for word in ['provided that', 'conditions', 'restrictions']):
            risk_level = RiskLevel.MEDIUM
        
        # Generate compliant action
        section_ref = f"Section {metadata.get('section_number', 'Unknown')}"
        if metadata.get('law_type'):
            section_ref += f" of {metadata['law_type']} Act"
        
        # Check if user is exempt due to turnover
        compliant_action = ""
        if metadata.get('turnover_threshold'):
            try:
                threshold = float(metadata['turnover_threshold'])
                threshold_cr = threshold / 10000000
                if user_turnover > 0 and user_turnover < threshold:
                    compliant_action = (
                        f"EXEMPT: Your turnover ({profile.get('turnover_tier', 'unknown')}) "
                        f"is below the {threshold_cr} crore threshold. This provision does not apply to you."
                    )
                else:
                    compliant_action = f"APPLICABLE: Your turnover exceeds {threshold_cr} crore threshold. "
            except ValueError:
                pass
        
        if not compliant_action.startswith("EXEMPT"):
            # Generate action based on content
            if 'input tax credit' in text.lower():
                compliant_action += "Ensure proper documentation and eligibility before claiming ITC."
            elif 'filing' in text.lower():
                compliant_action += "File returns within prescribed time limits to avoid penalties."
            else:
                compliant_action += "Review the provision carefully and ensure compliance."
        
        return LegalRisk(
            risk_level=risk_level,
            relevant_section=section_ref,
            compliant_action=compliant_action
        )
    
    except Exception as e:
        # Fallback to simple logic if vector DB is not available
        if "itc" in query.lower() or "input tax credit" in query.lower():
            return LegalRisk(
                risk_level=RiskLevel.MEDIUM,
                relevant_section="Section 17(5) of CGST Act",
                compliant_action="ITC blocked for personal use items. Vector DB not available - using fallback logic."
            )
        else:
            return LegalRisk(
                risk_level=RiskLevel.LOW,
                relevant_section="General Compliance",
                compliant_action=f"Vector DB error: {str(e)}. Please check system setup."
            )

@mcp.tool()
def find_applicable_subsidies(sector: str, capex_amount: float, state: str = None) -> str:
    """
    Tool 3: The Subsidy Hunter (Agent C)
    Enhanced scheme-aware subsidy discovery with benefit calculation
    """
    print(f"DEBUG: find_applicable_subsidies called with sector='{sector}', amount={capex_amount}, state='{state}'")
    
    # Comprehensive scheme database with sector-specific schemes
    SCHEME_DATABASE = {
        "textile": [
            {
                "name": "Technology Upgradation Fund Scheme (TUFS)",
                "benefit": "25% capital subsidy on eligible machinery",
                "max_subsidy": 25000000,
                "eligibility": "MSME textile units, new & expansion projects",
                "link": "https://texmin.nic.in/schemes/technology-upgradation-fund-scheme-tufs",
                "ministry": "Ministry of Textiles"
            },
            {
                "name": "PM MITRA Parks Scheme",
                "benefit": "30% capital subsidy + PLI incentives",
                "max_subsidy": 50000000,
                "eligibility": "Investment > 50 lakhs in PM MITRA parks",
                "link": "https://pmmitra.gov.in",
                "ministry": "Ministry of Textiles"
            },
            {
                "name": "Amended Technology Upgradation Fund Scheme (A-TUFS)",
                "benefit": "15% capital subsidy on technology upgradation",
                "max_subsidy": 20000000,
                "eligibility": "All textile segments including weaving, processing",
                "link": "https://www.txcindia.gov.in/html/atufs.htm",
                "ministry": "Ministry of Textiles"
            }
        ],
        "manufacturing": [
            {
                "name": "Credit Linked Capital Subsidy Scheme (CLCSS)",
                "benefit": "15% capital subsidy on plant & machinery",
                "max_subsidy": 1500000,  # 15 Lakhs
                "eligibility": "MSEs in manufacturing, investment up to Rs 1 Cr",
                "link": "https://msme.gov.in/schemes/clcss",
                "ministry": "Ministry of MSME"
            },
            {
                "name": "Credit Guarantee Fund Scheme (CGS)",
                "benefit": "Collateral-free loans up to Rs 2 Cr",
                "max_subsidy": 20000000,
                "eligibility": "MSMEs with viable business plans",
                "link": "https://www.cgtmse.in",
                "ministry": "Ministry of MSME"
            },
            {
                "name": "Production Linked Incentive (PLI) Scheme",
                "benefit": "4% incentive on incremental sales",
                "max_subsidy": 100000000,
                "eligibility": "Manufacturing units meeting threshold criteria",
                "link": "https://invest.gov.in/pli-schemes/",
                "ministry": "DPIIT"
            }
        ],
        "food_processing": [
            {
                "name": "PM Formalization of Micro Food Processing (PMFME)",
                "benefit": "35% capital subsidy, max Rs 10 lakhs",
                "max_subsidy": 1000000,
                "eligibility": "Micro food processing enterprises",
                "link": "https://pmfme.mofpi.gov.in",
                "ministry": "Ministry of Food Processing"
            },
            {
                "name": "Pradhan Mantri Kisan SAMPADA Yojana",
                "benefit": "35% capital subsidy for cold chains",
                "max_subsidy": 100000000,
                "eligibility": "Food processing, cold chain, mega food parks",
                "link": "https://sampada.mofpi.gov.in",
                "ministry": "Ministry of Food Processing"
            },
            {
                "name": "Operation Greens (TOP to Total)",
                "benefit": "50% subsidy on supply chain infrastructure",
                "max_subsidy": 50000000,
                "eligibility": "Fruits & vegetables processing",
                "link": "https://mofpi.gov.in/schemes/operation-greens",
                "ministry": "Ministry of Food Processing"
            }
        ],
        "agriculture": [
            {
                "name": "Agriculture Infrastructure Fund (AIF)",
                "benefit": "3% interest subvention + credit guarantee",
                "max_subsidy": 20000000,
                "eligibility": "Agri-infrastructure projects",
                "link": "https://agriinfra.dac.gov.in",
                "ministry": "Ministry of Agriculture"
            },
            {
                "name": "Sub-Mission on Agricultural Mechanization (SMAM)",
                "benefit": "40% subsidy on farm machinery",
                "max_subsidy": 5000000,
                "eligibility": "Farmers, FPOs, Custom Hiring Centers",
                "link": "https://agrimachinery.nic.in",
                "ministry": "Ministry of Agriculture"
            },
            {
                "name": "Micro Irrigation Fund (MIF)",
                "benefit": "Interest subvention on micro irrigation",
                "max_subsidy": 10000000,
                "eligibility": "Drip and sprinkler irrigation projects",
                "link": "https://pmksy.gov.in",
                "ministry": "Ministry of Agriculture"
            }
        ],
        "pharma": [
            {
                "name": "PLI Scheme for Pharmaceuticals",
                "benefit": "10% incentive on incremental sales",
                "max_subsidy": 200000000,
                "eligibility": "API and KSM manufacturers",
                "link": "https://pharmaceuticals.gov.in/schemes",
                "ministry": "Department of Pharmaceuticals"
            },
            {
                "name": "Bulk Drug Parks Scheme",
                "benefit": "70% grant for common infrastructure",
                "max_subsidy": 100000000,
                "eligibility": "Units in bulk drug parks",
                "link": "https://pharmaceuticals.gov.in/bulk-drug-parks",
                "ministry": "Department of Pharmaceuticals"
            }
        ],
        "it": [
            {
                "name": "STPI Registration Benefits",
                "benefit": "100% FDI, duty-free imports",
                "max_subsidy": 50000000,
                "eligibility": "Software export units",
                "link": "https://stpi.in",
                "ministry": "MeitY"
            },
            {
                "name": "Digital MSME Scheme",
                "benefit": "Up to 90% subsidy on cloud computing",
                "max_subsidy": 500000,
                "eligibility": "MSMEs for ICT adoption",
                "link": "https://msme.gov.in/digital-msme",
                "ministry": "Ministry of MSME"
            }
        ],
        "technology": [
            {
                "name": "STPI Registration Benefits",
                "benefit": "100% FDI, duty-free imports",
                "max_subsidy": 50000000,
                "eligibility": "Software export units",
                "link": "https://stpi.in",
                "ministry": "MeitY"
            },
            {
                "name": "PLI for IT Hardware",
                "benefit": "4-6% incentive on net incremental sales",
                "max_subsidy": 100000000,
                "eligibility": "Laptops, tablets, servers manufacturing",
                "link": "https://meity.gov.in/schemes",
                "ministry": "MeitY"
            }
        ],
        "services": [
            {
                "name": "MSME Credit Guarantee Scheme",
                "benefit": "Collateral-free loans up to Rs 2 Cr",
                "max_subsidy": 20000000,
                "eligibility": "Service sector MSMEs",
                "link": "https://www.cgtmse.in",
                "ministry": "Ministry of MSME"
            },
            {
                "name": "Skill Development Subsidy",
                "benefit": "75% training cost subsidy",
                "max_subsidy": 1000000,
                "eligibility": "Skill training for employees",
                "link": "https://msde.gov.in/en/schemes-initiatives",
                "ministry": "Ministry of Skill Development"
            }
        ],
        "women_entrepreneur": [
            {
                "name": "Stand Up India Scheme",
                "benefit": "Bank loans between ₹10 Lakh and ₹1 Crore",
                "max_subsidy": 10000000,
                "eligibility": "SC/ST and/or Woman entrepreneur (Greenfield projects)",
                "link": "https://www.standupmitra.in/",
                "ministry": "Ministry of Finance"
            },
            {
                "name": "Pradhan Mantri MUDRA Yojana (Tarun)",
                "benefit": "Collateral-free loans up to ₹10 Lakhs",
                "max_subsidy": 1000000,
                "eligibility": "Non-Corporate Small Business Segment (NCSBS)",
                "link": "https://www.mudra.org.in/",
                "ministry": "Ministry of Finance"
            },
            {
                "name": "Prime Minister's Employment Generation Programme (PMEGP)",
                "benefit": "Up to 35% subsidy (Margin Money) in rural areas",
                "max_subsidy": 5000000,  # Max project cost 50L for mfg
                "eligibility": "New micro-enterprises, special category (Women/SC/ST)",
                "link": "https://www.kviconline.gov.in/pmegpeportal/pmegphome/index.jsp",
                "ministry": "Ministry of MSME"
            }
        ],
        "rural_business": [
            {
                "name": "Prime Minister's Employment Generation Programme (PMEGP)",
                "benefit": "Subsidy: 35% (Rural), 25% (Urban) for Special Category",
                "max_subsidy": 5000000,
                "eligibility": "Any individual above 18 years, new projects",
                "link": "https://www.kviconline.gov.in/pmegpeportal/pmegphome/index.jsp",
                "ministry": "Ministry of MSME"
            },
            {
                "name": "Deendayal Antyodaya Yojana (NRLM)",
                "benefit": "Revolving Fund & Community Investment Support",
                "max_subsidy": 500000,
                "eligibility": "Women SHGs in rural areas",
                "link": "https://aajeevika.gov.in/",
                "ministry": "Ministry of Rural Development"
            },
            {
                "name": "Aspire Scheme (LBI)",
                "benefit": "100% grant for Livelihood Business Incubators",
                "max_subsidy": 10000000,
                "eligibility": "Agencies setting up incubators in rural areas",
                "link": "https://msme.gov.in/sites/default/files/ASPIRE-Scheme-Guidelines.pdf",
                "ministry": "Ministry of MSME"
            }
        ]
    }
    
    # State specific schemes (Major States)
    STATE_SCHEMES = {
        "maharashtra": [
            {
                "name": "Magnet Maharashtra - PSI 2019",
                "benefit": "100% SGST refund + 5% Interest Subsidy",
                "max_subsidy": 50000000,
                "eligibility": "MSMEs and Large units in Maharashtra",
                "link": "https://di.maharashtra.gov.in",
                "ministry": "Govt of Maharashtra"
            },
            {
                "name": "Mukhyamantri Rojgar Nirman Yojana",
                "benefit": "Up to 35% subsidy on project cost",
                "max_subsidy": 2500000,
                "eligibility": "Unemployed youth in Maharashtra",
                "link": "https://cmegp.gov.in",
                "ministry": "Govt of Maharashtra"
            }
        ],
        "gujarat": [
            {
                "name": "Gujarat Industrial Policy 2020",
                "benefit": "Capital subsidy @ 25% + 7% Interest Subsidy",
                "max_subsidy": 3500000,
                "eligibility": "MSMEs in Gujarat",
                "link": "https://ic.gujarat.gov.in",
                "ministry": "Govt of Gujarat"
            }
        ],
        "karnataka": [
            {
                "name": "Karnataka Industrial Policy 2020-25",
                "benefit": "Inv. Promotion Subsidy based on zone (up to 25%)",
                "max_subsidy": 50000000,
                "eligibility": "New enterprises in Karnataka",
                "link": "https://kum.karnataka.gov.in",
                "ministry": "Govt of Karnataka"
            }
        ],
        "tamil_nadu": [
            {
                "name": "TN MSME Policy 2021",
                "benefit": "Capital Subsidy 25% on plant & machinery",
                "max_subsidy": 15000000,
                "eligibility": "New & existing MSMEs in TN",
                "link": "https://msmeonline.tn.gov.in",
                "ministry": "Govt of Tamil Nadu"
            }
        ]
    }
    
    # Get sector-specific schemes
    sector_key = sector.lower().replace(" ", "_").replace("-", "_")
    
    # Check for sector aliases
    sector_aliases = {
        "textiles": "textile",
        "food": "food_processing",
        "agri": "agriculture",
        "pharma": "pharma",
        "pharmaceutical": "pharma",
        "information technology": "it",
        "tech": "technology",
        "service": "services"
    }
    sector_key = sector_aliases.get(sector_key, sector_key)
    
    schemes = SCHEME_DATABASE.get(sector_key)
    
    if not schemes and sector_key != "manufacturing":
        # Try semantic search if SchemeVectorDB is available
        try:
            from scheme_database import SchemeVectorDB
            print(f"DEBUG: Falling back to Semantic Search for '{sector}'")
            scheme_db = SchemeVectorDB()
            
            # Search for eligible schemes using vector search
            eligible_schemes = scheme_db.search_eligible_schemes(
                user_sector=sector,
                user_investment=capex_amount,
                query=f"{sector} subsidy scheme",
                n_results=3
            )
            
            if eligible_schemes:
                schemes = []
                for s in eligible_schemes:
                    schemes.append({
                        "name": s.get('scheme_name', 'Unknown Scheme'),
                        "benefit": s.get('benefit_summary', 'Benefit details in link'),
                        "max_subsidy": s.get('max_benefit', 1000000), 
                        "eligibility": s.get('eligibility', 'Check details'),
                        "link": s.get('url', '#'),
                        "ministry": s.get('ministry', 'Government of India')
                    })
                sector_display = f"{sector.title()} (AI Matched Schemes)"
        except Exception as e:
            print(f"DEBUG: Vector search failed: {e}")
            schemes = None

    if not schemes:
        # Default to manufacturing if sector not found
        schemes = SCHEME_DATABASE["manufacturing"]
        sector_display = f"{sector.title()} (using general Manufacturing schemes)"
    elif 'sector_display' not in locals():
        sector_display = sector.title()
        
    # Add State Schemes if state matches
    state_display = ""
    state_schemes_list = []
    
    if state:
        state_key = state.lower().replace(" ", "_")
        state_schemes_list = STATE_SCHEMES.get(state_key, [])
        if state_schemes_list:
            state_display = f" & {state.title()} State"
    
    # Build comprehensive response
    response = f"🎯 SUBSIDY OPPORTUNITIES for {sector_display} Sector{state_display}\n\n"
    response += f"📊 Investment Amount: Rs {capex_amount:,.0f}\n"
    response += "=" * 50 + "\n\n"
    
    # 1. Central/Sector Schemes
    response += f"🏛️ CENTRAL/SECTOR SPECIFIC SCHEMES:\n"
    
    total_potential = 0
    for i, scheme in enumerate(schemes, 1):
        # Calculate estimated benefit
        benefit_text = scheme['benefit']
        if '%' in benefit_text:
            try:
                subsidy_rate = float(benefit_text.split('%')[0].split()[-1]) / 100
            except:
                subsidy_rate = 0.25
        else:
            subsidy_rate = 0.25
        
        estimated = min(capex_amount * subsidy_rate, scheme['max_subsidy'])
        total_potential += estimated
        
        response += f"**{i}. {scheme['name']}**\n"
        response += f"   Benefit: {scheme['benefit']}\n"
        response += f"   Estimated for you: Rs {estimated:,.0f}\n"
        response += f"   Eligibility: {scheme['eligibility']}\n"
        response += f"   Ministry: {scheme['ministry']}\n"
        response += f"   Official Link: {scheme['link']}\n\n"
    
    # 2. State Schemes (if applicable)
    if state_schemes_list:
        response += f"📍 STATE SPECIFIC SCHEMES ({state.title()}):\n"
        for i, scheme in enumerate(state_schemes_list, 1):
             # Calculate estimated benefit (simple logic for now)
            benefit_text = scheme['benefit']
            if '%' in benefit_text:
                try:
                    subsidy_rate = float(benefit_text.split('%')[0].split()[-1]) / 100
                except:
                    subsidy_rate = 0.10 # Conservative default for state
            else:
                subsidy_rate = 0.10
            
            estimated = min(capex_amount * subsidy_rate, scheme['max_subsidy'])
            # Don't add to total potential blindly as they might be mutually exclusive or additive, keeps it simple
            
            response += f"**S{i}. {scheme['name']}**\n"
            response += f"   Benefit: {scheme['benefit']}\n"
            response += f"   Estimated: Rs {estimated:,.0f} (Check overlap rules)\n"
            response += f"   Eligibility: {scheme['eligibility']}\n"
            response += f"   Ministry: {scheme['ministry']}\n"
            response += f"   Official Link: {scheme['link']}\n\n"
            
    response += "=" * 50 + "\n"
    response += f"TOTAL POTENTIAL BENEFIT (Central): Rs {total_potential:,.0f}\n"
    response += f"Benefit Ratio: {(total_potential/capex_amount)*100:.1f}% of investment\n\n"
    
    response += "IMPORTANT NEXT STEPS:\n"
    response += "1. Visit official links above to verify current scheme status\n"
    response += "2. Check if State and Central schemes can be clubbed (often allowed up to 50% max)\n"
    response += "3. Prepare: Registration certificate, Bank details, Project report\n"
    response += "4. Consult a CA for compliance and application assistance\n"
    response += "5. Apply before scheme deadline (check respective portals)\n\n"
    response += "Note: Amounts are estimates. Actual benefits depend on eligibility verification."
    
    return response

# Phase 1: Router Logic - The Decision Maker
class NegotiationIntent(str, Enum):
    """Negotiation strategies based on financial context"""
    CREDIT_EXTENSION = "credit_extension"
    PAYMENT_CHASE = "payment_chase"
    EARLY_PAYMENT_OFFER = "early_payment_offer"

class NegotiationDraft(BaseModel):
    """Response model for negotiation drafts"""
    intent: NegotiationIntent
    strategy_explanation: str
    whatsapp_message: str
    formal_email: str
    option_a: str  # Relationship-focused
    option_b: str  # Transactional-focused

def _determine_negotiation_intent(
    transaction_type: str,
    amount: float,
    due_date: str,
    current_cash_position: float,
    upcoming_outflows: float = 0
) -> NegotiationIntent:
    """
    Router Logic: Determines negotiation strategy before writing
    
    Args:
        transaction_type: "payable" (we owe) or "receivable" (they owe us)
        amount: Transaction amount
        due_date: Due date in YYYY-MM-DD format
        current_cash_position: Current cash balance
        upcoming_outflows: Predicted outflows in next 30 days
    """
    from datetime import datetime, timedelta
    
    try:
        due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
        today = datetime.now()
        days_overdue = (today - due_date_obj).days
        
        # Intent 1: Credit Extension (We owe money and cash is tight)
        if transaction_type == "payable":
            projected_balance = current_cash_position - upcoming_outflows
            if projected_balance < amount or current_cash_position < amount * 1.2:
                return NegotiationIntent.CREDIT_EXTENSION
        
        # Intent 2: Payment Chase (They owe us and it's overdue)
        if transaction_type == "receivable" and days_overdue > 0:
            return NegotiationIntent.PAYMENT_CHASE
        
        # Intent 3: Early Payment Offer (We have surplus cash)
        if transaction_type == "payable" and current_cash_position > amount * 3:
            return NegotiationIntent.EARLY_PAYMENT_OFFER
        
        # Default to payment chase for receivables, credit extension for payables
        return NegotiationIntent.PAYMENT_CHASE if transaction_type == "receivable" else NegotiationIntent.CREDIT_EXTENSION
        
    except Exception as e:
        print(f"Intent determination error: {e}")
        return NegotiationIntent.CREDIT_EXTENSION

def _generate_negotiation_content(
    intent: NegotiationIntent,
    counterparty_name: str,
    amount: float,
    transaction_type: str,
    due_date: str,
    invoice_id: str = None
) -> dict:
    """
    Phase 2: Generator Logic using Gemini 3 Flash
    Generates authentic, context-aware negotiation messages
    """
    
    # Context setup
    invoice_ref = f"Invoice #{invoice_id}" if invoice_id else f"Amount ₹{amount:,.0f}"
    
    # Intent-specific prompt engineering
    if intent == NegotiationIntent.CREDIT_EXTENSION:
        scenario = f"requesting 15 days extension for payment of {invoice_ref}"
        tone_a = "apologetic, relationship-focused, emphasizing long-term partnership"
        tone_b = "professional, direct, focusing on specific payment date"
        
    elif intent == NegotiationIntent.PAYMENT_CHASE:
        from datetime import datetime
        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
            days_overdue = (datetime.now() - due_date_obj).days
            scenario = f"following up on overdue payment of {invoice_ref} (overdue by {days_overdue} days)"
        except:
            scenario = f"following up on overdue payment of {invoice_ref}"
        tone_a = "polite but firm, maintaining relationship while seeking immediate action"
        tone_b = "direct, business-focused, emphasizing payment urgency"
        
    else:  # EARLY_PAYMENT_OFFER
        scenario = f"offering early payment for {invoice_ref} in exchange for 2% discount"
        tone_a = "collaborative, win-win focused, emphasizing mutual benefit"
        tone_b = "transactional, direct, focusing on discount terms"
    
    # Base prompt for Gemini 3 Flash
    base_prompt = f"""You are the CFO of an Indian MSME. Your goal is to manage cash flow without burning relationships.

SCENARIO: {scenario}
COUNTERPARTY: {counterparty_name}
AMOUNT: ₹{amount:,.0f}
CONTEXT: {transaction_type.title()} transaction

REQUIREMENTS:
1. Generate TWO variations (Option A & B) with different approaches
2. Include WhatsApp message (max 160 chars) and formal email for each
3. Reference specific invoice number for authenticity
4. Use Indian business communication style
5. Be specific about dates and amounts

OPTION A TONE: {tone_a}
OPTION B TONE: {tone_b}

OUTPUT FORMAT (JSON):
{{
  "option_a": {{
    "whatsapp": "Brief WhatsApp message",
    "email": "Formal email content"
  }},
  "option_b": {{
    "whatsapp": "Brief WhatsApp message", 
    "email": "Formal email content"
  }}
}}

Generate authentic, professional content that sounds like real business communication."""

    try:
        # Call Gemini 3 Flash based on available provider
        if vision_provider == "gemini_new" and vision_model:
            response = vision_model.models.generate_content(
                model='gemini-1.5-flash',
                contents=[{'role': 'user', 'parts': [{'text': base_prompt}]}]
            )
            response_text = response.text.strip()
        elif vision_provider == "gemini_old" and vision_model:
            # Use the same model for text generation
            text_model = genai.GenerativeModel('gemini-2.5-flash')
            response = text_model.generate_content(base_prompt)
            response_text = response.text.strip()
        elif vision_provider == "openrouter":
            response_text = _call_openrouter_text(base_prompt)
        else:
            # Fallback to template-based generation
            return _generate_fallback_content(intent, counterparty_name, amount, invoice_ref)
        
        # Parse JSON response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        content = json.loads(response_text)
        return content
        
    except Exception as e:
        print(f"Content generation error: {e}")
        return _generate_fallback_content(intent, counterparty_name, amount, invoice_ref)

def _call_openrouter_text(prompt: str) -> str:
    """Call OpenRouter API for text generation"""
    import httpx
    
    api_key = OPENROUTER_API_KEY or GEMINI_API_KEY
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "google/gemini-flash-1.5",  # Use Gemini Flash via OpenRouter
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500
    }
    
    with httpx.Client() as client:
        response = client.post("https://openrouter.ai/api/v1/chat/completions", 
                             headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]

def _generate_fallback_content(intent: NegotiationIntent, counterparty_name: str, amount: float, invoice_ref: str) -> dict:
    """Fallback content generation when AI APIs are unavailable"""
    
    if intent == NegotiationIntent.CREDIT_EXTENSION:
        return {
            "option_a": {
                "whatsapp": f"Hi {counterparty_name}, need 15 days for {invoice_ref} payment. Cash flow timing issue. Thanks for understanding! 🙏",
                "email": f"Dear {counterparty_name} Team,\n\nWe value our partnership and need to request a 15-day extension for {invoice_ref} (₹{amount:,.0f}) due to temporary cash flow timing. We'll process payment by [date]. Thank you for your continued support.\n\nBest regards,\nFinance Team"
            },
            "option_b": {
                "whatsapp": f"{counterparty_name}, requesting payment extension for {invoice_ref} till [date]. Will confirm exact date by tomorrow.",
                "email": f"Subject: Payment Extension Request - {invoice_ref}\n\nDear Sir/Madam,\n\nWe request a 15-day extension for payment of {invoice_ref} amounting to ₹{amount:,.0f}. New payment date: [specific date].\n\nRegards,\nAccounts Department"
            }
        }
    
    elif intent == NegotiationIntent.PAYMENT_CHASE:
        return {
            "option_a": {
                "whatsapp": f"Hi {counterparty_name}, gentle reminder for {invoice_ref} payment. Let us know if any clarification needed. Thanks! 😊",
                "email": f"Dear {counterparty_name} Team,\n\nI hope you're doing well. This is a friendly reminder regarding {invoice_ref} for ₹{amount:,.0f} which was due on [date]. Please let us know if you need any clarification or if there are any issues we can help resolve.\n\nLooking forward to your response.\n\nBest regards,\nFinance Team"
            },
            "option_b": {
                "whatsapp": f"{counterparty_name}, {invoice_ref} payment overdue. Please process immediately or confirm payment date.",
                "email": f"Subject: Overdue Payment - {invoice_ref}\n\nDear Sir/Madam,\n\nThis is to inform you that payment for {invoice_ref} amounting to ₹{amount:,.0f} is overdue. Please process the payment immediately or confirm the expected payment date.\n\nRegards,\nAccounts Department"
            }
        }
    
    else:  # EARLY_PAYMENT_OFFER
        discount_amount = amount * 0.02
        return {
            "option_a": {
                "whatsapp": f"Hi {counterparty_name}, can offer early payment for {invoice_ref} with 2% discount. Win-win for both! Let me know 😊",
                "email": f"Dear {counterparty_name} Team,\n\nWe have good cash flow this month and would like to offer early payment for {invoice_ref} (₹{amount:,.0f}) in exchange for a 2% early payment discount (₹{discount_amount:,.0f}). This benefits both parties - you get faster payment, we get cost savings.\n\nPlease let us know if this works for you.\n\nBest regards,\nFinance Team"
            },
            "option_b": {
                "whatsapp": f"{counterparty_name}, offering immediate payment for {invoice_ref} less 2% discount. Confirm if acceptable.",
                "email": f"Subject: Early Payment Offer - {invoice_ref}\n\nDear Sir/Madam,\n\nWe offer immediate payment for {invoice_ref} (₹{amount:,.0f}) with 2% early payment discount. Net payment: ₹{amount - discount_amount:,.0f}.\n\nPlease confirm acceptance.\n\nRegards,\nAccounts Department"
            }
        }

@mcp.tool()
def generate_negotiation_draft(
    counterparty_name: str,
    amount: float,
    transaction_type: str,  # "payable" or "receivable"
    due_date: str,  # YYYY-MM-DD format
    current_cash_position: float,
    upcoming_outflows: float = 0,
    invoice_id: str = None
) -> NegotiationDraft:
    """
    Tool 4: The Negotiator (Agent D) - Complete Implementation
    
    Phase 1: Router determines strategy
    Phase 2: Gemini 3 Flash generates content
    Phase 3: Returns A/B testing options
    
    Args:
        counterparty_name: Name of vendor/customer
        amount: Transaction amount in rupees
        transaction_type: "payable" (we owe) or "receivable" (they owe us)
        due_date: Due date in YYYY-MM-DD format
        current_cash_position: Current cash balance
        upcoming_outflows: Predicted outflows in next 30 days (optional)
        invoice_id: Invoice number for reference (optional)
    
    Returns:
        NegotiationDraft with strategy, WhatsApp message, formal email, and A/B options
    """
    
    try:
        # Phase 1: Router Logic - Determine Intent
        intent = _determine_negotiation_intent(
            transaction_type=transaction_type,
            amount=amount,
            due_date=due_date,
            current_cash_position=current_cash_position,
            upcoming_outflows=upcoming_outflows
        )
        
        # Strategy explanation
        strategy_explanations = {
            NegotiationIntent.CREDIT_EXTENSION: f"Cash flow analysis shows insufficient funds. Requesting payment extension to maintain vendor relationships while managing liquidity.",
            NegotiationIntent.PAYMENT_CHASE: f"Payment is overdue. Following up professionally to maintain cash flow while preserving business relationship.",
            NegotiationIntent.EARLY_PAYMENT_OFFER: f"Strong cash position detected. Offering early payment with discount to optimize working capital and strengthen vendor relationships."
        }
        
        # Phase 2: Generator Logic - Create Content
        content = _generate_negotiation_content(
            intent=intent,
            counterparty_name=counterparty_name,
            amount=amount,
            transaction_type=transaction_type,
            due_date=due_date,
            invoice_id=invoice_id
        )
        
        # Phase 3: Format Response with A/B Testing
        return NegotiationDraft(
            intent=intent,
            strategy_explanation=strategy_explanations[intent],
            whatsapp_message=content["option_a"]["whatsapp"],
            formal_email=content["option_a"]["email"],
            option_a=f"RELATIONSHIP-FOCUSED:\nWhatsApp: {content['option_a']['whatsapp']}\n\nEmail:\n{content['option_a']['email']}",
            option_b=f"TRANSACTIONAL-FOCUSED:\nWhatsApp: {content['option_b']['whatsapp']}\n\nEmail:\n{content['option_b']['email']}"
        )
        
    except Exception as e:
        # Fallback response
        return NegotiationDraft(
            intent=NegotiationIntent.CREDIT_EXTENSION,
            strategy_explanation=f"Error in negotiation generation: {str(e)}",
            whatsapp_message=f"Hi {counterparty_name}, regarding payment of ₹{amount:,.0f}. Can we discuss?",
            formal_email=f"Dear {counterparty_name},\n\nWe would like to discuss the payment terms for ₹{amount:,.0f}.\n\nBest regards,\nFinance Team",
            option_a="Fallback option A - Relationship focused approach",
            option_b="Fallback option B - Direct business approach"
        )

if __name__ == "__main__":
    mcp.run()
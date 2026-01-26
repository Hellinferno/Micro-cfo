#!/usr/bin/env python3
"""
Direct test of Gemini 1.5 Flash without MCP wrapper
"""

import os
import json
import io

import pytest
from PIL import Image, ImageDraw, ImageFont

# SECURITY: Load API keys from environment variables only
# Set your API key before running: export GEMINI_API_KEY='your-key-here'
# Or create a .env file (see .env.example)

# Import Gemini
try:
    import google.generativeai as genai
except ImportError as import_error:
    pytest.skip(f"Gemini SDK unavailable: {import_error}", allow_module_level=True)

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    pytest.skip("GEMINI_API_KEY not set. Skipping Gemini direct test.", allow_module_level=True)

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ Gemini 2.5 Flash configured")
except Exception as setup_error:
    pytest.skip(f"Gemini setup failed: {setup_error}", allow_module_level=True)

def create_simple_invoice():
    """Create a simple text-based invoice image"""
    
    # Create image
    img = Image.new('RGB', (600, 800), 'white')
    draw = ImageDraw.Draw(img)
    
    # Use default font
    font = ImageFont.load_default()
    
    # Draw invoice content
    y = 50
    lines = [
        "INVOICE",
        "",
        "Gujarat Textile Machinery Ltd",
        "GSTIN: 24AABCU9603R1ZX",
        "Date: 2024-01-15",
        "",
        "Bill To: ABC Textiles Pvt Ltd",
        "",
        "ITEMS:",
        "1. Rapier Loom Machine      ₹8,00,000",
        "2. Automatic Warp Feeder    ₹1,50,000", 
        "3. Installation & Training  ₹50,000",
        "",
        "Subtotal:                   ₹10,00,000",
        "GST @ 18%:                  ₹1,80,000",
        "TOTAL:                      ₹11,80,000"
    ]
    
    for line in lines:
        if line == "INVOICE":
            # Make title larger
            draw.text((50, y), line, fill='black', font=font)
            y += 40
        else:
            draw.text((50, y), line, fill='black', font=font)
            y += 25
    
    return img

def test_gemini_vision():
    """Test Gemini with a simple invoice"""
    
    print("🧪 Testing Gemini 2.5 Flash Vision")
    print("=" * 40)
    
    # Create invoice image
    print("📸 Creating invoice image...")
    invoice_img = create_simple_invoice()
    invoice_img.save("test_invoice.png")
    print("✅ Invoice image saved: test_invoice.png")
    
    # Prepare prompt
    prompt = """You are a financial auditor. Analyze this invoice image and extract:

1. Vendor name
2. Invoice date (YYYY-MM-DD format)
3. Total amount (as number)
4. Tax amount (as number)
5. GSTIN number
6. Line items with amounts

Respond in JSON format:
{
  "vendor_name": "string",
  "invoice_date": "YYYY-MM-DD", 
  "total_amount": number,
  "tax_amount": number,
  "gstin": "string",
  "line_items": [
    {"description": "string", "amount": number, "category": "Capital Goods"}
  ]
}"""

    try:
        print("🚀 Calling Gemini 2.5 Flash...")
        
        # Call Gemini
        response = model.generate_content([prompt, invoice_img])
        
        print("✅ Response received!")
        print(f"📄 Raw response:")
        print("-" * 30)
        print(response.text)
        print("-" * 30)
        
        # Try to parse JSON
        response_text = response.text.strip()
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_text = response_text
        
        try:
            data = json.loads(json_text)
            print(f"\n✅ Parsed JSON successfully!")
            print(f"📊 Extracted Data:")
            print(f"   Vendor: {data.get('vendor_name', 'N/A')}")
            print(f"   Date: {data.get('invoice_date', 'N/A')}")
            print(f"   Total: ₹{data.get('total_amount', 0):,.2f}")
            print(f"   Tax: ₹{data.get('tax_amount', 0):,.2f}")
            print(f"   GSTIN: {data.get('gstin', 'N/A')}")
            
            line_items = data.get('line_items', [])
            print(f"   Items: {len(line_items)} line items")
            
            for i, item in enumerate(line_items, 1):
                desc = item.get('description', 'N/A')
                amount = item.get('amount', 0)
                print(f"     {i}. {desc} - ₹{amount:,.2f}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print("Raw text might not be valid JSON")
            return False
        
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_vision()
    
    if success:
        print(f"\n🚀 SUCCESS: Gemini 2.5 Flash is working!")
        print("Agent A vision processing is ready for integration.")
    else:
        print(f"\n❌ Test failed. Check API key and connection.")
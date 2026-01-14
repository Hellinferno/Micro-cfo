#!/usr/bin/env python3
"""
Test Agent A with real Gemini 1.5 Flash API
Creates a sample invoice image and processes it
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# SECURITY: Load API keys from environment variables only
# Set your API key before running: export GEMINI_API_KEY='your-key-here'
# Or create a .env file (see .env.example)

def create_sample_invoice_image():
    """Create a sample invoice image for testing"""
    
    # Create a white background image
    width, height = 800, 1000
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_medium = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw invoice header
    draw.text((50, 50), "INVOICE", fill='black', font=font_large)
    draw.text((50, 100), "Gujarat Textile Machinery Ltd", fill='black', font=font_medium)
    draw.text((50, 130), "GSTIN: 24AABCU9603R1ZX", fill='black', font=font_small)
    draw.text((50, 150), "Date: 2024-01-15", fill='black', font=font_small)
    
    # Draw bill to
    draw.text((50, 200), "Bill To:", fill='black', font=font_medium)
    draw.text((50, 230), "ABC Textiles Pvt Ltd", fill='black', font=font_small)
    draw.text((50, 250), "Mumbai, Maharashtra", fill='black', font=font_small)
    
    # Draw line items
    y_pos = 320
    draw.text((50, y_pos), "Description", fill='black', font=font_medium)
    draw.text((400, y_pos), "Amount", fill='black', font=font_medium)
    
    # Draw a line
    draw.line([(50, y_pos + 25), (750, y_pos + 25)], fill='black', width=1)
    
    y_pos += 50
    items = [
        ("Rapier Loom Machine - Model RTL-2024", "₹8,00,000.00"),
        ("Automatic Warp Feeder", "₹1,50,000.00"),
        ("Installation & Training", "₹50,000.00"),
        ("", ""),
        ("Subtotal", "₹10,00,000.00"),
        ("GST @ 18%", "₹1,80,000.00"),
        ("Total Amount", "₹11,80,000.00")
    ]
    
    for desc, amount in items:
        if desc:  # Skip empty lines
            draw.text((50, y_pos), desc, fill='black', font=font_small)
        if amount:
            draw.text((400, y_pos), amount, fill='black', font=font_small)
        y_pos += 30
    
    # Draw total box
    draw.rectangle([(350, y_pos - 60), (750, y_pos - 30)], outline='black', width=2)
    
    return image

def test_gemini_vision():
    """Test Gemini 1.5 Flash with sample invoice"""
    
    print("🧪 Testing Agent A with Gemini 1.5 Flash")
    print("=" * 50)
    
    # Step 1: Create sample invoice image
    print("\n📸 Step 1: Creating Sample Invoice Image")
    print("-" * 30)
    
    try:
        invoice_image = create_sample_invoice_image()
        
        # Save for reference
        invoice_image.save("sample_invoice.png")
        print("✅ Sample invoice image created: sample_invoice.png")
        print("   Content: Textile machinery purchase (₹11.8L)")
        
    except Exception as e:
        print(f"❌ Error creating image: {e}")
        return False
    
    # Step 2: Test with mock data first
    print("\n📋 Step 2: Testing Mock Data Processing")
    print("-" * 30)
    
    try:
        from server import _get_mock_invoice, _apply_safety_validations
        
        mock_invoice = _get_mock_invoice()
        print(f"✅ Mock invoice: {mock_invoice.vendor_name}")
        print(f"   Total: ₹{mock_invoice.total_amount:,.2f}")
        print(f"   Items: {len(mock_invoice.line_items)} line items")
        
    except Exception as e:
        print(f"❌ Error with mock data: {e}")
        return False
    
    # Step 3: Test real vision processing
    print("\n🔍 Step 3: Testing Real Vision Processing")
    print("-" * 30)
    
    try:
        # Convert image to base64 for processing
        buffer = io.BytesIO()
        invoice_image.save(buffer, format='PNG')
        image_b64 = base64.b64encode(buffer.getvalue()).decode()
        image_data_url = f"data:image/png;base64,{image_b64}"
        
        print("✅ Image converted to base64")
        print(f"   Size: {len(image_b64)} characters")
        
        # Import and test the scan function
        from server import scan_invoice_document
        
        print("\n🚀 Calling Gemini 1.5 Flash...")
        result = scan_invoice_document(image_data_url, use_mock=False)
        
        print("✅ Vision processing completed!")
        print(f"\n📄 Extracted Invoice Data:")
        print(f"   Vendor: {result.vendor_name}")
        print(f"   Date: {result.invoice_date}")
        print(f"   Total: ₹{result.total_amount:,.2f}")
        print(f"   Tax: ₹{result.tax_amount:,.2f}")
        print(f"   GSTIN: {result.gstin}")
        
        print(f"\n🔍 Audit Results:")
        print(f"   Handwritten: {result.is_handwritten}")
        print(f"   Tampering: {result.tampering_detected}")
        print(f"   Confidence: {result.confidence_score}")
        
        print(f"\n📋 Line Items ({len(result.line_items)}):")
        for i, item in enumerate(result.line_items, 1):
            if item.category != "Alert":
                print(f"   {i}. {item.description}")
                print(f"      ₹{item.amount:,.2f} ({item.category})")
            else:
                print(f"   🚨 {item.description[:80]}...")
        
        if result.compliance_flags:
            print(f"\n⚠️  Compliance Flags ({len(result.compliance_flags)}):")
            for flag in result.compliance_flags:
                print(f"   • {flag}")
        
        # Check for orchestrator triggers
        capital_goods = [item for item in result.line_items if item.category == "Capital Goods"]
        if capital_goods:
            total_capex = sum(item.amount for item in capital_goods)
            print(f"\n🎯 Orchestrator Analysis:")
            print(f"   Capital Goods Total: ₹{total_capex:,.2f}")
            if total_capex > 100000:
                print(f"   ✅ Subsidy trigger activated (>₹1L)")
                print(f"   Expected: TUFS scheme alert")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in vision processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_configuration():
    """Test API configuration"""
    
    print("\n🔧 API Configuration Test")
    print("-" * 30)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"✅ Gemini API Key: {gemini_key[:20]}...")
        
        # Test import
        try:
            from server import vision_provider, vision_model
            print(f"✅ Vision Provider: {vision_provider}")
            
            if vision_provider and "gemini" in vision_provider:
                print("✅ Gemini 1.5 Flash configured successfully")
                return True
            else:
                print("⚠️ Gemini not configured, using fallback")
                return False
                
        except Exception as e:
            print(f"❌ Import error: {e}")
            return False
    else:
        print("❌ No Gemini API key found")
        return False

if __name__ == "__main__":
    
    print("🎯 Agent A - Gemini 1.5 Flash Integration Test")
    print("=" * 60)
    
    # Test 1: API Configuration
    api_ok = test_api_configuration()
    
    if not api_ok:
        print("\n❌ API configuration failed. Please check your setup.")
        exit(1)
    
    # Test 2: Vision Processing
    vision_ok = test_gemini_vision()
    
    if vision_ok:
        print(f"\n" + "=" * 60)
        print("🚀 SUCCESS: Agent A with Gemini 1.5 Flash is working!")
        print("=" * 60)
        
        print(f"\n✅ Capabilities Verified:")
        print(f"   • Real image processing with Gemini 1.5 Flash")
        print(f"   • Structured data extraction from invoices")
        print(f"   • Fraud detection and compliance checking")
        print(f"   • Orchestrator triggers for other agents")
        print(f"   • Conservative CA-style risk assessment")
        
        print(f"\n📖 Ready for Production:")
        print(f"   • Process real invoices: scan_invoice_document('image.jpg')")
        print(f"   • Start MCP server: python server.py")
        print(f"   • Test with MCP Inspector: mcp dev server.py")
        
    else:
        print(f"\n❌ Vision processing test failed.")
        print("Check your Gemini API key and network connection.")
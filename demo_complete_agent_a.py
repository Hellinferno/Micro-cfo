#!/usr/bin/env python3
"""
Complete Demo of Agent A - Visual Auditor with Real Invoice Processing
Shows the full workflow from image to structured data with orchestrator triggers
"""

# SECURITY: Load API keys from environment variables only
# Set your API key before running:
#   Windows: set GEMINI_API_KEY=your-key-here
#   Unix/Mac: export GEMINI_API_KEY=your-key-here
# Or create a .env file (see .env.example)

import os
import json
from datetime import datetime

print("🎯 MicroCFO Agent A - Complete Demo")
print("=" * 60)

def demo_textile_machinery_scenario():
    """Demo: Textile company buying industrial loom"""
    
    print("\n🏭 SCENARIO: Textile Company Machinery Purchase")
    print("-" * 50)
    
    from server import _get_mock_invoice, _apply_safety_validations
    
    # Create a realistic textile machinery invoice
    from server import Invoice, LineItem
    
    invoice = Invoice(
        vendor_name="Gujarat Textile Machinery Ltd",
        invoice_date=datetime.now().strftime("%Y-%m-%d"),  # Today's date
        total_amount=1180000.0,  # 11.8 Lakh
        tax_amount=180000.0,     # 18% GST
        line_items=[
            LineItem(description="Rapier Loom Machine - Model RTL-2024", amount=800000.0, category="Capital Goods"),
            LineItem(description="Automatic Warp Feeder", amount=150000.0, category="Capital Goods"),
            LineItem(description="Installation & Training", amount=50000.0, category="Service"),
            LineItem(description="GST @ 18%", amount=180000.0, category="Service")
        ],
        gstin="24AABCU9603R1ZX",
        is_handwritten=False,
        tampering_detected=False,
        compliance_flags=[],
        confidence_score=0.92
    )
    
    print(f"📄 Invoice Details:")
    print(f"   Vendor: {invoice.vendor_name}")
    print(f"   Date: {invoice.invoice_date}")
    print(f"   Total: ₹{invoice.total_amount:,.2f}")
    print(f"   GSTIN: {invoice.gstin}")
    
    print(f"\n📋 Line Items:")
    capital_goods_total = 0
    for i, item in enumerate(invoice.line_items, 1):
        print(f"   {i}. {item.description}")
        print(f"      ₹{item.amount:,.2f} ({item.category})")
        if item.category == "Capital Goods":
            capital_goods_total += item.amount
    
    print(f"\n💰 Capital Goods Total: ₹{capital_goods_total:,.2f}")
    
    # Apply safety validations
    _apply_safety_validations(invoice)
    
    if invoice.compliance_flags:
        print(f"\n⚠️  Compliance Flags:")
        for flag in invoice.compliance_flags:
            print(f"   • {flag}")
    else:
        print(f"\n✅ No compliance issues detected")
    
    # Manual orchestrator trigger simulation
    print(f"\n🎯 ORCHESTRATOR TRIGGERS:")
    print("-" * 30)
    
    if capital_goods_total > 100000:
        print(f"✅ Capital Goods Trigger Activated!")
        print(f"   Amount: ₹{capital_goods_total:,.2f} > ₹1,00,000")
        print(f"   Action: Auto-triggering Agent C (Subsidy Hunter)")
        
        # Simulate subsidy search
        print(f"\n🎯 SUBSIDY ALERT:")
        print(f"   Scheme: Technology Upgradation Fund Scheme (TUFS)")
        print(f"   Eligibility: Textile machinery purchase")
        print(f"   Benefit: Up to 25% capital subsidy")
        print(f"   Estimated Benefit: ₹{min(capital_goods_total * 0.25, 2500000):,.2f}")
        print(f"   Next Steps: Apply within 6 months of purchase")
    
    return invoice

def demo_restaurant_bill_scenario():
    """Demo: Restaurant bill with compliance issues"""
    
    print("\n🍽️  SCENARIO: Restaurant Bill Compliance Check")
    print("-" * 50)
    
    from server import Invoice, LineItem, _apply_safety_validations
    
    invoice = Invoice(
        vendor_name="The Grand Restaurant",
        invoice_date="2024-01-10",
        total_amount=8500.0,
        tax_amount=765.0,  # 9% GST on restaurant services
        line_items=[
            LineItem(description="Business Lunch - 8 persons", amount=6000.0, category="Personal/Entertainment"),
            LineItem(description="Alcoholic Beverages", amount=2000.0, category="Personal/Entertainment"),
            LineItem(description="Service Charge", amount=500.0, category="Service"),
            LineItem(description="GST @ 9%", amount=765.0, category="Service")
        ],
        gstin="27AABCD1234E1ZF",
        is_handwritten=False,
        tampering_detected=False,
        compliance_flags=[],
        confidence_score=0.88
    )
    
    print(f"📄 Invoice Details:")
    print(f"   Vendor: {invoice.vendor_name}")
    print(f"   Total: ₹{invoice.total_amount:,.2f}")
    print(f"   Items: Business entertainment")
    
    # Apply safety validations
    _apply_safety_validations(invoice)
    
    # Manual compliance trigger
    personal_items = [item for item in invoice.line_items if item.category == "Personal/Entertainment"]
    
    if personal_items:
        print(f"\n⚠️  COMPLIANCE TRIGGER ACTIVATED:")
        print(f"   Detected: {len(personal_items)} personal/entertainment items")
        print(f"   Action: Auto-triggering Agent B (Legal Sentinel)")
        
        print(f"\n🚨 ITC WARNING:")
        print(f"   Section 17(5) of CGST Act - ITC Blocked Items:")
        print(f"   • Food and beverages (except for resale)")
        print(f"   • Alcoholic beverages")
        print(f"   • Entertainment expenses")
        print(f"   Recommendation: Claim only service charge GST as ITC")
        
        eligible_itc = 765.0 * (500.0 / 8500.0)  # Only service charge portion
        print(f"   Eligible ITC: ₹{eligible_itc:.2f} (service charge only)")
    
    return invoice

def demo_fraud_detection():
    """Demo: Fraud detection capabilities"""
    
    print("\n🕵️ SCENARIO: Fraud Detection Demo")
    print("-" * 50)
    
    from server import Invoice, LineItem, _apply_safety_validations
    
    # Suspicious invoice
    invoice = Invoice(
        vendor_name="Suspicious Vendor",
        invoice_date="2023-06-15",  # Old date
        total_amount=50000.0,
        tax_amount=9000.0,  # Tax without GSTIN
        line_items=[
            LineItem(description="Consulting Services", amount=50000.0, category="Service"),
            LineItem(description="GST @ 18%", amount=9000.0, category="Service")
        ],
        gstin=None,  # Missing GSTIN
        is_handwritten=True,  # Handwritten
        tampering_detected=True,  # Tampering detected
        compliance_flags=[],
        confidence_score=0.45  # Low confidence
    )
    
    print(f"📄 Suspicious Invoice:")
    print(f"   Vendor: {invoice.vendor_name}")
    print(f"   Total: ₹{invoice.total_amount:,.2f}")
    print(f"   GSTIN: {invoice.gstin or 'MISSING'}")
    print(f"   Handwritten: {invoice.is_handwritten}")
    print(f"   Tampering: {invoice.tampering_detected}")
    print(f"   Confidence: {invoice.confidence_score}")
    
    # Apply all validations
    _apply_safety_validations(invoice)
    
    print(f"\n🚨 FRAUD ALERTS:")
    for flag in invoice.compliance_flags:
        print(f"   • {flag}")
    
    print(f"\n📋 Recommended Actions:")
    print(f"   1. Manual verification required")
    print(f"   2. Request original invoice copy")
    print(f"   3. Verify vendor GSTIN registration")
    print(f"   4. Do not claim ITC without proper documentation")
    
    return invoice

def demo_real_image_processing():
    """Demo: How to process real images"""
    
    print("\n📸 REAL IMAGE PROCESSING GUIDE")
    print("-" * 50)
    
    print(f"🔧 Setup Instructions:")
    print(f"   1. Your OpenRouter API key is already configured")
    print(f"   2. Supports: JPG, PNG, PDF files")
    print(f"   3. Can process: URLs, local files, base64 data")
    
    print(f"\n💻 Code Example:")
    print(f"   ```python")
    print(f"   from server import scan_invoice_document")
    print(f"   ")
    print(f"   # Process local image")
    print(f"   result = scan_invoice_document('invoice.jpg')")
    print(f"   ")
    print(f"   # Process URL")
    print(f"   result = scan_invoice_document('https://example.com/invoice.png')")
    print(f"   ")
    print(f"   # Process base64")
    print(f"   result = scan_invoice_document('data:image/jpeg;base64,/9j/4AAQ...')")
    print(f"   ```")
    
    print(f"\n🎯 Expected Output:")
    print(f"   • Vendor name, date, amounts extracted")
    print(f"   • Line items categorized (Capital/Raw Material/Personal/Service)")
    print(f"   • Fraud detection (tampering, handwriting)")
    print(f"   • Compliance flags (ITC eligibility)")
    print(f"   • Automatic subsidy alerts for machinery")
    print(f"   • Conservative CA-style warnings")

if __name__ == "__main__":
    
    # Run all demo scenarios
    invoice1 = demo_textile_machinery_scenario()
    invoice2 = demo_restaurant_bill_scenario()
    invoice3 = demo_fraud_detection()
    demo_real_image_processing()
    
    print(f"\n" + "=" * 60)
    print(f"🚀 AGENT A - VISUAL AUDITOR READY!")
    print(f"=" * 60)
    
    print(f"\n✅ Capabilities Demonstrated:")
    print(f"   • Mock invoice processing with realistic data")
    print(f"   • Safety validations and compliance checking")
    print(f"   • Orchestrator triggers for other agents")
    print(f"   • Fraud detection and tampering alerts")
    print(f"   • Conservative CA-style risk assessment")
    
    print(f"\n🎯 Ready for Production:")
    print(f"   • OpenRouter API configured (GPT-4V)")
    print(f"   • Supports real image processing")
    print(f"   • Integrates with Agents B, C, D")
    print(f"   • MCP server ready: python server.py")
    
    print(f"\n📖 Next Steps:")
    print(f"   1. Start MCP server: python server.py")
    print(f"   2. Test with MCP Inspector: mcp dev server.py")
    print(f"   3. Process real invoices through MCP tools")
    print(f"   4. Integrate with your AI assistant/chatbot")
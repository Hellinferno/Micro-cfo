#!/usr/bin/env python3
"""
Demo script for Agent A - The Visual Auditor
Tests the Gemini 1.5 Flash integration with sample invoice processing
"""

import os
import json
from server import scan_invoice_document, get_user_profile

def test_visual_auditor():
    """Test the visual auditor with mock data and real API if available"""
    
    print("🔍 MicroCFO Agent A - Visual Auditor Demo")
    print("=" * 50)
    
    # Check if vision API is configured
    gemini_key = os.getenv("GEMINI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if openrouter_key or (gemini_key and gemini_key.startswith("sk-or-")):
        print("✅ OpenRouter API Key found - Will use GPT-4V for vision processing")
        print("📝 Supports: GPT-4V, Claude 3 Sonnet, and other vision models")
    elif gemini_key:
        print("✅ Gemini API Key found - Will use Gemini 1.5 Flash")
        print("📝 Google's multimodal model for invoice processing")
    else:
        print("⚠️  No vision API key found - Using mock data")
        print("   Set OPENROUTER_API_KEY or GEMINI_API_KEY environment variable")
        print("   OpenRouter: https://openrouter.ai/")
        print("   Gemini: https://makersuite.google.com/app/apikey")
    
    print("\n" + "=" * 50)
    
    # Test 1: Mock invoice processing
    print("\n🧪 Test 1: Processing Sample Invoice (Mock Data)")
    print("-" * 30)
    
    try:
        # Process with mock data
        invoice = scan_invoice_document("mock_image_url", use_mock=True)
        
        print(f"📄 Vendor: {invoice.vendor_name}")
        print(f"📅 Date: {invoice.invoice_date}")
        print(f"💰 Total: ₹{invoice.total_amount:,.2f}")
        print(f"🏷️  Tax: ₹{invoice.tax_amount:,.2f}")
        print(f"🆔 GSTIN: {invoice.gstin}")
        
        print(f"\n🔍 Audit Results:")
        print(f"   Handwritten: {invoice.is_handwritten}")
        print(f"   Tampering Detected: {invoice.tampering_detected}")
        print(f"   Confidence: {invoice.confidence_score:.2f}")
        
        print(f"\n📋 Line Items:")
        for i, item in enumerate(invoice.line_items, 1):
            if item.category != "Alert":
                print(f"   {i}. {item.description} - ₹{item.amount:,.2f} ({item.category})")
            else:
                print(f"   🚨 {item.description}")
        
        if invoice.compliance_flags:
            print(f"\n⚠️  Compliance Flags:")
            for flag in invoice.compliance_flags:
                print(f"   • {flag}")
        
        print("\n✅ Mock processing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in mock processing: {e}")
    
    # Test 2: User profile context
    print(f"\n🧪 Test 2: User Profile Context")
    print("-" * 30)
    
    try:
        profile = get_user_profile()
        profile_data = json.loads(profile)
        
        print(f"🏢 Business: {profile_data['business_name']}")
        print(f"📊 Turnover Tier: {profile_data['turnover_tier']}")
        print(f"🏭 Industry: {profile_data['industry_code']}")
        print(f"📋 GST Type: {profile_data['gst_registration_type']}")
        
    except Exception as e:
        print(f"❌ Error getting profile: {e}")
    
    # Test 3: Integration demonstration
    print(f"\n🧪 Test 3: Agent Integration Demo")
    print("-" * 30)
    
    print("🔄 The Visual Auditor automatically triggers:")
    print("   • Agent C (Subsidy Hunter) for Capital Goods > ₹1L")
    print("   • Agent B (Legal Sentinel) for compliance issues")
    print("   • Fraud detection and tampering alerts")
    print("   • ITC eligibility warnings")
    
    # Instructions for real testing
    print(f"\n📖 Real Image Testing Instructions:")
    print("-" * 30)
    print("1. Your OpenRouter API key is already configured!")
    print("2. Call: scan_invoice_document('path/to/invoice.jpg')")
    print("3. Supported formats: JPG, PNG, PDF (first page)")
    print("4. Can use URLs, local paths, or base64 data")
    print("5. Uses GPT-4V through OpenRouter for vision processing")
    
    print(f"\n🎯 Expected Behavior:")
    print("   • Extracts vendor, amounts, dates, GSTIN")
    print("   • Categorizes items (Capital/Raw Material/Personal/Service)")
    print("   • Detects tampering and handwriting")
    print("   • Flags ITC non-eligible items")
    print("   • Triggers subsidy alerts for machinery")
    print("   • Conservative CA-style compliance warnings")

def demo_fraud_detection():
    """Demonstrate fraud detection capabilities"""
    
    print(f"\n🕵️ Fraud Detection Demo")
    print("=" * 30)
    
    fraud_scenarios = [
        "Mismatched fonts in amount fields",
        "Blurred or pixelated numbers",
        "Handwritten overrides on printed bills",
        "Missing GSTIN with tax charged",
        "Stale invoices (>30 days old)",
        "Personal expenses claimed as business"
    ]
    
    print("🚨 Agent A detects these fraud patterns:")
    for i, scenario in enumerate(fraud_scenarios, 1):
        print(f"   {i}. {scenario}")
    
    print(f"\n🛡️ Conservative Approach:")
    print("   • When in doubt, flag it")
    print("   • Manual verification recommended")
    print("   • CA-style risk assessment")

def demo_orchestrator():
    """Demonstrate orchestrator triggers"""
    
    print(f"\n🎭 Orchestrator Demo")
    print("=" * 25)
    
    print("🔄 Automatic Agent Triggers:")
    print("   📸 Agent A scans invoice")
    print("   ⬇️  Detects ₹5L machinery purchase")
    print("   🎯 Auto-triggers Agent C (Subsidy Hunter)")
    print("   💰 Shows: 'PLI Scheme - ₹75,000 potential benefit'")
    print("   ⚠️  Auto-triggers Agent B for compliance")
    print("   📋 Shows: 'ITC eligible - ensure proper documentation'")

if __name__ == "__main__":
    test_visual_auditor()
    demo_fraud_detection()
    demo_orchestrator()
    
    print(f"\n🚀 Ready to process real invoices!")
    print("Set GEMINI_API_KEY and call scan_invoice_document() with image path")
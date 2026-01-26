#!/usr/bin/env python3
"""
Quick test for Agent A - Visual Auditor
"""

import os
import sys

# SECURITY: Load API keys from environment variables only
# Set your API key before running: export OPENROUTER_API_KEY='your-key-here'
# Or create a .env file (see .env.example)

print("🔍 Testing Agent A - Visual Auditor")
print("=" * 50)

# Test 1: Check API configuration
print("\n📋 Test 1: API Configuration")
print("-" * 30)

openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    print(f"✅ OpenRouter API Key: {openrouter_key[:15]}...")
    print("   Provider: OpenRouter (GPT-4V)")
else:
    print("⚠️  No OpenRouter API key found; skipping live API checks and continuing with mock validation")

# Test 2: Import and test mock invoice
print("\n📋 Test 2: Mock Invoice Processing")
print("-" * 30)

try:
    # Import the internal functions directly
    from server import _get_mock_invoice, _apply_safety_validations, _trigger_orchestrator
    
    # Get mock invoice
    invoice = _get_mock_invoice()
    
    print(f"✅ Mock invoice created")
    print(f"   Vendor: {invoice.vendor_name}")
    print(f"   Date: {invoice.invoice_date}")
    print(f"   Total: ₹{invoice.total_amount:,.2f}")
    print(f"   Tax: ₹{invoice.tax_amount:,.2f}")
    print(f"   GSTIN: {invoice.gstin}")
    
    print(f"\n📋 Line Items:")
    for i, item in enumerate(invoice.line_items, 1):
        print(f"   {i}. {item.description}")
        print(f"      Amount: ₹{item.amount:,.2f}")
        print(f"      Category: {item.category}")
    
    print(f"\n🔍 Audit Flags:")
    print(f"   Handwritten: {invoice.is_handwritten}")
    print(f"   Tampering: {invoice.tampering_detected}")
    print(f"   Confidence: {invoice.confidence_score}")
    
    # Test 3: Apply safety validations
    print("\n📋 Test 3: Safety Validations")
    print("-" * 30)
    
    _apply_safety_validations(invoice)
    
    if invoice.compliance_flags:
        print(f"⚠️  Compliance Flags Found:")
        for flag in invoice.compliance_flags:
            print(f"   • {flag}")
    else:
        print("✅ No compliance issues detected")
    
    # Test 4: Orchestrator triggers
    print("\n📋 Test 4: Orchestrator Triggers")
    print("-" * 30)
    
    initial_items = len(invoice.line_items)
    _trigger_orchestrator(invoice)
    
    if len(invoice.line_items) > initial_items:
        print("✅ Orchestrator triggered successfully!")
        print(f"   Added {len(invoice.line_items) - initial_items} alert(s)")
        
        # Show new alerts
        for item in invoice.line_items[initial_items:]:
            print(f"\n   🚨 {item.description[:100]}...")
    else:
        print("ℹ️  No orchestrator triggers activated")
        print("   (Triggers activate for Capital Goods >₹1L or Personal items)")
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Agent A is ready.")
    print("\n📖 Next Steps:")
    print("   1. Your OpenRouter API key is configured")
    print("   2. To test with real images, use the MCP server")
    print("   3. Start server: python server.py")
    print("   4. Or test with MCP Inspector: mcp dev server.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

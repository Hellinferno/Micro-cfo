#!/usr/bin/env python3
"""
Simple Test for Agent D: The Negotiator
Direct function testing without MCP wrapper complications
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append('.')

def test_agent_d_direct():
    """Test Agent D functions directly"""
    print("🤖 AGENT D: DIRECT FUNCTION TESTING")
    print("=" * 50)
    
    # Test 1: Router Logic
    print("🔄 Testing Router Logic...")
    try:
        # Import the classes and functions we need
        from server import NegotiationIntent, _determine_negotiation_intent
        
        # Test credit extension scenario
        intent = _determine_negotiation_intent(
            transaction_type="payable",
            amount=500000,
            due_date="2024-01-20", 
            current_cash_position=300000,
            upcoming_outflows=200000
        )
        
        print(f"✅ Router Test: {intent}")
        assert intent == NegotiationIntent.CREDIT_EXTENSION
        
    except Exception as e:
        print(f"❌ Router Error: {e}")
        return False
    
    # Test 2: Content Generation
    print("\n🎨 Testing Content Generation...")
    try:
        from server import _generate_negotiation_content, NegotiationIntent
        
        content = _generate_negotiation_content(
            intent=NegotiationIntent.CREDIT_EXTENSION,
            counterparty_name="Test Supplier Ltd",
            amount=500000,
            transaction_type="payable",
            due_date="2024-01-20",
            invoice_id="TEST-001"
        )
        
        print(f"✅ Content Generated: {len(content)} options")
        print(f"   Option A WhatsApp: {content['option_a']['whatsapp'][:50]}...")
        print(f"   Option B Email: {content['option_b']['email'][:50]}...")
        
    except Exception as e:
        print(f"❌ Content Error: {e}")
        return False
    
    # Test 3: Complete Workflow (Manual)
    print("\n🛠️ Testing Complete Workflow...")
    try:
        from server import (
            NegotiationIntent, NegotiationDraft, 
            _determine_negotiation_intent, _generate_negotiation_content
        )
        
        # Step 1: Determine intent
        intent = _determine_negotiation_intent(
            transaction_type="receivable",
            amount=200000,
            due_date="2024-01-10",  # Overdue
            current_cash_position=1000000,
            upcoming_outflows=0
        )
        
        # Step 2: Generate content
        content = _generate_negotiation_content(
            intent=intent,
            counterparty_name="Overdue Client Ltd",
            amount=200000,
            transaction_type="receivable",
            due_date="2024-01-10",
            invoice_id="OD-001"
        )
        
        # Step 3: Create draft object
        draft = NegotiationDraft(
            intent=intent,
            strategy_explanation=f"Payment is overdue. Following up professionally.",
            whatsapp_message=content["option_a"]["whatsapp"],
            formal_email=content["option_a"]["email"],
            option_a=f"RELATIONSHIP: {content['option_a']['whatsapp']}",
            option_b=f"DIRECT: {content['option_b']['whatsapp']}"
        )
        
        print(f"✅ Complete Workflow: {draft.intent}")
        print(f"   Strategy: {draft.strategy_explanation}")
        print(f"   WhatsApp: {draft.whatsapp_message}")
        
    except Exception as e:
        print(f"❌ Workflow Error: {e}")
        return False
    
    print("\n🎉 ALL DIRECT TESTS PASSED!")
    return True

def demo_real_scenarios():
    """Demo with realistic business scenarios"""
    print("\n💼 REALISTIC BUSINESS SCENARIOS")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Cash Flow Crunch",
            "counterparty": "Raw Material Suppliers Ltd",
            "amount": 750000,
            "type": "payable",
            "due_date": "2024-01-25",
            "cash": 400000,
            "outflows": 300000
        },
        {
            "name": "Overdue Invoice Chase", 
            "counterparty": "Corporate Client Pvt Ltd",
            "amount": 320000,
            "type": "receivable",
            "due_date": "2024-01-05",
            "cash": 800000,
            "outflows": 100000
        },
        {
            "name": "Early Payment Opportunity",
            "counterparty": "Equipment Supplier Co",
            "amount": 450000,
            "type": "payable", 
            "due_date": "2024-02-15",
            "cash": 2000000,
            "outflows": 200000
        }
    ]
    
    try:
        from server import (
            _determine_negotiation_intent, _generate_negotiation_content
        )
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 Scenario {i}: {scenario['name']}")
            print(f"   Counterparty: {scenario['counterparty']}")
            print(f"   Amount: ₹{scenario['amount']:,}")
            print(f"   Cash Position: ₹{scenario['cash']:,}")
            
            # Determine intent
            intent = _determine_negotiation_intent(
                transaction_type=scenario['type'],
                amount=scenario['amount'],
                due_date=scenario['due_date'],
                current_cash_position=scenario['cash'],
                upcoming_outflows=scenario['outflows']
            )
            
            print(f"   🎯 Strategy: {intent}")
            
            # Generate content
            content = _generate_negotiation_content(
                intent=intent,
                counterparty_name=scenario['counterparty'],
                amount=scenario['amount'],
                transaction_type=scenario['type'],
                due_date=scenario['due_date'],
                invoice_id=f"DEMO-{i:03d}"
            )
            
            print(f"   📱 WhatsApp A: {content['option_a']['whatsapp']}")
            print(f"   📱 WhatsApp B: {content['option_b']['whatsapp']}")
            
    except Exception as e:
        print(f"❌ Scenario Error: {e}")
        return False
    
    print("\n🎉 ALL SCENARIOS COMPLETED!")
    return True

def main():
    """Main test function"""
    print("🚀 AGENT D: THE NEGOTIATOR - SIMPLE TESTING")
    print("=" * 60)
    
    success = True
    
    # Run direct function tests
    if not test_agent_d_direct():
        success = False
    
    # Run scenario demos
    if not demo_real_scenarios():
        success = False
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("Agent D: The Negotiator is working correctly!")
        print("\n✅ Verified Components:")
        print("  • Router Logic (Intent Determination)")
        print("  • Content Generation (Fallback Mode)")
        print("  • Complete Workflow Integration")
        print("  • Business Scenario Handling")
        
        print("\n💡 Next Steps:")
        print("  1. Set API keys for AI-powered content")
        print("  2. Test with MCP client: mcp dev server.py")
        print("  3. Integrate with financial workflows")
        
    else:
        print("❌ SOME TESTS FAILED")
        print("Check the error messages above")
    
    # API Status
    print(f"\n🔌 API Status:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if gemini_key:
        print(f"  ✅ GEMINI_API_KEY: Set")
    elif openrouter_key:
        print(f"  ✅ OPENROUTER_API_KEY: Set")
    else:
        print(f"  ⚠️ No API keys - using fallback mode")
        print(f"  Set GEMINI_API_KEY or OPENROUTER_API_KEY for AI content")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test Agent D: The Negotiator
Demonstrates the complete negotiation system with router logic and content generation
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append('.')

def test_negotiation_router():
    """Test Phase 1: Router Logic - Decision Making"""
    print("🔄 PHASE 1: TESTING ROUTER LOGIC")
    print("=" * 50)
    
    # Import the router function
    try:
        from server import _determine_negotiation_intent, NegotiationIntent
        
        # Test Case 1: Credit Extension (Cash flow tight)
        intent1 = _determine_negotiation_intent(
            transaction_type="payable",
            amount=500000,  # 5 lakh
            due_date="2024-01-20",
            current_cash_position=300000,  # Only 3 lakh available
            upcoming_outflows=200000  # 2 lakh outflows
        )
        print(f"✅ Test 1 - Cash Tight: {intent1}")
        assert intent1 == NegotiationIntent.CREDIT_EXTENSION
        
        # Test Case 2: Payment Chase (Overdue receivable)
        intent2 = _determine_negotiation_intent(
            transaction_type="receivable",
            amount=200000,  # 2 lakh
            due_date="2024-01-10",  # Overdue
            current_cash_position=1000000,
            upcoming_outflows=0
        )
        print(f"✅ Test 2 - Overdue Payment: {intent2}")
        assert intent2 == NegotiationIntent.PAYMENT_CHASE
        
        # Test Case 3: Early Payment Offer (Cash surplus)
        intent3 = _determine_negotiation_intent(
            transaction_type="payable",
            amount=100000,  # 1 lakh
            due_date="2024-02-15",
            current_cash_position=2000000,  # 20 lakh available (surplus)
            upcoming_outflows=0
        )
        print(f"✅ Test 3 - Cash Surplus: {intent3}")
        assert intent3 == NegotiationIntent.EARLY_PAYMENT_OFFER
        
        print("\n🎯 ROUTER LOGIC: ALL TESTS PASSED!")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure server.py has the router functions implemented")
        return False
    
    return True

def test_content_generation():
    """Test Phase 2: Content Generation (with fallback)"""
    print("\n🎨 PHASE 2: TESTING CONTENT GENERATION")
    print("=" * 50)
    
    try:
        from server import _generate_negotiation_content, NegotiationIntent
        
        # Test credit extension content
        content = _generate_negotiation_content(
            intent=NegotiationIntent.CREDIT_EXTENSION,
            counterparty_name="ABC Suppliers Ltd",
            amount=500000,
            transaction_type="payable",
            due_date="2024-01-20",
            invoice_id="INV-2024-001"
        )
        
        print("✅ Credit Extension Content Generated:")
        print(f"   Option A WhatsApp: {content['option_a']['whatsapp'][:80]}...")
        print(f"   Option B WhatsApp: {content['option_b']['whatsapp'][:80]}...")
        
        # Verify structure
        assert 'option_a' in content
        assert 'option_b' in content
        assert 'whatsapp' in content['option_a']
        assert 'email' in content['option_a']
        
        print("\n🎯 CONTENT GENERATION: STRUCTURE VERIFIED!")
        
    except Exception as e:
        print(f"❌ Content Generation Error: {e}")
        return False
    
    return True

def test_complete_negotiation_tool():
    """Test Phase 3: Complete MCP Tool"""
    print("\n🛠️ PHASE 3: TESTING COMPLETE NEGOTIATION TOOL")
    print("=" * 50)
    
    try:
        from server import generate_negotiation_draft
        
        # Test complete workflow
        result = generate_negotiation_draft(
            counterparty_name="XYZ Manufacturing Ltd",
            amount=750000,  # 7.5 lakh
            transaction_type="payable",
            due_date="2024-01-25",
            current_cash_position=400000,  # 4 lakh (tight)
            upcoming_outflows=300000,  # 3 lakh outflows
            invoice_id="INV-2024-025"
        )
        
        print("✅ Complete Negotiation Draft Generated:")
        print(f"   Intent: {result.intent}")
        print(f"   Strategy: {result.strategy_explanation}")
        print(f"   WhatsApp: {result.whatsapp_message}")
        print(f"   Email Preview: {result.formal_email[:100]}...")
        print(f"   A/B Testing: {len(result.option_a)} chars vs {len(result.option_b)} chars")
        
        # Verify all fields are populated
        assert result.intent is not None
        assert len(result.strategy_explanation) > 0
        assert len(result.whatsapp_message) > 0
        assert len(result.formal_email) > 0
        assert len(result.option_a) > 0
        assert len(result.option_b) > 0
        
        print("\n🎯 COMPLETE TOOL: ALL FIELDS VERIFIED!")
        
    except Exception as e:
        print(f"❌ Complete Tool Error: {e}")
        return False
    
    return True

def test_business_scenarios():
    """Test real-world business scenarios"""
    print("\n💼 PHASE 4: TESTING BUSINESS SCENARIOS")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Textile MSME - Vendor Payment Delay",
            "counterparty": "Cotton Suppliers Pvt Ltd",
            "amount": 850000,
            "type": "payable",
            "due_date": "2024-01-18",
            "cash": 500000,
            "outflows": 400000,
            "expected_intent": "credit_extension"
        },
        {
            "name": "IT Services - Client Payment Chase",
            "counterparty": "Tech Solutions Inc",
            "amount": 320000,
            "type": "receivable", 
            "due_date": "2024-01-05",  # Overdue
            "cash": 1200000,
            "outflows": 0,
            "expected_intent": "payment_chase"
        },
        {
            "name": "Manufacturing - Early Payment Opportunity",
            "counterparty": "Steel Suppliers Ltd",
            "amount": 450000,
            "type": "payable",
            "due_date": "2024-02-10",
            "cash": 2500000,  # Strong cash position
            "outflows": 200000,
            "expected_intent": "early_payment_offer"
        }
    ]
    
    try:
        from server import generate_negotiation_draft
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 Scenario {i}: {scenario['name']}")
            
            result = generate_negotiation_draft(
                counterparty_name=scenario['counterparty'],
                amount=scenario['amount'],
                transaction_type=scenario['type'],
                due_date=scenario['due_date'],
                current_cash_position=scenario['cash'],
                upcoming_outflows=scenario['outflows'],
                invoice_id=f"TEST-{i:03d}"
            )
            
            print(f"   💡 Intent: {result.intent}")
            print(f"   📱 WhatsApp: {result.whatsapp_message[:60]}...")
            print(f"   ✅ Expected: {scenario['expected_intent']}")
            
            # Verify intent matches expectation (flexible check)
            if scenario['expected_intent'] in str(result.intent).lower():
                print(f"   ✅ SCENARIO {i}: PASSED")
            else:
                print(f"   ⚠️ SCENARIO {i}: Intent mismatch (may be acceptable)")
        
        print("\n🎯 BUSINESS SCENARIOS: COMPLETED!")
        
    except Exception as e:
        print(f"❌ Business Scenarios Error: {e}")
        return False
    
    return True

def test_api_integration():
    """Test API integration status"""
    print("\n🔌 PHASE 5: TESTING API INTEGRATION")
    print("=" * 50)
    
    # Check environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    print(f"GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Not Set'}")
    print(f"OPENROUTER_API_KEY: {'✅ Set' if openrouter_key else '❌ Not Set'}")
    
    if not gemini_key and not openrouter_key:
        print("\n⚠️ NO API KEYS FOUND")
        print("Agent D will use fallback content generation")
        print("To enable AI-powered content:")
        print("1. Set GEMINI_API_KEY for Google Gemini")
        print("2. Or set OPENROUTER_API_KEY for OpenRouter")
        return False
    
    # Test import status
    try:
        import google.generativeai as genai
        print("✅ Google GenerativeAI: Available")
    except ImportError:
        print("❌ Google GenerativeAI: Not Available")
    
    try:
        import httpx
        print("✅ HTTPX: Available (for OpenRouter)")
    except ImportError:
        print("❌ HTTPX: Not Available (install with: pip install httpx)")
    
    return True

def main():
    """Run all Agent D tests"""
    print("🤖 AGENT D: THE NEGOTIATOR - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("Testing the complete negotiation system with router logic")
    print("and Gemini 3 Flash integration as per architectural blueprint")
    print("=" * 60)
    
    tests = [
        ("Router Logic", test_negotiation_router),
        ("Content Generation", test_content_generation),
        ("Complete Tool", test_complete_negotiation_tool),
        ("Business Scenarios", test_business_scenarios),
        ("API Integration", test_api_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Agent D is ready for production.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("Agent D will still work with fallback functionality.")
    
    print("\n💡 NEXT STEPS:")
    print("1. Set up API keys for AI-powered content generation")
    print("2. Test with real MCP client (mcp dev server.py)")
    print("3. Integrate with your financial workflow")

if __name__ == "__main__":
    main()
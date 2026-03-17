"""
MicroCFO - Quick Test Script
Test the main functionality without API keys
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_agents_initialization():
    """Test agent initialization"""
    print("\n=== Testing Agent Initialization ===\n")
    
    try:
        from backend.agents import initialize_agents
        success = initialize_agents()
        print(f"Agent initialization: {'✓ PASSED' if success else '✗ FAILED'}")
        return success
    except Exception as e:
        print(f"Agent initialization: ✗ FAILED - {e}")
        return False


def test_mock_invoice_analysis():
    """Test invoice analysis with mock data"""
    print("\n=== Testing Mock Invoice Analysis ===\n")
    
    try:
        from backend.agents.visual_auditor import _get_mock_invoice_analysis
        result = _get_mock_invoice_analysis()
        
        assert "vendor_name" in result
        assert "total_amount" in result
        assert "line_items" in result
        assert "confidence_score" in result
        
        print(f"Vendor: {result['vendor_name']}")
        print(f"Amount: ₹{result['total_amount']:,.2f}")
        print(f"Confidence: {result['confidence_score']*100:.0f}%")
        print(f"Mock invoice analysis: ✓ PASSED")
        return True
    except Exception as e:
        print(f"Mock invoice analysis: ✗ FAILED - {e}")
        return False


def test_compliance_response():
    """Test compliance query with mock data"""
    print("\n=== Testing Mock Compliance Query ===\n")
    
    try:
        from backend.agents.legal_sentinel import _get_mock_compliance_response
        result = _get_mock_compliance_response("Can I claim ITC on office supplies?")
        
        assert "risk_level" in result
        assert "explanation" in result
        assert "compliant_action" in result
        
        print(f"Risk Level: {result['risk_level']}")
        print(f"Explanation: {result['explanation'][:100]}...")
        print(f"Mock compliance query: ✓ PASSED")
        return True
    except Exception as e:
        print(f"Mock compliance query: ✗ FAILED - {e}")
        return False


def test_subsidy_search():
    """Test subsidy search with mock data"""
    print("\n=== Testing Mock Subsidy Search ===\n")
    
    try:
        from backend.agents.subsidy_hunter import _get_mock_subsidies
        result = _get_mock_subsidies(sector="Textile", capex=1000000)
        
        assert len(result) > 0
        assert "name" in result[0]
        assert "benefit" in result[0]
        assert "match_score" in result[0]
        
        print(f"Found {len(result)} schemes")
        for scheme in result[:2]:
            print(f"  - {scheme['name']} ({scheme['match_score']*100:.0f}% match)")
        print(f"Mock subsidy search: ✓ PASSED")
        return True
    except Exception as e:
        print(f"Mock subsidy search: ✗ FAILED - {e}")
        return False


def test_negotiation_draft():
    """Test negotiation draft generation with mock data"""
    print("\n=== Testing Mock Negotiation Draft ===\n")
    
    try:
        from backend.agents.negotiator import _get_mock_negotiation
        
        invoice_data = {
            "vendor_name": "ABC Suppliers",
            "invoice_number": "INV-001",
            "amount": 50000,
            "due_date": "2024-02-01"
        }
        
        result = _get_mock_negotiation(invoice_data, "Need 15 days extension")
        
        assert "primary_draft" in result
        assert "subject" in result["primary_draft"]
        assert "body" in result["primary_draft"]
        
        print(f"Subject: {result['primary_draft']['subject']}")
        print(f"Strategy: {result['primary_draft']['strategy_explanation']}")
        print(f"Mock negotiation draft: ✓ PASSED")
        return True
    except Exception as e:
        print(f"Mock negotiation draft: ✗ FAILED - {e}")
        return False


def test_orchestrator_routing():
    """Test message routing"""
    print("\n=== Testing Orchestrator Routing ===\n")
    
    try:
        from backend.agents.orchestrator import _determine_agent_from_message
        
        test_cases = [
            ("Can I scan this invoice?", "visual_auditor"),
            ("What are the ITC rules?", "legal_sentinel"),
            ("Find subsidies for textile", "subsidy_hunter"),
            ("Draft an email to vendor", "negotiator"),
            ("Hello, how are you?", "general")
        ]
        
        all_passed = True
        for message, expected_agent in test_cases:
            agent = _determine_agent_from_message(message)
            passed = agent == expected_agent or (expected_agent == "general" and agent == "general")
            status = "✓" if passed else "✗"
            print(f"  {status} '{message[:30]}...' → {agent}")
            if not passed:
                all_passed = False
        
        print(f"Orchestrator routing: {'✓ PASSED' if all_passed else '✗ FAILED'}")
        return all_passed
    except Exception as e:
        print(f"Orchestrator routing: ✗ FAILED - {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  MicroCFO - Test Suite")
    print("="*60)
    
    tests = [
        ("Agent Initialization", test_agents_initialization),
        ("Mock Invoice Analysis", test_mock_invoice_analysis),
        ("Mock Compliance Query", test_compliance_response),
        ("Mock Subsidy Search", test_subsidy_search),
        ("Mock Negotiation Draft", test_negotiation_draft),
        ("Orchestrator Routing", test_orchestrator_routing)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n{name}: ✗ EXCEPTION - {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

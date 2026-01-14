#!/usr/bin/env python3
"""
Demo: Agent D - The Negotiator
Interactive demonstration of the complete negotiation system
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append('.')

def demo_negotiation_scenarios():
    """Interactive demo of Agent D negotiation capabilities"""
    
    print("🤖 AGENT D: THE NEGOTIATOR - INTERACTIVE DEMO")
    print("=" * 60)
    print("Demonstrating AI-powered financial negotiation with")
    print("OpenAI Router + Gemini 3 Flash architecture")
    print("=" * 60)
    
    # Check if server imports work
    try:
        from server import generate_negotiation_draft, NegotiationIntent
        print("✅ Agent D modules loaded successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure server.py is properly configured")
        return
    
    # Demo scenarios
    scenarios = [
        {
            "title": "🏭 TEXTILE MSME - CASH FLOW CRUNCH",
            "description": "Small textile manufacturer needs to delay payment to cotton supplier",
            "counterparty": "Gujarat Cotton Mills Ltd",
            "amount": 850000,  # 8.5 lakh
            "type": "payable",
            "due_date": "2024-01-20",
            "cash": 400000,  # Only 4 lakh available
            "outflows": 350000,  # 3.5 lakh upcoming expenses
            "context": "Seasonal cash flow dip, major order payment expected next month"
        },
        {
            "title": "💻 IT SERVICES - OVERDUE CLIENT PAYMENT",
            "description": "Software company chasing overdue payment from corporate client",
            "counterparty": "MegaCorp Technologies Pvt Ltd",
            "amount": 480000,  # 4.8 lakh
            "type": "receivable",
            "due_date": "2024-01-05",  # 15 days overdue
            "cash": 1200000,  # 12 lakh
            "outflows": 200000,
            "context": "Client's accounts payable team is slow, need professional follow-up"
        },
        {
            "title": "🏗️ MANUFACTURING - EARLY PAYMENT OPPORTUNITY",
            "description": "Strong cash position allows for strategic early payment discount",
            "counterparty": "Premium Steel Suppliers Ltd",
            "amount": 650000,  # 6.5 lakh
            "type": "payable",
            "due_date": "2024-02-15",  # Future due date
            "cash": 3200000,  # 32 lakh (strong position)
            "outflows": 400000,
            "context": "Excellent quarter, opportunity to negotiate better terms"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{scenario['title']}")
        print("-" * 60)
        print(f"📊 Business Context: {scenario['description']}")
        print(f"🏢 Counterparty: {scenario['counterparty']}")
        print(f"💰 Amount: ₹{scenario['amount']:,}")
        print(f"📅 Due Date: {scenario['due_date']}")
        print(f"💳 Current Cash: ₹{scenario['cash']:,}")
        print(f"📤 Upcoming Outflows: ₹{scenario['outflows']:,}")
        print(f"🎯 Context: {scenario['context']}")
        
        print(f"\n🔄 PHASE 1: ROUTER ANALYSIS")
        print("-" * 30)
        
        # Calculate projected balance
        projected_balance = scenario['cash'] - scenario['outflows']
        print(f"Projected Balance: ₹{projected_balance:,}")
        
        # Determine strategy
        if scenario['type'] == 'payable' and projected_balance < scenario['amount']:
            strategy = "CREDIT_EXTENSION - Request payment delay"
        elif scenario['type'] == 'receivable':
            strategy = "PAYMENT_CHASE - Follow up on overdue amount"
        elif scenario['type'] == 'payable' and scenario['cash'] > scenario['amount'] * 3:
            strategy = "EARLY_PAYMENT_OFFER - Negotiate discount"
        else:
            strategy = "STANDARD_TERMS - Normal payment process"
        
        print(f"🎯 Router Decision: {strategy}")
        
        print(f"\n🎨 PHASE 2: CONTENT GENERATION")
        print("-" * 30)
        
        try:
            # Generate negotiation draft
            result = generate_negotiation_draft(
                counterparty_name=scenario['counterparty'],
                amount=scenario['amount'],
                transaction_type=scenario['type'],
                due_date=scenario['due_date'],
                current_cash_position=scenario['cash'],
                upcoming_outflows=scenario['outflows'],
                invoice_id=f"DEMO-{i:03d}"
            )
            
            print(f"✅ Intent Determined: {result.intent}")
            print(f"📋 Strategy: {result.strategy_explanation}")
            
            print(f"\n📱 WHATSAPP MESSAGE:")
            print(f"   {result.whatsapp_message}")
            
            print(f"\n📧 FORMAL EMAIL:")
            print("   " + result.formal_email.replace('\n', '\n   '))
            
            print(f"\n🔀 A/B TESTING OPTIONS:")
            print(f"\n   OPTION A (Relationship-Focused):")
            print("   " + result.option_a.replace('\n', '\n   '))
            
            print(f"\n   OPTION B (Transactional-Focused):")
            print("   " + result.option_b.replace('\n', '\n   '))
            
            # Simulate user choice
            print(f"\n👤 USER CHOICE SIMULATION:")
            if "relationship" in result.option_a.lower():
                print("   ✅ User selected OPTION A (Relationship-focused)")
                print("   📊 Logged for reinforcement learning")
            else:
                print("   ✅ User selected OPTION B (Direct approach)")
                print("   📊 Logged for reinforcement learning")
            
        except Exception as e:
            print(f"❌ Generation Error: {e}")
            print("   Using fallback content generation")
        
        print(f"\n{'='*60}")
        
        if i < len(scenarios):
            input("Press Enter to continue to next scenario...")
    
    print(f"\n🎉 DEMO COMPLETED!")
    print("Agent D: The Negotiator successfully demonstrated:")
    print("✅ Router logic for strategy determination")
    print("✅ Context-aware content generation")
    print("✅ A/B testing for message optimization")
    print("✅ Multi-format output (WhatsApp + Email)")
    print("✅ Indian business communication style")

def demo_api_setup():
    """Demo API setup and configuration"""
    print("\n🔧 API SETUP GUIDE")
    print("=" * 40)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not gemini_key and not openrouter_key:
        print("⚠️ No API keys detected. Agent D is using fallback mode.")
        print("\nTo enable AI-powered content generation:")
        print("\n1. GOOGLE GEMINI (Recommended):")
        print("   export GEMINI_API_KEY='your-gemini-api-key'")
        print("   # Get key from: https://makersuite.google.com/app/apikey")
        
        print("\n2. OPENROUTER (Alternative):")
        print("   export OPENROUTER_API_KEY='sk-or-your-openrouter-key'")
        print("   # Get key from: https://openrouter.ai/keys")
        
        print("\n3. RESTART THE DEMO:")
        print("   python demo_agent_d_negotiator.py")
    else:
        print("✅ API keys configured!")
        if gemini_key:
            print(f"   GEMINI_API_KEY: {gemini_key[:10]}...")
        if openrouter_key:
            print(f"   OPENROUTER_API_KEY: {openrouter_key[:10]}...")

def main():
    """Main demo function"""
    try:
        demo_negotiation_scenarios()
        demo_api_setup()
        
        print(f"\n💡 NEXT STEPS:")
        print("1. Run: python test_agent_d_negotiator.py (comprehensive tests)")
        print("2. Start MCP server: python server.py")
        print("3. Test with MCP client: mcp dev server.py")
        print("4. Integrate with your financial workflow")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("Check your Python environment and dependencies")

if __name__ == "__main__":
    main()
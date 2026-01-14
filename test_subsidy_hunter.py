#!/usr/bin/env python3
"""
Test script for Agent C: The Subsidy Hunter
Tests scheme-aware ingestion, vector search, and benefit calculation
"""

import json
from scheme_ingestion import SchemeDocumentProcessor, SchemeSplitter
from scheme_database import SchemeVectorDB

def test_scheme_splitter():
    """Test the scheme-aware text splitter"""
    print("🧪 Testing Scheme Text Splitter...")
    
    sample_scheme_text = """
Scheme: PMFME (PM Formalisation of Micro Food Processing Enterprises)

Objective
To enhance the competitiveness of individual micro-enterprises in the unorganized segment of the food processing industry.

Eligibility Criteria
1. Individual micro-enterprises with investment up to Rs. 10 lakh
2. Existing food processing units
3. Self Help Group (SHG) members
4. Minimum investment of Rs. 2 lakh for individual units

Quantum of Assistance
- Capital subsidy @ 35% of the eligible project cost
- Maximum subsidy of Rs. 10 lakh per beneficiary
- Credit linked subsidy for working capital

Application Process
Apply through Common Service Centers or online portal with project report and required documents.
    """
    
    splitter = SchemeSplitter()
    chunks = splitter.split_scheme_text(sample_scheme_text, "PMFME")
    
    print(f"   ✅ Generated {len(chunks)} scheme chunks")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"   Chunk {i} ({chunk.chunk_type}):")
        print(f"     Scheme: {chunk.scheme_name}")
        print(f"     Sector: {chunk.target_sector}")
        print(f"     Min Investment: ₹{chunk.min_investment:,.0f}" if chunk.min_investment else "     Min Investment: None")
        print(f"     Benefit Type: {chunk.benefit_type}")
        print(f"     Benefit %: {chunk.benefit_percentage}%" if chunk.benefit_percentage else "     Benefit %: None")
        print(f"     Max Benefit: ₹{chunk.max_benefit_amount:,.0f}" if chunk.max_benefit_amount else "     Max Benefit: None")
        print(f"     Text: {chunk.text[:80]}...")
        print()
    
    return chunks

def test_scheme_database(chunks):
    """Test scheme database operations"""
    print("🧪 Testing Scheme Database...")
    
    # Initialize scheme DB
    scheme_db = SchemeVectorDB(db_path="./test_scheme_db")
    
    # Add chunks
    scheme_db.add_scheme_chunks(chunks)
    print(f"   ✅ Added {len(chunks)} chunks to scheme database")
    
    # Test eligible scheme search
    print("\n   Testing eligible scheme search:")
    test_scenarios = [
        {
            "sector": "food_processing",
            "investment": 500000,  # 5 lakh
            "description": "Small food processing unit"
        },
        {
            "sector": "textile",
            "investment": 50000000,  # 5 crore
            "description": "Large textile manufacturing"
        },
        {
            "sector": "manufacturing",
            "investment": 1000000,  # 10 lakh
            "description": "Medium manufacturing unit"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n     Scenario: {scenario['description']}")
        print(f"     Sector: {scenario['sector']}, Investment: ₹{scenario['investment']:,.0f}")
        
        results = scheme_db.search_eligible_schemes(
            user_sector=scenario['sector'],
            user_investment=scenario['investment'],
            n_results=2
        )
        
        for j, result in enumerate(results, 1):
            scheme_name = result['metadata'].get('scheme_name', 'Unknown')
            benefit_type = result['metadata'].get('benefit_type', 'Unknown')
            similarity = 1 - result.get('distance', 1)
            print(f"       {j}. {scheme_name} ({benefit_type}) - Relevance: {similarity:.3f}")
            
            # Test benefit calculation
            benefit_calc = scheme_db.calculate_benefit(result, scenario['investment'])
            print(f"          Estimated Benefit: ₹{benefit_calc['estimated_benefit']:,.0f}")
            print(f"          Calculation: {benefit_calc['calculation_method']}")
    
    return scheme_db

def test_mcp_integration():
    """Test MCP server integration for Agent C"""
    print("🧪 Testing Agent C MCP Integration...")
    
    try:
        # Import server components
        from server import find_applicable_subsidies, scan_invoice_document
        
        # Test subsidy finder
        test_queries = [
            {"sector": "textile", "amount": 50000000, "description": "Large textile investment"},
            {"sector": "food_processing", "amount": 500000, "description": "Small food processing"},
            {"sector": "technology", "amount": 2000000, "description": "Tech startup"},
            {"sector": "manufacturing", "amount": 1000000, "description": "Manufacturing unit"}
        ]
        
        for query in test_queries:
            print(f"\n   Query: {query['description']}")
            print(f"   Sector: {query['sector']}, Amount: ₹{query['amount']:,.0f}")
            try:
                result = find_applicable_subsidies(query['sector'], query['amount'])
                print(f"   Result: {result[:200]}...")
            except Exception as e:
                print(f"   Error: {e}")
        
        # Test proactive trigger
        print(f"\n   Testing Proactive Trigger (Agent A -> Agent C):")
        try:
            # Simulate machinery invoice
            invoice = scan_invoice_document("https://example.com/machinery-invoice.jpg")
            print(f"   Invoice processed: {invoice.vendor_name}")
            print(f"   Line items: {len(invoice.line_items)} items")
            
            # Check for subsidy alert
            subsidy_alerts = [item for item in invoice.line_items if "SUBSIDY ALERT" in item]
            if subsidy_alerts:
                print(f"   ✅ Proactive trigger worked: {subsidy_alerts[0]}")
            else:
                print(f"   ⚠️ No proactive trigger detected")
                
        except Exception as e:
            print(f"   Error in proactive trigger: {e}")
    
    except ImportError as e:
        print(f"   ❌ MCP server import failed: {e}")

def test_benefit_calculations():
    """Test benefit calculation accuracy"""
    print("🧪 Testing Benefit Calculations...")
    
    # Mock scheme data for testing
    test_schemes = [
        {
            'metadata': {
                'scheme_name': 'PMFME',
                'benefit_percentage': '35',
                'max_benefit_amount': '1000000',
                'benefit_type': 'capital_subsidy'
            },
            'text': 'Capital subsidy @ 35% of project cost, maximum Rs. 10 lakh'
        },
        {
            'metadata': {
                'scheme_name': 'PLI Textiles',
                'benefit_percentage': '15',
                'max_benefit_amount': '50000000',
                'benefit_type': 'incentive'
            },
            'text': 'Incentive @ 15% on incremental sales'
        }
    ]
    
    scheme_db = SchemeVectorDB(db_path="./test_scheme_db")
    
    test_investments = [500000, 2000000, 10000000]  # 5L, 20L, 1Cr
    
    for investment in test_investments:
        print(f"\n   Investment: ₹{investment:,.0f}")
        
        for scheme in test_schemes:
            benefit_calc = scheme_db.calculate_benefit(scheme, investment)
            
            print(f"     {benefit_calc['scheme_name']}:")
            print(f"       Estimated Benefit: ₹{benefit_calc['estimated_benefit']:,.0f}")
            print(f"       Method: {benefit_calc['calculation_method']}")
            if benefit_calc['notes']:
                print(f"       Notes: {', '.join(benefit_calc['notes'])}")

def main():
    """Run all tests for Agent C"""
    print("🚀 Starting Agent C: Subsidy Hunter Test Suite\n")
    
    # Test 1: Scheme Splitter
    chunks = test_scheme_splitter()
    print("-" * 60)
    
    # Test 2: Scheme Database
    scheme_db = test_scheme_database(chunks)
    print("-" * 60)
    
    # Test 3: Benefit Calculations
    test_benefit_calculations()
    print("-" * 60)
    
    # Test 4: MCP Integration
    test_mcp_integration()
    print("-" * 60)
    
    print("✅ All Agent C tests completed!")
    print("\nNext steps:")
    print("1. Run 'python setup_scheme_db.py' to initialize with comprehensive scheme data")
    print("2. Test the enhanced MCP server with 'python server.py'")
    print("3. Try the proactive trigger by scanning machinery invoices")
    print("4. Verify benefit calculations match scheme guidelines")

if __name__ == "__main__":
    main()
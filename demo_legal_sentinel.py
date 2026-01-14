#!/usr/bin/env python3
"""
Demo script for Legal Sentinel functionality
Shows the complete workflow of the structure-aware RAG system
"""

import json
from legal_ingestion import LegalDocumentProcessor
from vector_database import LegalVectorDB
from server import check_compliance_law, get_user_profile, LegalRisk, RiskLevel

def demo_legal_sentinel():
    """Demonstrate the Legal Sentinel system"""
    print("🚀 MicroCFO Legal Sentinel Demo")
    print("=" * 50)
    
    # Initialize components
    print("\n📚 Initializing Legal Database...")
    vector_db = LegalVectorDB()
    stats = vector_db.get_stats()
    print(f"   Database loaded with {stats['total_chunks']} legal chunks")
    print(f"   Law types: {', '.join(stats['law_type_distribution'].keys())}")
    
    # Show user profile
    print("\n👤 User Profile:")
    try:
        from server import mcp
        profile_resource = mcp.resources["microcfo://data/profile"]
        profile_data = profile_resource()
        profile = json.loads(profile_data)
        for key, value in profile.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   Using mock profile due to: {e}")
        profile = {
            "business_name": "Sample Business Ltd",
            "turnover_tier": "< 5Cr",
            "gst_registration_type": "Regular",
            "industry_code": "Textile"
        }
        for key, value in profile.items():
            print(f"   {key}: {value}")
    
    # Demo queries with different scenarios
    demo_queries = [
        {
            "query": "Can I claim input tax credit on office supplies if my turnover is 3 crores?",
            "scenario": "Small business (< 5Cr) asking about ITC eligibility"
        },
        {
            "query": "What are the blocked credits under Section 17(5)?",
            "scenario": "Specific section query about blocked ITC"
        },
        {
            "query": "Late filing penalty for GST returns",
            "scenario": "Penalty information query"
        },
        {
            "query": "Section 44AD presumptive taxation eligibility",
            "scenario": "Income Tax presumptive scheme query"
        }
    ]
    
    print("\n🔍 Legal Compliance Queries:")
    print("-" * 50)
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n{i}. Scenario: {demo['scenario']}")
        print(f"   Query: \"{demo['query']}\"")
        
        try:
            # This simulates what happens inside the MCP tool
            result = check_compliance_law(demo['query'])
            
            # Display results
            risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
            print(f"   Risk Level: {risk_emoji.get(result.risk_level, '⚪')} {result.risk_level}")
            print(f"   Relevant Section: {result.relevant_section}")
            print(f"   Compliant Action: {result.compliant_action}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Demo vector search capabilities
    print(f"\n🔎 Vector Database Search Demo:")
    print("-" * 50)
    
    search_queries = [
        "input tax credit eligibility",
        "turnover threshold 5 crore",
        "blocked credits motor vehicle"
    ]
    
    for query in search_queries:
        print(f"\nSemantic Search: \"{query}\"")
        results = vector_db.semantic_search(query, n_results=2)
        
        for j, result in enumerate(results, 1):
            section = result['metadata'].get('section_number', 'Unknown')
            law_type = result['metadata'].get('law_type', 'Unknown')
            similarity = 1 - result.get('distance', 1)
            print(f"   {j}. Section {section} ({law_type}) - Similarity: {similarity:.3f}")
            print(f"      Preview: {result['text'][:80]}...")
    
    # Show structure-aware processing
    print(f"\n🏗️ Structure-Aware Processing Demo:")
    print("-" * 50)
    
    sample_legal_text = """
Section 18 - Input tax credit on capital goods

(1) A registered person shall be entitled to take credit of input tax charged on capital goods used in the course or furtherance of his business.

Provided that where the capital goods are used partly for effecting taxable supplies including zero-rated supplies under this Act or under the Integrated Goods and Services Tax Act, 2017 and partly for effecting exempt supplies under the said Acts, the amount of credit shall be restricted.

(a) the registered person shall determine the value of exempt supplies made during a tax period;
(b) the credit attributable to exempt supplies shall be calculated.
    """
    
    processor = LegalDocumentProcessor()
    chunks = processor.splitter.split_legal_text(sample_legal_text, "GST")
    
    print(f"   Input: Legal text with Section 18, proviso, and sub-clauses")
    print(f"   Output: {len(chunks)} smart chunks generated")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"   Chunk {i}: Section {chunk.section_number}, Type: {chunk.chunk_type}")
        if chunk.turnover_threshold:
            print(f"            Turnover threshold: ₹{chunk.turnover_threshold:,.0f}")
    
    print(f"\n✅ Demo completed!")
    print(f"   The Legal Sentinel successfully demonstrates:")
    print(f"   • Structure-aware legal text processing")
    print(f"   • Context-aware compliance filtering")
    print(f"   • Turnover-based exemption detection")
    print(f"   • Conservative CA-style interpretations")

if __name__ == "__main__":
    demo_legal_sentinel()
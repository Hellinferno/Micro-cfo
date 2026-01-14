#!/usr/bin/env python3
"""
Test script for Legal Sentinel functionality
"""

import json
from legal_ingestion import LegalDocumentProcessor, LegalTextSplitter
from vector_database import LegalVectorDB
from sentinel_monitor import LegalSentinel

def test_text_splitter():
    """Test the legal text splitter"""
    print("🧪 Testing Legal Text Splitter...")
    
    sample_text = """
Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged on any supply of goods or services or both to him which are used or intended to be used in the course or furtherance of his business.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless the turnover exceeds 5 crore.

Provided that where the goods against an invoice are received in lots or instalments, the registered person shall be entitled to take credit upon receipt of the last lot or instalment.

(a) he is in possession of a tax invoice or debit note issued by a supplier registered under this Act;
(b) he has received the goods or services or both.

Section 17 - Apportionment of credit and blocked credits

(5) Input tax credit shall not be available for motor vehicles for transportation of persons.
    """
    
    splitter = LegalTextSplitter()
    chunks = splitter.split_legal_text(sample_text, "GST")
    
    print(f"   ✅ Generated {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"   Chunk {i}:")
        print(f"     Section: {chunk.section_number}")
        print(f"     Type: {chunk.chunk_type}")
        print(f"     Turnover Threshold: {chunk.turnover_threshold}")
        print(f"     Text: {chunk.text[:100]}...")
        print()
    
    return chunks

def test_vector_database(chunks):
    """Test vector database operations"""
    print("🧪 Testing Vector Database...")
    
    # Initialize vector DB
    vector_db = LegalVectorDB(db_path="./test_legal_db")
    
    # Add chunks
    vector_db.add_chunks(chunks)
    print(f"   ✅ Added {len(chunks)} chunks to database")
    
    # Test semantic search
    print("\n   Testing semantic search:")
    queries = [
        "input tax credit eligibility",
        "blocked credits",
        "turnover threshold"
    ]
    
    for query in queries:
        results = vector_db.semantic_search(query, n_results=2)
        print(f"     Query: '{query}' -> {len(results)} results")
        for result in results:
            section = result['metadata'].get('section_number', 'Unknown')
            distance = result.get('distance', 0)
            print(f"       Section {section} (similarity: {1-distance:.3f})")
    
    # Test keyword search
    print("\n   Testing keyword search:")
    results = vector_db.keyword_search("16")
    print(f"     Section 16 search -> {len(results)} results")
    
    # Test hybrid search with turnover filter
    print("\n   Testing hybrid search with turnover filter:")
    results = vector_db.hybrid_search(
        "input tax credit", 
        n_results=3, 
        max_turnover=40000000  # 4 crores
    )
    print(f"     Hybrid search (max 4Cr turnover) -> {len(results)} results")
    
    return vector_db

def test_mcp_integration():
    """Test MCP server integration"""
    print("🧪 Testing MCP Server Integration...")
    
    try:
        # Import server components
        from server import check_compliance_law, mcp
        
        # Test user profile resource
        try:
            profile_resource = mcp.resources["microcfo://data/profile"]
            profile = profile_resource()
            print(f"   ✅ User profile: {json.loads(profile)['business_name']}")
        except Exception as e:
            print(f"   ⚠️ Profile resource test: {e}")
        
        # Test compliance queries
        test_queries = [
            "Can I claim input tax credit on office supplies?",
            "What is the penalty for late filing?",
            "Section 16 eligibility conditions",
            "Blocked credits for motor vehicles"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            try:
                result = check_compliance_law(query)
                print(f"     Risk Level: {result.risk_level}")
                print(f"     Section: {result.relevant_section}")
                print(f"     Action: {result.compliant_action[:100]}...")
            except Exception as e:
                print(f"     Error: {e}")
    
    except ImportError as e:
        print(f"   ❌ MCP server import failed: {e}")

def test_sentinel_monitoring():
    """Test sentinel monitoring functionality"""
    print("🧪 Testing Sentinel Monitoring...")
    
    try:
        sentinel = LegalSentinel(db_path="./test_legal_db")
        
        # Test notification processing
        mock_notification = {
            'id': 'test_notification_001',
            'title': 'New GST Notification for Textile Industry',
            'url': 'https://example.com/notification.pdf',
            'source': 'CBIC',
            'law_type': 'GST',
            'date_found': '2024-01-15T10:00:00'
        }
        
        # Test user relevance check
        sample_profiles = [
            {
                'business_name': 'Textile Mills Ltd',
                'industry_code': 'textile',
                'turnover_tier': '5-20Cr'
            },
            {
                'business_name': 'Software Company',
                'industry_code': 'technology',
                'turnover_tier': '< 5Cr'
            }
        ]
        
        relevant_users = sentinel.check_user_relevance(mock_notification, sample_profiles)
        print(f"   ✅ Found {len(relevant_users)} relevant users for notification")
        
        for user in relevant_users:
            print(f"     - {user['business_name']} ({user['industry_code']})")
        
        # Test alert generation
        if relevant_users:
            print(f"\n   Testing alert generation:")
            sentinel.send_whatsapp_alert(relevant_users[0], mock_notification)
    
    except Exception as e:
        print(f"   ❌ Sentinel test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Legal Sentinel Test Suite\n")
    
    # Test 1: Text Splitter
    chunks = test_text_splitter()
    print("-" * 60)
    
    # Test 2: Vector Database
    vector_db = test_vector_database(chunks)
    print("-" * 60)
    
    # Test 3: MCP Integration
    test_mcp_integration()
    print("-" * 60)
    
    # Test 4: Sentinel Monitoring
    test_sentinel_monitoring()
    print("-" * 60)
    
    print("✅ All tests completed!")
    print("\nNext steps:")
    print("1. Run 'python setup_legal_db.py' to initialize with sample data")
    print("2. Run 'python server.py' to start the MCP server")
    print("3. Test with 'mcp dev server.py' in another terminal")
    print("4. Run 'python sentinel_monitor.py run-once' to test monitoring")

if __name__ == "__main__":
    main()
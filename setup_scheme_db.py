#!/usr/bin/env python3
"""
Setup script for Scheme Database
Initializes the vector database with sample government schemes
"""

from scheme_ingestion import SchemeDocumentProcessor
from scheme_database import SchemeVectorDB
import os

def setup_sample_schemes():
    """Setup sample government schemes for testing"""
    
    schemes = [
        {
            "name": "PLI Textiles",
            "content": """
Scheme: Production Linked Incentive (PLI) for Textiles

Objective
To promote manufacturing of Man-Made Fibre (MMF) apparel, MMF fabrics and technical textiles in India and boost exports.

Eligibility Criteria
1. Company incorporated in India under Companies Act
2. Minimum investment of Rs. 300 crore for MMF apparel and fabrics
3. Minimum investment of Rs. 100 crore for technical textiles
4. Achieve minimum turnover thresholds as prescribed
5. Fresh investment in plant, machinery, equipment, and associated utilities

Quantum of Assistance
- Incentive @ 15% on incremental sales over base year for MMF apparel and fabrics
- Incentive @ 11% on incremental sales over base year for technical textiles
- Maximum incentive of Rs. 500 crore per company over 5 years
- Additional capital subsidy up to 25% of project cost for MSME units

Application Process
Submit applications online through designated portal with detailed project report, financial projections, and bank guarantee.
            """
        },
        {
            "name": "PMFME",
            "content": """
Scheme: PM Formalisation of Micro Food Processing Enterprises (PMFME)

Objective
To enhance competitiveness of individual micro-enterprises in the unorganized segment of food processing industry and promote formalization.

Eligibility Criteria
1. Individual micro-enterprises with investment up to Rs. 10 lakh
2. Existing unregistered food processing units
3. Self Help Group (SHG) members engaged in food processing
4. Farmer Producer Organizations (FPOs) with food processing activities
5. Cooperatives engaged in food processing

Quantum of Assistance
- Capital subsidy @ 35% of the eligible project cost
- Maximum subsidy of Rs. 10 lakh per beneficiary
- Credit linked subsidy for working capital requirements
- Seed capital for SHGs @ Rs. 40,000 per SHG with maximum 15 members

Application Process
Apply through Common Service Centers (CSCs) or online portal with project report, cost estimates, and required documents.
            """
        },
        {
            "name": "TUFS",
            "content": """
Scheme: Technology Upgradation Fund Scheme (TUFS) for Textiles

Objective
To facilitate technology upgradation of the textile industry by providing subsidized credit for modernization and expansion.

Eligibility Criteria
1. Textile units engaged in spinning, weaving, processing, garmenting, and technical textiles
2. Minimum investment of Rs. 25 lakh for plant and machinery
3. Units should be commercially viable and technically feasible
4. Compliance with environmental and labor regulations

Quantum of Assistance
- Capital subsidy @ 25% for plant and machinery (North East: 30%)
- Maximum subsidy of Rs. 30 crore per unit
- Interest reimbursement @ 5% for 7 years on term loans
- Additional 5% subsidy for units in Aspirational Districts

Application Process
Submit application to designated banks with detailed project report, environmental clearance, and technical feasibility study.
            """
        },
        {
            "name": "Startup India",
            "content": """
Scheme: Startup India Initiative

Objective
To build a strong ecosystem for nurturing innovation and startups in the country that will drive sustainable economic growth.

Eligibility Criteria
1. Entity incorporated as private limited company or registered as partnership firm or LLP
2. Up to 10 years from date of incorporation/registration
3. Annual turnover not exceeding Rs. 100 crore in any financial year
4. Working towards innovation, development, deployment of new products, processes or services
5. Not formed by splitting up or reconstruction of existing business

Quantum of Assistance
- Tax exemption for 3 consecutive years out of first 10 years
- Capital gains tax exemption on investment in startups
- Self-certification under labor and environment laws
- Fast-track patent examination with 80% fee reduction
- Fund of Funds with corpus of Rs. 10,000 crore for equity funding

Application Process
Register on Startup India portal, obtain recognition certificate, and apply for specific benefits through designated channels.
            """
        },
        {
            "name": "MSME Credit Guarantee",
            "content": """
Scheme: Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)

Objective
To facilitate flow of credit to the micro and small enterprise sector without collateral/third party guarantees.

Eligibility Criteria
1. New and existing micro and small enterprises
2. Manufacturing enterprises with investment up to Rs. 10 crore in plant and machinery
3. Service enterprises with investment up to Rs. 5 crore in equipment
4. Credit facility up to Rs. 5 crore per borrowing unit
5. Unit should not be in default to any bank/financial institution

Quantum of Assistance
- Guarantee coverage up to 85% of credit facility for micro enterprises
- Guarantee coverage up to 75% of credit facility for small enterprises
- Maximum guarantee of Rs. 4.25 crore for micro and Rs. 3.75 crore for small enterprises
- Annual guarantee fee ranging from 0.75% to 1.5% of guaranteed amount

Application Process
Apply through member lending institutions (banks/NBFCs) with business plan and required documentation.
            """
        }
    ]
    
    return schemes

def main():
    """Main setup function"""
    print("🚀 Setting up Scheme Database...")
    
    # Initialize components
    processor = SchemeDocumentProcessor()
    scheme_db = SchemeVectorDB()
    
    # Get sample schemes
    sample_schemes = setup_sample_schemes()
    
    total_chunks = 0
    
    for scheme_data in sample_schemes:
        scheme_name = scheme_data["name"]
        content = scheme_data["content"]
        
        print(f"\n📄 Processing {scheme_name}...")
        
        # Process the scheme content
        chunks = processor.process_scheme_text(content, scheme_name)
        print(f"   Generated {len(chunks)} chunks")
        
        # Add to scheme database
        scheme_db.add_scheme_chunks(chunks)
        total_chunks += len(chunks)
        
        # Show sample chunks
        for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
            print(f"   Chunk {i+1}: {chunk.chunk_type.title()}")
            print(f"            Sector: {chunk.target_sector}")
            if chunk.min_investment:
                print(f"            Min Investment: ₹{chunk.min_investment:,.0f}")
            if chunk.benefit_percentage:
                print(f"            Benefit: {chunk.benefit_percentage}%")
    
    print(f"\n✅ Setup complete!")
    print(f"   Total chunks added: {total_chunks}")
    
    # Show database stats
    stats = scheme_db.get_scheme_stats()
    print(f"   Database location: {stats['db_path']}")
    print(f"   Sector distribution: {stats['sector_distribution']}")
    print(f"   Benefit types: {stats['benefit_type_distribution']}")
    
    # Test search functionality
    print(f"\n🔍 Testing scheme search functionality...")
    
    test_scenarios = [
        {"sector": "textile", "investment": 50000000, "query": "textile manufacturing subsidy"},
        {"sector": "food_processing", "investment": 500000, "query": "food processing micro enterprise"},
        {"sector": "technology", "investment": 2000000, "query": "startup funding scheme"},
    ]
    
    for scenario in test_scenarios:
        print(f"\n   Scenario: {scenario['sector'].title()} sector, ₹{scenario['investment']:,.0f} investment")
        results = scheme_db.search_eligible_schemes(
            user_sector=scenario['sector'],
            user_investment=scenario['investment'],
            query=scenario['query'],
            n_results=2
        )
        
        for i, result in enumerate(results, 1):
            scheme_name = result['metadata'].get('scheme_name', 'Unknown')
            benefit_type = result['metadata'].get('benefit_type', 'Unknown')
            similarity = 1 - result.get('distance', 1)
            
            print(f"     {i}. {scheme_name} ({benefit_type}) - Relevance: {similarity:.3f}")
            
            # Calculate potential benefit
            benefit_calc = scheme_db.calculate_benefit(result, scenario['investment'])
            if benefit_calc['estimated_benefit'] > 0:
                print(f"        Estimated Benefit: ₹{benefit_calc['estimated_benefit']:,.0f}")
    
    print(f"\n🎉 Scheme Database setup completed successfully!")
    print(f"   Agent C: The Subsidy Hunter is now ready with real scheme data.")

if __name__ == "__main__":
    main()
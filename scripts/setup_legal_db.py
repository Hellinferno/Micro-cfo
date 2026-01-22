#!/usr/bin/env python3
"""
Setup script for Legal Database
Initializes the vector database with sample legal content
"""

from legal_ingestion import LegalDocumentProcessor
from vector_database import LegalVectorDB
import os

def setup_sample_legal_content():
    """Setup sample legal content for testing"""
    
    # Sample GST Act content
    sample_gst_content = """
Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged on any supply of goods or services or both to him which are used or intended to be used in the course or furtherance of his business.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless,—
    (a) he is in possession of a tax invoice or debit note issued by a supplier registered under this Act, or such other tax paying documents as may be prescribed;
    (b) he has received the goods or services or both.

(3) Where the goods against an invoice are received in lots or instalments, the registered person shall be entitled to take credit upon receipt of the last lot or instalment.

Provided that where it is not possible to receive the goods in pursuance of a contract or for any other reason, the registered person shall be entitled to take credit on the basis of the documents referred to in clause (a) of sub-section (2).

Section 17 - Apportionment of credit and blocked credits

(1) The amount of input tax credit available to a registered person in respect of a tax period shall be the amount of eligible input tax reduced by the amount of ineligible input tax.

(5) Notwithstanding anything contained in sub-section (1) of section 16 and subsection (1) of section 18, input tax credit shall not be available in respect of the following, namely:—

(a) motor vehicles for transportation of persons having approved seating capacity of not more than thirteen persons (including the driver), except when they are used for making the following taxable supplies, namely:—
    (i) further supply of such motor vehicles; or
    (ii) transportation of passengers; or
    (iii) imparting training on driving such motor vehicles;

(b) the following supply of goods or services or both—
    (i) food and beverages, outdoor catering, beauty treatment, health services, cosmetic and plastic surgery except where an inward supply of goods or services or both of a particular category is used by a registered person for making an outward taxable supply of the same category of goods or services or both or as an element of a taxable composite or mixed supply;

Section 47 - Late fee for delayed furnishing of returns

Where a registered person fails to furnish the return under section 39 or section 45 by the due date, he shall pay a late fee of one hundred rupees per day during which such failure continues:

Provided that the amount of late fee shall not exceed an amount calculated at one-fourth per cent. of the turnover in the State or Union territory of such person for the relevant tax period:

Provided further that where the return is furnished after the due date but on or before the 15th day of the month succeeding the tax period to which such return relates, the late fee payable shall be two hundred rupees.

Section 122 - Penalty for certain offences

(1) A taxable person who—
    (a) supplies any goods or services or both without issue of any invoice, in violation of the provisions of this Act or the rules made thereunder; or
    (b) issues any invoice or document other than as provided under this Act or the rules made thereunder; or
    (c) fails to account for any tax collected by him; or
    (d) fails to furnish information or documents called for by the officers of central tax or state tax; or
    (e) furnishes false information or documents; or
    (f) obstructs or prevents any officer in discharge of his duties under this Act; or
    (g) transports any taxable goods without the cover of specified documents; or
    (h) suppresses his turnover leading to evasion of tax; or
    (i) fails to register despite being liable to registration; or
    (j) furnishes false information regarding his liability to registration,
shall be liable to a penalty which may extend to ten thousand rupees or an amount equivalent to the tax evaded or the tax not deducted or short deducted or erroneously refunded, whichever is higher.

Notification No. 12/2017 - Central Tax (Rate)

In exercise of the powers conferred by sub-section (1) of section 9 of the Central Goods and Services Tax Act, 2017, the Central Government, on the recommendations of the Council, hereby notifies that the tax on the supply of goods, where the turnover exceeds 5 crore rupees in the preceding financial year, specified in column (3) of the Table below, falling under Chapter, Section, Heading, Sub-heading or Tariff item specified in the corresponding entry in column (2) thereof, shall be levied at the rate specified in the corresponding entry in column (4) of the said Table.

Rule 86B - Restriction on availment of input tax credit

(1) A registered person, whose aggregate turnover in the preceding financial year has exceeded fifty crore rupees, shall not be allowed input tax credit in respect of invoices or debit notes, the details of which have not been uploaded by the suppliers under sub-section (1) of section 37.

(2) The restriction under sub-rule (1) shall not apply to—
    (a) a registered person having aggregate turnover up to fifty crore rupees in the preceding financial year;
    (b) input tax credit availed on the basis of documents other than invoices or debit notes.
    """
    
    # Sample Income Tax content
    sample_income_tax_content = """
Section 44AD - Presumptive taxation scheme for small businesses

(1) Notwithstanding anything to the contrary contained in sections 28 to 43C, in the case of an eligible assessee engaged in an eligible business, a sum equal to eight per cent of the total turnover or gross receipts of the assessee in the previous year on account of such business or, as the case may be, a sum higher than the aforesaid sum claimed to have been earned by the assessee, shall be deemed to be the profits and gains of such business chargeable to income-tax.

Provided that where the total turnover or gross receipts of any previous year exceeds the limit specified under clause (a) or clause (b) of section 44AB, this section shall not apply to the assessee for such previous year and all subsequent previous years.

(2) For the purposes of sub-section (1), "eligible assessee" means—
    (a) an individual or a Hindu undivided family or a partnership firm (other than a limited liability partnership firm), being a resident; and
    (b) whose total turnover or gross receipts in the previous year does not exceed two crore rupees.

Section 44AB - Audit of accounts of certain persons carrying on business or profession

Every person,—
    (a) carrying on business shall, if his total sales, turnover or gross receipts, as the case may be, in business exceed or exceeds one crore rupees in any previous year;
    (b) carrying on profession shall, if his gross receipts in profession exceed fifty lakh rupees in any previous year,
get his accounts of such previous year audited by an accountant before the specified date and furnish by that date the report of such audit in the prescribed form duly signed and verified by such accountant and setting forth such particulars as may be prescribed.
    """
    
    return [
        ("sample_gst.txt", sample_gst_content, "GST"),
        ("sample_income_tax.txt", sample_income_tax_content, "Income Tax")
    ]

def main():
    """Main setup function"""
    print("🚀 Setting up Legal Database...")
    
    # Initialize components
    processor = LegalDocumentProcessor()
    vector_db = LegalVectorDB()
    
    # Get sample content
    sample_files = setup_sample_legal_content()
    
    total_chunks = 0
    
    for filename, content, law_type in sample_files:
        print(f"\n📄 Processing {filename} ({law_type})...")
        
        # Create temporary file
        temp_file = f"temp_{filename}"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        try:
            # Process the content
            chunks = processor.process_text_file(temp_file, law_type)
            print(f"   Generated {len(chunks)} chunks")
            
            # Add to vector database
            vector_db.add_chunks(chunks)
            total_chunks += len(chunks)
            
            # Show sample chunks
            for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
                print(f"   Chunk {i+1}: Section {chunk.section_number}, Type: {chunk.chunk_type}")
                if chunk.turnover_threshold:
                    print(f"            Turnover threshold: ₹{chunk.turnover_threshold:,.0f}")
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    print(f"\n✅ Setup complete!")
    print(f"   Total chunks added: {total_chunks}")
    
    # Show database stats
    stats = vector_db.get_stats()
    print(f"   Database location: {stats['db_path']}")
    print(f"   Law type distribution: {stats['law_type_distribution']}")
    
    # Test search functionality
    print(f"\n🔍 Testing search functionality...")
    
    test_queries = [
        "input tax credit eligibility",
        "late filing penalty",
        "Section 16",
        "turnover threshold"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = vector_db.semantic_search(query, n_results=2)
        for i, result in enumerate(results, 1):
            section = result['metadata'].get('section_number', 'Unknown')
            distance = result.get('distance', 0)
            print(f"     {i}. Section {section} (similarity: {1-distance:.3f})")
    
    print(f"\n🎉 Legal Database setup completed successfully!")
    print(f"   You can now use the MCP server with real legal data.")

if __name__ == "__main__":
    main()
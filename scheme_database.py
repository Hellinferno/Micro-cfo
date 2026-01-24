#!/usr/bin/env python3
"""
Scheme Vector Database for Government Subsidies
Extends the legal vector database for scheme-specific operations
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any
import json
import os
from scheme_ingestion import SchemeChunk

class SchemeVectorDB:
    """Vector database for government scheme chunks"""
    
    def __init__(self, db_path: str = "./scheme_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the scheme vector database
        
        Args:
            db_path: Path to store ChromaDB files
            model_name: Sentence transformer model for embeddings
        """
        self.db_path = db_path
        self.model_name = model_name
        
        self.db_path = db_path
        self.model_name = model_name
        self._client = None
        self._embedding_model = None
        self._collection = None
        
    @property
    def client(self):
        if self._client is None:
            print("Initializing Scheme ChromaDB client...")
            self._client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            print(f"Loading embedding model: {self.model_name}")
            self._embedding_model = SentenceTransformer(self.model_name)
        return self._embedding_model

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="scheme_chunks",
                metadata={"description": "Government scheme chunks with eligibility metadata"}
            )
            print(f"Scheme DB initialized. Collection has {self._collection.count()} documents.")
        return self._collection

    def add_scheme_chunks(self, chunks: List[SchemeChunk]) -> None:
        """
        Add scheme chunks to the vector database
        """
        if not chunks:
            return
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            # Create unique ID
            chunk_id = f"{chunk.scheme_name.replace(' ', '_')}_{chunk.chunk_type}_{i}"
            
            # Prepare metadata (ChromaDB requires string values)
            metadata = {
                "scheme_name": chunk.scheme_name,
                "target_sector": chunk.target_sector or "",
                "min_investment": str(chunk.min_investment) if chunk.min_investment else "",
                "max_investment": str(chunk.max_investment) if chunk.max_investment else "",
                "benefit_type": chunk.benefit_type or "",
                "benefit_percentage": str(chunk.benefit_percentage) if chunk.benefit_percentage else "",
                "max_benefit_amount": str(chunk.max_benefit_amount) if chunk.max_benefit_amount else "",
                "location_restriction": chunk.location_restriction or "",
                "chunk_type": chunk.chunk_type,
                "effective_date": chunk.effective_date or ""
            }
            
            documents.append(chunk.text)
            metadatas.append(metadata)
            ids.append(chunk_id)
        
        # Generate embeddings
        print(f"Generating embeddings for {len(documents)} scheme chunks...")
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        
        print(f"Added {len(chunks)} scheme chunks to vector database.")
    
    def search_eligible_schemes(self, user_sector: str, user_investment: float, 
                               query: str = "", n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for schemes eligible for the user based on sector and investment
        
        Args:
            user_sector: User's business sector
            user_investment: User's planned investment amount
            query: Optional search query
            n_results: Number of results to return
        """
        # Build where clause for filtering
        where_clause = {}
        if user_sector:
            where_clause["target_sector"] = user_sector
        
        # If no specific query, search for eligibility information
        search_query = query if query else f"{user_sector} eligibility subsidy scheme"
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([search_query]).tolist()[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results * 2,  # Get more results for filtering
            where=where_clause if where_clause else None
        )
        
        # Process and filter results
        processed_results = []
        for i in range(len(results['documents'][0])):
            metadata = results['metadatas'][0][i]
            
            # Apply investment filter
            if metadata.get('min_investment'):
                try:
                    min_investment = float(metadata['min_investment'])
                    if user_investment < min_investment:
                        continue  # Skip schemes requiring higher investment
                except ValueError:
                    pass  # Keep schemes without valid min_investment
            
            processed_results.append({
                'text': results['documents'][0][i],
                'metadata': metadata,
                'distance': results['distances'][0][i],
                'id': results['ids'][0][i]
            })
            
            if len(processed_results) >= n_results:
                break
        
        return processed_results
    
    def calculate_benefit(self, scheme_chunk: Dict[str, Any], user_investment: float) -> Dict[str, Any]:
        """
        Calculate potential benefit for user based on scheme details
        """
        metadata = scheme_chunk['metadata']
        text = scheme_chunk['text']
        
        benefit_calculation = {
            'scheme_name': metadata.get('scheme_name', 'Unknown'),
            'benefit_type': metadata.get('benefit_type', 'Unknown'),
            'estimated_benefit': 0,
            'calculation_method': 'Unable to calculate',
            'max_benefit': metadata.get('max_benefit_amount', ''),
            'notes': []
        }
        
        # Calculate based on benefit percentage
        if metadata.get('benefit_percentage'):
            try:
                percentage = float(metadata['benefit_percentage'])
                estimated_benefit = user_investment * (percentage / 100)
                
                benefit_calculation['estimated_benefit'] = estimated_benefit
                benefit_calculation['calculation_method'] = f"{percentage}% of project cost"
                
                # Check against maximum benefit
                if metadata.get('max_benefit_amount'):
                    try:
                        max_benefit = float(metadata['max_benefit_amount'])
                        if estimated_benefit > max_benefit:
                            benefit_calculation['estimated_benefit'] = max_benefit
                            benefit_calculation['notes'].append(f"Capped at maximum benefit of ₹{max_benefit:,.0f}")
                    except ValueError:
                        pass
                        
            except ValueError:
                pass
        
        # If no percentage, try to extract from text
        elif 'quantum' in text.lower() or 'assistance' in text.lower():
            benefit_calculation['calculation_method'] = 'Based on scheme guidelines'
            benefit_calculation['notes'].append('Refer to Quantum of Assistance section for detailed calculation')
        
        return benefit_calculation
    
    def get_scheme_stats(self) -> Dict[str, Any]:
        """Get scheme database statistics"""
        total_count = self.collection.count()
        
        # Get sector distribution
        all_metadata = self.collection.get()['metadatas']
        sectors = {}
        benefit_types = {}
        
        for metadata in all_metadata:
            sector = metadata.get('target_sector', 'unknown')
            if sector:
                sectors[sector] = sectors.get(sector, 0) + 1
            
            benefit_type = metadata.get('benefit_type', 'unknown')
            if benefit_type:
                benefit_types[benefit_type] = benefit_types.get(benefit_type, 0) + 1
        
        return {
            'total_schemes': total_count,
            'sector_distribution': sectors,
            'benefit_type_distribution': benefit_types,
            'db_path': self.db_path
        }


# Example usage and testing
if __name__ == "__main__":
    from scheme_ingestion import SchemeDocumentProcessor
    
    # Initialize scheme DB
    scheme_db = SchemeVectorDB()
    
    # Test with sample scheme data
    sample_scheme_text = """
Scheme: PMFME (PM Formalisation of Micro Food Processing Enterprises)

Objective
To enhance the competitiveness of individual micro-enterprises in the unorganized segment of the food processing industry.

Eligibility Criteria
1. Individual micro-enterprises with investment up to Rs. 10 lakh
2. Existing food processing units
3. Self Help Group (SHG) members
4. Farmer Producer Organizations (FPOs)

Quantum of Assistance
- Capital subsidy @ 35% of the eligible project cost
- Maximum subsidy of Rs. 10 lakh per beneficiary
- Credit linked subsidy for working capital

Application Process
Apply through Common Service Centers or online portal with project report and required documents.
    """
    
    # Process and add to scheme DB
    processor = SchemeDocumentProcessor()
    chunks = processor.process_scheme_text(sample_scheme_text, "PMFME")
    scheme_db.add_scheme_chunks(chunks)
    
    # Test search
    print("\n=== Scheme Search Test ===")
    results = scheme_db.search_eligible_schemes(
        user_sector="food_processing",
        user_investment=500000,  # 5 lakh investment
        query="food processing subsidy"
    )
    
    for result in results:
        print(f"Scheme: {result['metadata']['scheme_name']}")
        print(f"Benefit Type: {result['metadata']['benefit_type']}")
        print(f"Min Investment: {result['metadata']['min_investment']}")
        
        # Calculate benefit
        benefit = scheme_db.calculate_benefit(result, 500000)
        print(f"Estimated Benefit: ₹{benefit['estimated_benefit']:,.0f}")
        print(f"Calculation: {benefit['calculation_method']}")
        print()
    
    # Show stats
    print("\n=== Scheme Database Stats ===")
    stats = scheme_db.get_scheme_stats()
    print(json.dumps(stats, indent=2))
#!/usr/bin/env python3
"""
Phase 2: Vector Database for Legal Chunks
Stores smart chunks with semantic search capabilities
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any
import json
import os
from legal_ingestion import LegalChunk

class LegalVectorDB:
    """Vector database for legal document chunks"""
    
    def __init__(self, db_path: str = "./legal_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector database
        
        Args:
            db_path: Path to store ChromaDB files
            model_name: Sentence transformer model for embeddings
        """
        self.db_path = db_path
        self.model_name = model_name
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        print(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="legal_chunks",
            metadata={"description": "Legal document chunks with metadata"}
        )
        
        print(f"Vector DB initialized. Collection has {self.collection.count()} documents.")
    
    def add_chunks(self, chunks: List[LegalChunk]) -> None:
        """
        Add legal chunks to the vector database
        """
        if not chunks:
            return
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            # Create unique ID
            chunk_id = f"{chunk.law_type}_{chunk.section_number or 'unknown'}_{i}"
            
            # Prepare metadata (ChromaDB requires string values)
            metadata = {
                "law_type": chunk.law_type,
                "section_number": chunk.section_number or "",
                "turnover_threshold": str(chunk.turnover_threshold) if chunk.turnover_threshold else "",
                "sector_tag": chunk.sector_tag or "",
                "effective_date": chunk.effective_date or "",
                "chunk_type": chunk.chunk_type
            }
            
            documents.append(chunk.text)
            metadatas.append(metadata)
            ids.append(chunk_id)
        
        # Generate embeddings
        print(f"Generating embeddings for {len(documents)} chunks...")
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        
        print(f"Added {len(chunks)} chunks to vector database.")
    
    def semantic_search(self, query: str, n_results: int = 5, 
                       law_type: Optional[str] = None,
                       max_turnover: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search on legal chunks
        
        Args:
            query: Search query
            n_results: Number of results to return
            law_type: Filter by law type (GST, Income Tax, etc.)
            max_turnover: Filter chunks applicable to this turnover
        """
        # Build where clause for filtering
        where_clause = {}
        if law_type:
            where_clause["law_type"] = law_type
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        
        # Process results
        processed_results = []
        for i in range(len(results['documents'][0])):
            metadata = results['metadatas'][0][i]
            
            # Apply turnover filter
            if max_turnover and metadata.get('turnover_threshold'):
                try:
                    threshold = float(metadata['turnover_threshold'])
                    if threshold > max_turnover:
                        continue  # Skip chunks that don't apply
                except ValueError:
                    pass  # Keep chunks without valid threshold
            
            processed_results.append({
                'text': results['documents'][0][i],
                'metadata': metadata,
                'distance': results['distances'][0][i],
                'id': results['ids'][0][i]
            })
        
        return processed_results
    
    def keyword_search(self, section_number: str, law_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for specific section numbers
        """
        where_clause = {"section_number": section_number}
        if law_type:
            where_clause["law_type"] = law_type
        
        results = self.collection.get(
            where=where_clause
        )
        
        processed_results = []
        for i in range(len(results['documents'])):
            processed_results.append({
                'text': results['documents'][i],
                'metadata': results['metadatas'][i],
                'id': results['ids'][i]
            })
        
        return processed_results
    
    def hybrid_search(self, query: str, n_results: int = 5,
                     law_type: Optional[str] = None,
                     max_turnover: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Combine keyword and semantic search
        """
        results = []
        
        # Try keyword search for section numbers
        import re
        section_match = re.search(r'section\s+(\d+[a-z]*)', query, re.IGNORECASE)
        if section_match:
            section_num = section_match.group(1)
            keyword_results = self.keyword_search(section_num, law_type)
            results.extend(keyword_results)
        
        # Semantic search
        semantic_results = self.semantic_search(query, n_results, law_type, max_turnover)
        
        # Combine and deduplicate
        seen_ids = set()
        combined_results = []
        
        for result in results + semantic_results:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                combined_results.append(result)
        
        return combined_results[:n_results]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        total_count = self.collection.count()
        
        # Get law type distribution
        all_metadata = self.collection.get()['metadatas']
        law_types = {}
        for metadata in all_metadata:
            law_type = metadata.get('law_type', 'unknown')
            law_types[law_type] = law_types.get(law_type, 0) + 1
        
        return {
            'total_chunks': total_count,
            'law_type_distribution': law_types,
            'db_path': self.db_path
        }


# Example usage and testing
if __name__ == "__main__":
    from legal_ingestion import LegalDocumentProcessor
    
    # Initialize vector DB
    vector_db = LegalVectorDB()
    
    # Test with sample data
    sample_text = """
Section 16 - Eligibility and conditions for taking input tax credit

(1) Every registered person shall be entitled to take credit of input tax charged on any supply of goods or services or both to him which are used or intended to be used in the course or furtherance of his business.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless the turnover exceeds 5 crore.

Section 17 - Apportionment of credit and blocked credits

(5) Input tax credit shall not be available for motor vehicles for transportation of persons.
    """
    
    # Process and add to vector DB
    processor = LegalDocumentProcessor()
    chunks = processor.splitter.split_legal_text(sample_text, "GST")
    vector_db.add_chunks(chunks)
    
    # Test searches
    print("\n=== Semantic Search Test ===")
    results = vector_db.semantic_search("input tax credit eligibility", n_results=3)
    for result in results:
        print(f"Section: {result['metadata']['section_number']}")
        print(f"Distance: {result['distance']:.3f}")
        print(f"Text: {result['text'][:100]}...")
        print()
    
    print("\n=== Keyword Search Test ===")
    results = vector_db.keyword_search("16")
    for result in results:
        print(f"Section: {result['metadata']['section_number']}")
        print(f"Text: {result['text'][:100]}...")
        print()
    
    print("\n=== Database Stats ===")
    stats = vector_db.get_stats()
    print(json.dumps(stats, indent=2))
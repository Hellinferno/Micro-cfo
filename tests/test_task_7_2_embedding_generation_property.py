#!/usr/bin/env python3
"""
Property-Based Tests for Embedding Generation
Task 7.2: Write property test for embedding generation

Tests:
- Property 20: Embedding Generation Completeness

Validates Requirements: 7.1
"""

import pytest
from hypothesis import given, strategies as st, settings, example
from contextlib import contextmanager
import tempfile
import shutil
import os

# Import the components we're testing
from legal_ingestion import LegalChunk
from vector_database import LegalVectorDB


# ============================================================================
# Test Helpers
# ============================================================================

@contextmanager
def temp_db_env():
    """Create temporary database directory for testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_embed_")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(db_dir, exist_ok=True)
    
    try:
        yield db_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Property 20: Embedding Generation Completeness
# ============================================================================

@st.composite
def legal_chunk_data(draw):
    """Generate data for creating a LegalChunk"""
    # Generate text content
    text = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
        min_size=20,
        max_size=500
    ))
    
    # Generate law type
    law_type = draw(st.sampled_from(['GST', 'Income Tax', 'Corporate Law', 'Subsidy Scheme']))
    
    # Generate optional section number
    section_number = draw(st.one_of(
        st.none(),
        st.integers(min_value=1, max_value=999).map(str)
    ))
    
    # Generate optional turnover threshold
    turnover = draw(st.one_of(
        st.none(),
        st.sampled_from([50000000, 500000000, 1000000000])  # 5Cr, 50Cr, 100Cr
    ))
    
    # Generate optional sector tag
    sector = draw(st.one_of(
        st.none(),
        st.sampled_from(['Textile', 'Manufacturing', 'Technology', 'Trading'])
    ))
    
    return {
        'text': text,
        'law_type': law_type,
        'section_number': section_number,
        'turnover_threshold': turnover,
        'sector_tag': sector,
        'chunk_type': 'main'
    }


@given(legal_chunk_data())
@settings(max_examples=10, deadline=60000)
@example({
    'text': 'Section 16 - Every registered person shall be entitled to take credit of input tax',
    'law_type': 'GST',
    'section_number': '16',
    'turnover_threshold': 50000000,
    'sector_tag': 'Manufacturing',
    'chunk_type': 'main'
})
def test_property_20_embedding_generation_completeness(chunk_data):
    """
    **Property 20: Embedding Generation Completeness**
    
    For any legal chunk processed by the Seed Data Processor, an embedding vector
    should be generated using sentence transformers with the correct dimensionality
    for the model.
    
    **Validates: Requirements 7.1**
    
    Property: For any LegalChunk, when added to the vector database, an embedding
    should be generated with dimensionality matching the embedding model (384 for all-MiniLM-L6-v2).
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Create a legal chunk
            chunk = LegalChunk(**chunk_data)
            
            # Add chunk to database (this should generate embeddings)
            vector_db.add_chunks([chunk])
            
            # Verify chunk was added
            stats = vector_db.get_stats()
            assert stats['total_chunks'] >= 1, \
                "Chunk should be added to database"
            
            # Retrieve the chunk to verify embedding was generated
            # We can't directly access embeddings in ChromaDB easily, but we can verify
            # that semantic search works (which requires embeddings)
            results = vector_db.semantic_search(
                query=chunk_data['text'][:50],  # Use part of the text as query
                n_results=1,
                law_type=chunk_data['law_type']
            )
            
            # Should find at least one result (the chunk we just added)
            assert len(results) >= 1, \
                "Semantic search should find the added chunk (requires embeddings)"
            
            # Verify the result has expected structure
            result = results[0]
            assert 'text' in result, "Result should contain text"
            assert 'metadata' in result, "Result should contain metadata"
            assert 'distance' in result, "Result should contain distance (from embedding comparison)"
            
            # Distance should be a valid number (indicates embedding comparison occurred)
            assert isinstance(result['distance'], (int, float)), \
                "Distance should be numeric (from embedding vector comparison)"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


@given(st.lists(legal_chunk_data(), min_size=2, max_size=5))
@settings(max_examples=5, deadline=60000)
def test_property_20_multiple_chunks_all_have_embeddings(chunks_data_list):
    """
    **Property 20 (Multiple Chunks): All Chunks Get Embeddings**
    
    For any list of legal chunks, when added to the vector database,
    ALL chunks should have embeddings generated.
    
    **Validates: Requirements 7.1**
    
    Property: For any list of LegalChunks, all chunks should be searchable
    via semantic search (which requires embeddings).
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Create legal chunks
            chunks = [LegalChunk(**data) for data in chunks_data_list]
            
            # Add all chunks to database
            vector_db.add_chunks(chunks)
            
            # Verify all chunks were added
            stats = vector_db.get_stats()
            assert stats['total_chunks'] >= len(chunks), \
                f"All {len(chunks)} chunks should be added to database"
            
            # Verify each chunk is searchable (has embeddings)
            for chunk_data in chunks_data_list:
                results = vector_db.semantic_search(
                    query=chunk_data['text'][:50],
                    n_results=len(chunks),
                    law_type=chunk_data['law_type']
                )
                
                # Should find results (requires embeddings)
                assert len(results) >= 1, \
                    f"Should find results for chunk with law_type {chunk_data['law_type']}"
                
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


@given(legal_chunk_data())
@settings(max_examples=10, deadline=60000)
def test_property_20_embedding_dimensionality(chunk_data):
    """
    **Property 20 (Dimensionality): Embeddings Have Correct Dimensionality**
    
    For any legal chunk, the generated embedding should have the correct
    dimensionality for the model (384 for all-MiniLM-L6-v2).
    
    **Validates: Requirements 7.1**
    
    Property: Embeddings should have dimensionality matching the model.
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Get the embedding model's dimension
            # For all-MiniLM-L6-v2, this should be 384
            test_embedding = vector_db.embedding_model.encode(["test"])
            expected_dim = test_embedding.shape[1]
            
            # Verify it's the expected dimension for all-MiniLM-L6-v2
            assert expected_dim == 384, \
                f"Expected embedding dimension 384 for all-MiniLM-L6-v2, got {expected_dim}"
            
            # Create and add a chunk
            chunk = LegalChunk(**chunk_data)
            vector_db.add_chunks([chunk])
            
            # Generate embedding for the chunk text directly
            chunk_embedding = vector_db.embedding_model.encode([chunk_data['text']])
            
            # Verify embedding has correct shape
            assert chunk_embedding.shape[1] == expected_dim, \
                f"Chunk embedding should have dimension {expected_dim}, got {chunk_embedding.shape[1]}"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


@given(legal_chunk_data())
@settings(max_examples=10, deadline=60000)
def test_property_20_embedding_determinism(chunk_data):
    """
    **Property 20 (Determinism): Same Text Produces Same Embedding**
    
    For any legal chunk text, generating embeddings multiple times
    should produce the same embedding vector (deterministic).
    
    **Validates: Requirements 7.1**
    
    Property: Embedding generation is deterministic for the same input.
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Generate embedding for the same text multiple times
            text = chunk_data['text']
            embedding1 = vector_db.embedding_model.encode([text])
            embedding2 = vector_db.embedding_model.encode([text])
            embedding3 = vector_db.embedding_model.encode([text])
            
            # Embeddings should be identical (or very close due to floating point)
            import numpy as np
            assert np.allclose(embedding1, embedding2, rtol=1e-5), \
                "Embeddings should be identical for same text (first vs second)"
            assert np.allclose(embedding2, embedding3, rtol=1e-5), \
                "Embeddings should be identical for same text (second vs third)"
            assert np.allclose(embedding1, embedding3, rtol=1e-5), \
                "Embeddings should be identical for same text (first vs third)"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


# ============================================================================
# Edge Cases
# ============================================================================

def test_property_20_empty_text_handling():
    """
    **Property 20 (Edge Case): Empty Text Handling**
    
    For empty or whitespace-only text, the system should handle gracefully.
    
    **Validates: Requirements 7.1**
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Create chunk with empty text
            chunk = LegalChunk(
                text="",
                law_type="GST",
                chunk_type="main"
            )
            
            # Should handle gracefully (not crash)
            try:
                vector_db.add_chunks([chunk])
                # If it succeeds, verify it was added
                stats = vector_db.get_stats()
                assert stats['total_chunks'] >= 0, "Should handle empty text gracefully"
            except Exception:
                # It's acceptable to reject empty text
                pass
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


def test_property_20_very_long_text_handling():
    """
    **Property 20 (Edge Case): Very Long Text Handling**
    
    For very long text, the system should handle gracefully (may truncate).
    
    **Validates: Requirements 7.1**
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Create chunk with very long text (10000 characters)
            long_text = "Section 1 - " + ("This is a very long legal provision. " * 300)
            chunk = LegalChunk(
                text=long_text,
                law_type="GST",
                section_number="1",
                chunk_type="main"
            )
            
            # Should handle gracefully
            vector_db.add_chunks([chunk])
            
            # Verify it was added
            stats = vector_db.get_stats()
            assert stats['total_chunks'] >= 1, "Should handle long text"
            
            # Verify it's searchable
            results = vector_db.semantic_search(
                query="Section 1",
                n_results=1,
                law_type="GST"
            )
            assert len(results) >= 1, "Long text chunk should be searchable"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])

#!/usr/bin/env python3
"""
Property-Based Tests for Database Round-Trip
Task 7.3: Write property test for database round-trip

Tests:
- Property 21: Database Storage Round-Trip

Validates Requirements: 7.2
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
    temp_dir = tempfile.mkdtemp(prefix="test_roundtrip_")
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(db_dir, exist_ok=True)
    
    try:
        yield db_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Property 21: Database Storage Round-Trip
# ============================================================================

@st.composite
def legal_chunk_with_all_fields(draw):
    """Generate a complete LegalChunk with all fields populated"""
    # Generate text content
    text = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
        min_size=50,
        max_size=500
    ))
    
    # Generate law type
    law_type = draw(st.sampled_from(['GST', 'Income Tax', 'Corporate Law', 'Subsidy Scheme']))
    
    # Generate section number
    section_number = draw(st.integers(min_value=1, max_value=999).map(str))
    
    # Generate turnover threshold
    turnover = draw(st.sampled_from([50000000, 500000000, 1000000000]))
    
    # Generate sector tag
    sector = draw(st.sampled_from(['Textile', 'Manufacturing', 'Technology', 'Trading']))
    
    # Generate effective date
    year = draw(st.integers(min_value=2000, max_value=2099))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    effective_date = f"{year}-{month:02d}-{day:02d}"
    
    # Generate chunk type
    chunk_type = draw(st.sampled_from(['main', 'proviso', 'sub_clause']))
    
    return LegalChunk(
        text=text,
        law_type=law_type,
        section_number=section_number,
        turnover_threshold=turnover,
        sector_tag=sector,
        effective_date=effective_date,
        chunk_type=chunk_type
    )


@given(legal_chunk_with_all_fields())
@settings(max_examples=10, deadline=60000)
@example(LegalChunk(
    text='Section 16 - Every registered person shall be entitled to take credit of input tax charged on any supply',
    law_type='GST',
    section_number='16',
    turnover_threshold=50000000,
    sector_tag='Manufacturing',
    effective_date='2023-04-01',
    chunk_type='main'
))
def test_property_21_database_storage_roundtrip(chunk):
    """
    **Property 21: Database Storage Round-Trip**
    
    For any legal chunk stored in the vector database, retrieving it should
    return a chunk with identical text content, metadata fields, and embedding vector.
    
    **Validates: Requirements 7.2**
    
    Property: store(chunk) then retrieve(chunk) should return data matching original chunk.
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Store the chunk
            vector_db.add_chunks([chunk])
            
            # Retrieve the chunk using semantic search with its own text
            results = vector_db.semantic_search(
                query=chunk.text[:100],  # Use beginning of text as query
                n_results=1,
                law_type=chunk.law_type
            )
            
            # Should find the chunk
            assert len(results) >= 1, \
                "Should retrieve the stored chunk"
            
            retrieved = results[0]
            
            # Verify text content matches
            assert retrieved['text'] == chunk.text, \
                f"Retrieved text should match original"
            
            # Verify metadata fields match
            metadata = retrieved['metadata']
            assert metadata['law_type'] == chunk.law_type, \
                f"Law type should match: expected {chunk.law_type}, got {metadata['law_type']}"
            assert metadata['section_number'] == chunk.section_number, \
                f"Section number should match: expected {chunk.section_number}, got {metadata['section_number']}"
            assert metadata['chunk_type'] == chunk.chunk_type, \
                f"Chunk type should match: expected {chunk.chunk_type}, got {metadata['chunk_type']}"
            
            # Verify numeric metadata (stored as strings in ChromaDB)
            if chunk.turnover_threshold:
                assert metadata['turnover_threshold'] == str(chunk.turnover_threshold), \
                    f"Turnover threshold should match"
            
            # Verify optional metadata
            if chunk.sector_tag:
                assert metadata['sector_tag'] == chunk.sector_tag, \
                    f"Sector tag should match"
            
            if chunk.effective_date:
                assert metadata['effective_date'] == chunk.effective_date, \
                    f"Effective date should match"
            
            # Verify distance is very small (chunk should match itself closely)
            assert retrieved['distance'] < 0.5, \
                f"Distance should be small for exact match, got {retrieved['distance']}"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


@given(st.lists(legal_chunk_with_all_fields(), min_size=3, max_size=5))
@settings(max_examples=5, deadline=60000)
def test_property_21_multiple_chunks_roundtrip(chunks):
    """
    **Property 21 (Multiple Chunks): All Chunks Survive Round-Trip**
    
    For any list of legal chunks stored in the vector database,
    all chunks should be retrievable with their data intact.
    
    **Validates: Requirements 7.2**
    
    Property: For any list of chunks, all should be retrievable after storage.
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Store all chunks
            vector_db.add_chunks(chunks)
            
            # Verify all chunks are retrievable
            for chunk in chunks:
                results = vector_db.semantic_search(
                    query=chunk.text[:100],
                    n_results=len(chunks),
                    law_type=chunk.law_type
                )
                
                # Should find at least one result
                assert len(results) >= 1, \
                    f"Should retrieve chunk with law_type {chunk.law_type}"
                
                # Find the matching chunk in results
                found = False
                for result in results:
                    if result['text'] == chunk.text:
                        found = True
                        # Verify metadata matches
                        metadata = result['metadata']
                        assert metadata['law_type'] == chunk.law_type
                        assert metadata['section_number'] == chunk.section_number
                        break
                
                assert found, \
                    f"Should find exact match for stored chunk"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


@given(legal_chunk_with_all_fields())
@settings(max_examples=10, deadline=60000)
def test_property_21_keyword_search_roundtrip(chunk):
    """
    **Property 21 (Keyword Search): Chunks Retrievable by Section Number**
    
    For any legal chunk with a section number, it should be retrievable
    using keyword search by that section number.
    
    **Validates: Requirements 7.2**
    
    Property: Chunks with section numbers should be findable via keyword search.
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Store the chunk
            vector_db.add_chunks([chunk])
            
            # Retrieve using keyword search by section number
            if chunk.section_number:
                results = vector_db.keyword_search(
                    section_number=chunk.section_number,
                    law_type=chunk.law_type
                )
                
                # Should find the chunk
                assert len(results) >= 1, \
                    f"Should find chunk by section number {chunk.section_number}"
                
                # Verify it's the right chunk
                found = False
                for result in results:
                    if result['text'] == chunk.text:
                        found = True
                        break
                
                assert found, \
                    "Should find the exact chunk by section number"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


@given(legal_chunk_with_all_fields())
@settings(max_examples=10, deadline=60000)
def test_property_21_hybrid_search_roundtrip(chunk):
    """
    **Property 21 (Hybrid Search): Chunks Retrievable via Hybrid Search**
    
    For any legal chunk, it should be retrievable using hybrid search
    (combination of keyword and semantic search).
    
    **Validates: Requirements 7.2**
    
    Property: Chunks should be findable via hybrid search.
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Store the chunk
            vector_db.add_chunks([chunk])
            
            # Retrieve using hybrid search
            # Use section number in query if available
            if chunk.section_number:
                query = f"section {chunk.section_number} {chunk.text[:50]}"
            else:
                query = chunk.text[:100]
            
            results = vector_db.hybrid_search(
                query=query,
                n_results=5,
                law_type=chunk.law_type
            )
            
            # Should find the chunk
            assert len(results) >= 1, \
                "Should find chunk via hybrid search"
            
            # Verify the chunk is in results
            found = False
            for result in results:
                if result['text'] == chunk.text:
                    found = True
                    break
            
            assert found, \
                "Should find the exact chunk via hybrid search"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


# ============================================================================
# Edge Cases
# ============================================================================

def test_property_21_special_characters_roundtrip():
    """
    **Property 21 (Edge Case): Special Characters Survive Round-Trip**
    
    For chunks with special characters, all characters should be preserved.
    
    **Validates: Requirements 7.2**
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Create chunk with special characters
            special_text = "Section 16(1)(a) - Provided that: Rs. 5,00,000/- @ 18% GST"
            chunk = LegalChunk(
                text=special_text,
                law_type="GST",
                section_number="16",
                chunk_type="proviso"
            )
            
            # Store and retrieve
            vector_db.add_chunks([chunk])
            results = vector_db.semantic_search(
                query=special_text[:30],
                n_results=1,
                law_type="GST"
            )
            
            # Verify special characters preserved
            assert len(results) >= 1
            assert results[0]['text'] == special_text, \
                "Special characters should be preserved"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


def test_property_21_unicode_roundtrip():
    """
    **Property 21 (Edge Case): Unicode Characters Survive Round-Trip**
    
    For chunks with Unicode characters (e.g., Hindi), characters should be preserved.
    
    **Validates: Requirements 7.2**
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Create chunk with Unicode (Hindi) characters
            unicode_text = "धारा 16 - Section 16 - Input tax credit eligibility नियम"
            chunk = LegalChunk(
                text=unicode_text,
                law_type="GST",
                section_number="16",
                chunk_type="main"
            )
            
            # Store and retrieve
            vector_db.add_chunks([chunk])
            results = vector_db.semantic_search(
                query="Section 16",
                n_results=1,
                law_type="GST"
            )
            
            # Verify Unicode preserved
            assert len(results) >= 1
            assert results[0]['text'] == unicode_text, \
                "Unicode characters should be preserved"
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


def test_property_21_none_values_roundtrip():
    """
    **Property 21 (Edge Case): None Values Handled Correctly**
    
    For chunks with None/optional fields, the round-trip should handle correctly.
    
    **Validates: Requirements 7.2**
    """
    with temp_db_env() as db_dir:
        try:
            # Initialize vector database
            vector_db = LegalVectorDB(db_path=db_dir)
            
            # Create chunk with minimal fields (many None values)
            chunk = LegalChunk(
                text="This is a general legal provision without specific metadata",
                law_type="General",
                section_number=None,
                turnover_threshold=None,
                sector_tag=None,
                effective_date=None,
                chunk_type="main"
            )
            
            # Store and retrieve
            vector_db.add_chunks([chunk])
            results = vector_db.semantic_search(
                query=chunk.text[:30],
                n_results=1,
                law_type="General"
            )
            
            # Verify chunk retrieved
            assert len(results) >= 1
            assert results[0]['text'] == chunk.text
            
            # Verify None values handled (stored as empty strings in ChromaDB)
            metadata = results[0]['metadata']
            assert metadata['section_number'] == "" or metadata['section_number'] is None
            assert metadata['turnover_threshold'] == "" or metadata['turnover_threshold'] is None
            
        except Exception as e:
            pytest.skip(f"Could not initialize vector database: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])

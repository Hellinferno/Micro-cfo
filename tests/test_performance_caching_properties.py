#!/usr/bin/env python3
"""
Property-Based Tests for Performance and Caching
Feature: frontend-backend-integration

Tests Property 6: Performance and Caching
Validates: Requirements 6.1, 6.2, 6.3
"""

import pytest
import asyncio
import time
from hypothesis import given, strategies as st, settings, HealthCheck
from cache_manager import CacheManager
from connection_pool import ConnectionPool, ResourceQueue


class TestPerformanceAndCaching:
    """
    Property-based tests for performance optimization features
    
    Feature: frontend-backend-integration, Property 6: Performance and Caching
    
    Tests that:
    - Cached queries return results faster than uncached queries
    - Identical queries within cache window return cached results
    - Concurrent requests are handled without blocking
    """
    
    @given(
        query=st.text(min_size=1, max_size=100),
        user_context=st.text(max_size=50)
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cache_hit_returns_cached_result(self, query: str, user_context: str):
        """
        Property: For any legal query that has been cached, subsequent identical 
        queries should return the cached result.
        
        Feature: frontend-backend-integration, Property 6: Performance and Caching
        Validates: Requirements 6.1, 6.2
        """
        # Create a fresh cache manager for this test
        cache = CacheManager(default_ttl=60)
        
        # Generate cache key
        cache_key = cache.generate_key("legal_query", query=query, user_context=user_context)
        
        # First access should be a miss
        result1 = cache.get(cache_key)
        assert result1 is None, "First access should be a cache miss"
        
        # Set a value in cache
        test_value = {
            "risk_level": "Low",
            "relevant_section": "Section 16",
            "compliant_action": "Test action"
        }
        cache.set(cache_key, test_value, ttl=60)
        
        # Second access should be a hit
        result2 = cache.get(cache_key)
        assert result2 is not None, "Second access should be a cache hit"
        assert result2 == test_value, "Cached value should match original value"
        
        # Verify cache statistics
        stats = cache.get_stats()
        assert stats["hits"] >= 1, "Should have at least one cache hit"
        assert stats["misses"] >= 1, "Should have at least one cache miss"
    
    @given(
        query=st.text(min_size=1, max_size=100),
        ttl=st.integers(min_value=1, max_value=5)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cache_expiration_after_ttl(self, query: str, ttl: int):
        """
        Property: For any cached query, the cache entry should expire after 
        the TTL period and subsequent queries should miss the cache.
        
        Feature: frontend-backend-integration, Property 6: Performance and Caching
        Validates: Requirements 6.1, 6.2
        """
        # Create a fresh cache manager
        cache = CacheManager(default_ttl=ttl)
        
        # Generate cache key
        cache_key = cache.generate_key("legal_query", query=query)
        
        # Set a value with short TTL
        test_value = {"data": "test"}
        cache.set(cache_key, test_value, ttl=ttl)
        
        # Immediate access should hit
        result1 = cache.get(cache_key)
        assert result1 == test_value, "Immediate access should return cached value"
        
        # Wait for TTL to expire
        time.sleep(ttl + 0.5)
        
        # Access after expiration should miss
        result2 = cache.get(cache_key)
        assert result2 is None, "Access after TTL should be a cache miss"
    
    @given(
        prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        num_entries=st.integers(min_value=1, max_value=10)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cache_invalidation_by_prefix(self, prefix: str, num_entries: int):
        """
        Property: For any cache prefix, invalidating that prefix should remove 
        all entries with that prefix.
        
        Feature: frontend-backend-integration, Property 6: Performance and Caching
        Validates: Requirements 6.2
        """
        # Create a fresh cache manager
        cache = CacheManager(default_ttl=60)
        
        # Add multiple entries with the same prefix
        for i in range(num_entries):
            cache_key = f"{prefix}:{i}"
            cache.set(cache_key, {"value": i}, ttl=60)
        
        # Verify all entries exist
        for i in range(num_entries):
            cache_key = f"{prefix}:{i}"
            result = cache.get(cache_key)
            assert result is not None, f"Entry {i} should exist before invalidation"
        
        # Invalidate by prefix
        invalidated_count = cache.invalidate_prefix(prefix)
        assert invalidated_count == num_entries, f"Should invalidate {num_entries} entries"
        
        # Verify all entries are gone
        for i in range(num_entries):
            cache_key = f"{prefix}:{i}"
            result = cache.get(cache_key)
            assert result is None, f"Entry {i} should not exist after invalidation"
    
    @pytest.mark.asyncio
    @given(
        num_concurrent=st.integers(min_value=2, max_value=10)
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_concurrent_request_handling(self, num_concurrent: int):
        """
        Property: For any number of concurrent requests, the system should handle 
        them without blocking and all requests should complete successfully.
        
        Feature: frontend-backend-integration, Property 6: Performance and Caching
        Validates: Requirements 6.3
        """
        # Create a fresh connection pool
        pool = ConnectionPool(max_connections=num_concurrent)
        
        # Define a mock async operation
        async def mock_operation(operation_id: int):
            await asyncio.sleep(0.1)  # Simulate work
            return {"id": operation_id, "result": "success"}
        
        # Execute concurrent operations
        start_time = time.time()
        tasks = [
            pool.execute(mock_operation, i)
            for i in range(num_concurrent)
        ]
        results = await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time
        
        # Verify all operations completed
        assert len(results) == num_concurrent, "All operations should complete"
        
        # Verify results are correct
        for i, result in enumerate(results):
            assert result["id"] == i, f"Operation {i} should return correct ID"
            assert result["result"] == "success", f"Operation {i} should succeed"
        
        # Verify concurrent execution (should not take num_concurrent * 0.1 seconds)
        # Allow some overhead, but should be much faster than sequential
        max_expected_time = 0.1 * 3  # Allow 3x overhead for async scheduling
        assert elapsed_time < max_expected_time, \
            f"Concurrent execution should be fast (took {elapsed_time:.2f}s)"
        
        # Verify pool statistics
        stats = pool.get_stats()
        assert stats["total_requests"] == num_concurrent, \
            "Pool should track all requests"
    
    @pytest.mark.asyncio
    @given(
        num_operations=st.integers(min_value=1, max_value=5),
        max_concurrent=st.integers(min_value=1, max_value=3)
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_resource_queue_limits_concurrency(self, num_operations: int, max_concurrent: int):
        """
        Property: For any resource-intensive operations, the resource queue should 
        limit concurrent execution to the configured maximum.
        
        Feature: frontend-backend-integration, Property 6: Performance and Caching
        Validates: Requirements 6.3
        """
        # Create a fresh resource queue
        queue = ResourceQueue(max_concurrent=max_concurrent)
        
        # Track concurrent operations
        concurrent_count = 0
        max_observed_concurrent = 0
        lock = asyncio.Lock()
        
        async def tracked_operation(operation_id: int):
            nonlocal concurrent_count, max_observed_concurrent
            
            async with lock:
                concurrent_count += 1
                max_observed_concurrent = max(max_observed_concurrent, concurrent_count)
            
            await asyncio.sleep(0.1)  # Simulate work
            
            async with lock:
                concurrent_count -= 1
            
            return {"id": operation_id}
        
        # Execute operations through resource queue
        tasks = [
            queue.execute_resource_intensive(tracked_operation, i)
            for i in range(num_operations)
        ]
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed
        assert len(results) == num_operations, "All operations should complete"
        
        # Verify concurrency was limited
        assert max_observed_concurrent <= max_concurrent, \
            f"Concurrent operations ({max_observed_concurrent}) should not exceed limit ({max_concurrent})"
        
        # Verify queue statistics
        stats = queue.get_stats()
        assert stats["total_operations"] == num_operations, \
            "Queue should track all operations"
    
    @given(
        queries=st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=10)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cache_key_generation_consistency(self, queries: list):
        """
        Property: For any set of query parameters, generating the cache key 
        multiple times should produce the same key.
        
        Feature: frontend-backend-integration, Property 6: Performance and Caching
        Validates: Requirements 6.1
        """
        cache = CacheManager()
        
        for query in queries:
            # Generate key multiple times
            key1 = cache.generate_key("legal_query", query=query, context="test")
            key2 = cache.generate_key("legal_query", query=query, context="test")
            key3 = cache.generate_key("legal_query", query=query, context="test")
            
            # All keys should be identical
            assert key1 == key2 == key3, \
                "Cache key generation should be consistent"
            
            # Different parameters should produce different keys
            key_different = cache.generate_key("legal_query", query=query, context="different")
            assert key1 != key_different, \
                "Different parameters should produce different keys"
    
    @given(
        num_entries=st.integers(min_value=10, max_value=50)
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cache_statistics_accuracy(self, num_entries: int):
        """
        Property: For any cache operations, the statistics should accurately 
        reflect hits, misses, and cache size.
        
        Feature: frontend-backend-integration, Property 6: Performance and Caching
        Validates: Requirements 6.1, 6.2
        """
        cache = CacheManager(default_ttl=60)
        
        # Add entries
        for i in range(num_entries):
            cache.set(f"key_{i}", {"value": i}, ttl=60)
        
        # Perform some hits
        hits_expected = 0
        for i in range(0, num_entries, 2):  # Access every other entry
            result = cache.get(f"key_{i}")
            if result is not None:
                hits_expected += 1
        
        # Perform some misses
        misses_expected = 0
        for i in range(num_entries, num_entries + 5):  # Access non-existent entries
            result = cache.get(f"key_{i}")
            if result is None:
                misses_expected += 1
        
        # Verify statistics
        stats = cache.get_stats()
        assert stats["size"] == num_entries, \
            f"Cache size should be {num_entries}"
        assert stats["hits"] == hits_expected, \
            f"Hits should be {hits_expected}"
        assert stats["misses"] >= misses_expected, \
            f"Misses should be at least {misses_expected}"
        assert stats["total_requests"] == stats["hits"] + stats["misses"], \
            "Total requests should equal hits + misses"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

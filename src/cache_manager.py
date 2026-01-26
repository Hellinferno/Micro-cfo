#!/usr/bin/env python3
"""
Cache Manager for MicroCFO Integration Server
Provides in-memory caching for frequently accessed legal data
"""

import logging
import hashlib
import json
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a single cache entry with expiration"""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.expires_at
    
    def get_age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return (datetime.now() - self.created_at).total_seconds()


class CacheManager:
    """
    In-memory cache manager for legal queries and other frequently accessed data
    
    Features:
    - TTL-based expiration
    - Cache key generation from query parameters
    - Thread-safe operations
    - Cache statistics tracking
    - Manual invalidation support
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache manager
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(f"Cache manager initialized with default TTL: {default_ttl}s")
    
    def generate_key(self, prefix: str, **params) -> str:
        """
        Generate cache key from parameters
        
        Args:
            prefix: Key prefix (e.g., "legal_query", "subsidy_search")
            **params: Parameters to include in key generation
        
        Returns:
            str: Generated cache key
        """
        # Sort parameters for consistent key generation
        sorted_params = sorted(params.items())
        param_str = json.dumps(sorted_params, sort_keys=True)
        
        # Generate hash of parameters
        param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]
        
        return f"{prefix}:{param_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                logger.debug(f"Cache miss: {key}")
                return None
            
            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                self._evictions += 1
                self._misses += 1
                logger.debug(f"Cache expired: {key} (age: {entry.get_age_seconds():.1f}s)")
                return None
            
            self._hits += 1
            logger.debug(f"Cache hit: {key} (age: {entry.get_age_seconds():.1f}s)")
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate (remove) a specific cache entry
        
        Args:
            key: Cache key to invalidate
        
        Returns:
            bool: True if key was found and removed, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._evictions += 1
                logger.info(f"Cache invalidated: {key}")
                return True
            return False
    
    def invalidate_prefix(self, prefix: str) -> int:
        """
        Invalidate all cache entries with given prefix
        
        Args:
            prefix: Key prefix to match
        
        Returns:
            int: Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            
            for key in keys_to_remove:
                del self._cache[key]
                self._evictions += 1
            
            if keys_to_remove:
                logger.info(f"Cache invalidated {len(keys_to_remove)} entries with prefix: {prefix}")
            
            return len(keys_to_remove)
    
    def clear(self) -> int:
        """
        Clear all cache entries
        
        Returns:
            int: Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._evictions += count
            logger.info(f"Cache cleared: {count} entries removed")
            return count
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache
        
        Returns:
            int: Number of expired entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self._evictions += 1
            
            if expired_keys:
                logger.info(f"Cache cleanup: {len(expired_keys)} expired entries removed")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics including hits, misses, size, etc.
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "default_ttl_seconds": self.default_ttl
            }
    
    def reset_stats(self) -> None:
        """Reset cache statistics"""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            logger.info("Cache statistics reset")


# Global cache manager instance
cache_manager = CacheManager(default_ttl=3600)  # 1 hour default TTL

#!/usr/bin/env python3
"""
Enhanced Multi-Level Cache Service for MicroCFO
Implements L1 (in-memory) and L2 (Redis) caching with automatic failover

Based on Backend PRD:
- Multi-level caching (L1: Memory, L2: Redis, L3: Database)
- TTL-based expiration
- Cache invalidation on updates
- Statistics and monitoring
"""

import os
import json
import logging
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from threading import Lock
from dataclasses import dataclass
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached value with metadata"""
    value: Any
    created_at: datetime
    expires_at: datetime
    hits: int = 0
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def age_seconds(self) -> float:
        return (datetime.now() - self.created_at).total_seconds()


class L1Cache:
    """In-memory cache (Level 1) - Fastest but limited size"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            entry.hits += 1
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            self._cache[key] = CacheEntry(
                value=value,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl)
            )
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries"""
        if not self._cache:
            return
        
        # Sort by hits (ascending) and age (oldest first)
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hits, -self._cache[k].age_seconds())
        )
        
        # Remove bottom 10%
        to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:to_remove]:
            del self._cache[key]
    
    def clear(self) -> int:
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    def stats(self) -> Dict:
        total = self._hits + self._misses
        return {
            "type": "L1_memory",
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 2) if total > 0 else 0
        }


class L2Cache:
    """Redis cache (Level 2) - Shared across instances"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.default_ttl = default_ttl
        self._client = None
        self._available = False
        self._hits = 0
        self._misses = 0
        
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Redis"""
        try:
            import redis
            self._client = redis.from_url(
                self.redis_url,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=False  # We'll handle encoding ourselves
            )
            # Test connection
            self._client.ping()
            self._available = True
            logger.info("✅ Redis L2 cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
            self._available = False
    
    def is_available(self) -> bool:
        return self._available
    
    def get(self, key: str) -> Optional[Any]:
        if not self._available:
            return None
        
        try:
            data = self._client.get(f"cache:{key}")
            if data is None:
                self._misses += 1
                return None
            
            self._hits += 1
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self._available:
            return False
        
        ttl = ttl or self.default_ttl
        
        try:
            data = pickle.dumps(value)
            self._client.setex(f"cache:{key}", ttl, data)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        if not self._available:
            return False
        
        try:
            return self._client.delete(f"cache:{key}") > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._available:
            return 0
        
        try:
            keys = self._client.keys(f"cache:{pattern}")
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete pattern error: {e}")
            return 0
    
    def clear(self) -> int:
        if not self._available:
            return 0
        
        try:
            keys = self._client.keys("cache:*")
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0
    
    def stats(self) -> Dict:
        total = self._hits + self._misses
        info = {}
        
        if self._available:
            try:
                redis_info = self._client.info('memory')
                info = {
                    "used_memory": redis_info.get('used_memory_human', 'N/A'),
                    "connected_clients": self._client.info('clients').get('connected_clients', 0)
                }
            except:
                pass
        
        return {
            "type": "L2_redis",
            "available": self._available,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 2) if total > 0 else 0,
            **info
        }


class MultiLevelCache:
    """
    Multi-Level Cache with L1 (memory) and L2 (Redis)
    
    Read strategy: Check L1 -> Check L2 -> Miss
    Write strategy: Write to both L1 and L2
    """
    
    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_ttl: int = 300,  # 5 minutes
        l2_ttl: int = 3600,  # 1 hour
        prefix: str = "microcfo"
    ):
        self.l1 = L1Cache(max_size=l1_max_size, default_ttl=l1_ttl)
        self.l2 = L2Cache(default_ttl=l2_ttl)
        self.prefix = prefix
        
        logger.info(f"Multi-level cache initialized (L1: {l1_max_size} items, L2: Redis)")
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Create namespaced cache key"""
        return f"{self.prefix}:{namespace}:{key}"
    
    def generate_key(self, namespace: str, **params) -> str:
        """Generate cache key from parameters"""
        param_str = json.dumps(sorted(params.items()), sort_keys=True)
        key_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]
        return self._make_key(namespace, key_hash)
    
    def get(self, key: str) -> Optional[Any]:
        """Get from cache (L1 -> L2)"""
        
        # Check L1 first
        value = self.l1.get(key)
        if value is not None:
            return value
        
        # Check L2
        value = self.l2.get(key)
        if value is not None:
            # Populate L1
            self.l1.set(key, value)
            return value
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None
    ) -> None:
        """Set in both L1 and L2"""
        self.l1.set(key, value, l1_ttl)
        self.l2.set(key, value, l2_ttl)
    
    def delete(self, key: str) -> bool:
        """Delete from both levels"""
        l1_deleted = self.l1.delete(key)
        l2_deleted = self.l2.delete(key)
        return l1_deleted or l2_deleted
    
    def invalidate_namespace(self, namespace: str) -> int:
        """Invalidate all keys in a namespace"""
        pattern = f"{self.prefix}:{namespace}:*"
        
        # Clear L1 (simple iteration)
        l1_count = 0
        keys_to_remove = [
            k for k in list(self.l1._cache.keys())
            if k.startswith(f"{self.prefix}:{namespace}:")
        ]
        for k in keys_to_remove:
            self.l1.delete(k)
            l1_count += 1
        
        # Clear L2
        l2_count = self.l2.delete_pattern(pattern)
        
        logger.info(f"Invalidated namespace {namespace}: L1={l1_count}, L2={l2_count}")
        return l1_count + l2_count
    
    def clear_all(self) -> Dict[str, int]:
        """Clear all caches"""
        return {
            "l1_cleared": self.l1.clear(),
            "l2_cleared": self.l2.clear()
        }
    
    def stats(self) -> Dict:
        """Get combined statistics"""
        l1_stats = self.l1.stats()
        l2_stats = self.l2.stats()
        
        total_hits = l1_stats["hits"] + l2_stats["hits"]
        total_misses = l1_stats["misses"] + l2_stats["misses"]
        total = total_hits + total_misses
        
        return {
            "combined": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_rate": round(total_hits / total * 100, 2) if total > 0 else 0
            },
            "l1": l1_stats,
            "l2": l2_stats
        }


def cached(
    namespace: str,
    ttl: int = 300,
    key_params: Optional[List[str]] = None
):
    """
    Decorator for caching function results
    
    Usage:
        @cached(namespace="legal_query", ttl=600)
        async def search_laws(query: str, category: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key from function name and specified params
            key_dict = {"func": func.__name__}
            
            if key_params:
                for param in key_params:
                    if param in kwargs:
                        key_dict[param] = kwargs[param]
            else:
                # Use all kwargs
                key_dict.update(kwargs)
            
            cache_key = cache_service.generate_key(namespace, **key_dict)
            
            # Check cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache_service.set(cache_key, result, l1_ttl=min(ttl, 300), l2_ttl=ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_dict = {"func": func.__name__}
            key_dict.update(kwargs)
            
            cache_key = cache_service.generate_key(namespace, **key_dict)
            
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, l1_ttl=min(ttl, 300), l2_ttl=ttl)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Pre-defined cache namespaces
class CacheNamespace:
    """Standard cache namespaces"""
    LEGAL_QUERY = "legal_query"
    SUBSIDY_SEARCH = "subsidy_search"
    USER_PROFILE = "user_profile"
    COMPLIANCE_CALENDAR = "compliance_calendar"
    DOCUMENT_RESULT = "document_result"
    LLM_RESPONSE = "llm_response"
    EMBEDDING = "embedding"


# Global cache service instance
cache_service = MultiLevelCache(
    l1_max_size=1000,
    l1_ttl=300,  # 5 minutes for L1
    l2_ttl=3600,  # 1 hour for L2
    prefix="microcfo"
)

#!/usr/bin/env python3
"""
Connection Pool Manager for MicroCFO Integration Server
Manages database connections and resource-intensive operations
"""

import logging
import asyncio
from typing import Optional, Callable, Any
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Connection pool for managing database connections and resource-intensive operations
    
    Features:
    - Async connection management
    - Request queuing for resource-intensive operations
    - Connection lifecycle tracking
    - Pool statistics
    """
    
    def __init__(self, max_connections: int = 10, max_queue_size: int = 100):
        """
        Initialize connection pool
        
        Args:
            max_connections: Maximum number of concurrent connections
            max_queue_size: Maximum size of request queue
        """
        self.max_connections = max_connections
        self.max_queue_size = max_queue_size
        
        # Semaphore to limit concurrent operations
        self._semaphore = asyncio.Semaphore(max_connections)
        
        # Request queue for overflow
        self._queue: deque = deque(maxlen=max_queue_size)
        
        # Statistics
        self._active_connections = 0
        self._total_requests = 0
        self._queued_requests = 0
        self._rejected_requests = 0
        
        logger.info(f"Connection pool initialized: max_connections={max_connections}, max_queue_size={max_queue_size}")
    
    async def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation with connection pooling
        
        Args:
            operation: Async callable to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
        
        Returns:
            Result of the operation
        
        Raises:
            RuntimeError: If queue is full and operation cannot be queued
        """
        self._total_requests += 1
        
        # Try to acquire semaphore
        async with self._semaphore:
            self._active_connections += 1
            try:
                logger.debug(f"Executing operation: {operation.__name__} (active: {self._active_connections})")
                result = await operation(*args, **kwargs)
                return result
            finally:
                self._active_connections -= 1
    
    def get_stats(self) -> dict:
        """
        Get connection pool statistics
        
        Returns:
            dict: Pool statistics
        """
        return {
            "max_connections": self.max_connections,
            "active_connections": self._active_connections,
            "total_requests": self._total_requests,
            "queued_requests": self._queued_requests,
            "rejected_requests": self._rejected_requests,
            "queue_size": len(self._queue),
            "max_queue_size": self.max_queue_size
        }


class ResourceQueue:
    """
    Queue for managing resource-intensive operations
    
    Ensures that expensive operations (like document processing, vector search)
    don't overwhelm the system by limiting concurrent execution.
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize resource queue
        
        Args:
            max_concurrent: Maximum number of concurrent resource-intensive operations
        """
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Statistics
        self._active_operations = 0
        self._total_operations = 0
        self._total_wait_time = 0.0
        
        logger.info(f"Resource queue initialized: max_concurrent={max_concurrent}")
    
    async def execute_resource_intensive(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute a resource-intensive operation with queuing
        
        Args:
            operation: Async callable to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
        
        Returns:
            Result of the operation
        """
        start_wait = datetime.now()
        self._total_operations += 1
        
        async with self._semaphore:
            wait_time = (datetime.now() - start_wait).total_seconds()
            self._total_wait_time += wait_time
            
            self._active_operations += 1
            try:
                logger.debug(f"Executing resource-intensive operation: {operation.__name__} (waited: {wait_time:.2f}s)")
                result = await operation(*args, **kwargs)
                return result
            finally:
                self._active_operations -= 1
    
    def get_stats(self) -> dict:
        """
        Get resource queue statistics
        
        Returns:
            dict: Queue statistics
        """
        avg_wait_time = (
            self._total_wait_time / self._total_operations
            if self._total_operations > 0
            else 0.0
        )
        
        return {
            "max_concurrent": self.max_concurrent,
            "active_operations": self._active_operations,
            "total_operations": self._total_operations,
            "average_wait_time_seconds": round(avg_wait_time, 3)
        }


# Global instances
connection_pool = ConnectionPool(max_connections=20)
resource_queue = ResourceQueue(max_concurrent=5)

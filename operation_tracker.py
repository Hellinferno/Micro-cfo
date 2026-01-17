#!/usr/bin/env python3
"""
Operation Tracker for Long-running Operations
Tracks operation progress and sends WebSocket updates
"""

import uuid
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OperationStatus(str, Enum):
    """Operation status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationInfo(BaseModel):
    """Information about a tracked operation"""
    operation_id: str
    user_id: str
    operation_type: str
    status: OperationStatus
    progress: int  # 0-100
    message: str
    started_at: str
    updated_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class OperationTracker:
    """
    Tracks long-running operations and sends progress updates via WebSocket
    
    Features:
    - Unique operation ID generation
    - Progress tracking (0-100%)
    - Status updates
    - Result storage
    - Automatic WebSocket notifications
    """
    
    def __init__(self, websocket_manager=None):
        # Active operations: operation_id -> OperationInfo
        self.operations: Dict[str, OperationInfo] = {}
        
        # WebSocket manager for sending updates
        self.websocket_manager = websocket_manager
        
        logger.info("Operation Tracker initialized")
    
    def create_operation(
        self,
        user_id: str,
        operation_type: str,
        initial_message: str = "Operation started"
    ) -> str:
        """
        Create a new tracked operation
        
        Args:
            user_id: User identifier
            operation_type: Type of operation (e.g., "invoice_scan", "compliance_check")
            initial_message: Initial status message
            
        Returns:
            Unique operation ID
        """
        operation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        operation = OperationInfo(
            operation_id=operation_id,
            user_id=user_id,
            operation_type=operation_type,
            status=OperationStatus.PENDING,
            progress=0,
            message=initial_message,
            started_at=now,
            updated_at=now
        )
        
        self.operations[operation_id] = operation
        
        logger.info(f"Created operation {operation_id} for user {user_id}: {operation_type}")
        
        # Send initial notification
        asyncio.create_task(self._send_update(operation_id))
        
        return operation_id
    
    async def update_progress(
        self,
        operation_id: str,
        progress: int,
        message: Optional[str] = None,
        status: Optional[OperationStatus] = None
    ):
        """
        Update operation progress
        
        Args:
            operation_id: Operation identifier
            progress: Progress percentage (0-100)
            message: Optional status message
            status: Optional status update
        """
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return
        
        operation = self.operations[operation_id]
        
        # Update progress
        operation.progress = max(0, min(100, progress))
        
        # Update message if provided
        if message:
            operation.message = message
        
        # Update status if provided
        if status:
            operation.status = status
        elif progress >= 100:
            operation.status = OperationStatus.COMPLETED
        elif progress > 0:
            operation.status = OperationStatus.PROCESSING
        
        # Update timestamp
        operation.updated_at = datetime.utcnow().isoformat()
        
        logger.debug(f"Operation {operation_id} progress: {progress}% - {message or operation.message}")
        
        # Send update notification
        await self._send_update(operation_id)
    
    async def complete_operation(
        self,
        operation_id: str,
        result: Optional[Dict[str, Any]] = None,
        message: str = "Operation completed successfully"
    ):
        """
        Mark operation as completed
        
        Args:
            operation_id: Operation identifier
            result: Optional result data
            message: Completion message
        """
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return
        
        operation = self.operations[operation_id]
        
        operation.status = OperationStatus.COMPLETED
        operation.progress = 100
        operation.message = message
        operation.result = result
        operation.completed_at = datetime.utcnow().isoformat()
        operation.updated_at = operation.completed_at
        
        logger.info(f"Operation {operation_id} completed: {message}")
        
        # Send completion notification
        await self._send_update(operation_id)
    
    async def fail_operation(
        self,
        operation_id: str,
        error: str,
        message: str = "Operation failed"
    ):
        """
        Mark operation as failed
        
        Args:
            operation_id: Operation identifier
            error: Error description
            message: Failure message
        """
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return
        
        operation = self.operations[operation_id]
        
        operation.status = OperationStatus.FAILED
        operation.message = message
        operation.error = error
        operation.completed_at = datetime.utcnow().isoformat()
        operation.updated_at = operation.completed_at
        
        logger.error(f"Operation {operation_id} failed: {error}")
        
        # Send failure notification
        await self._send_update(operation_id)
    
    async def cancel_operation(
        self,
        operation_id: str,
        message: str = "Operation cancelled by user"
    ):
        """
        Cancel an operation
        
        Args:
            operation_id: Operation identifier
            message: Cancellation message
        """
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return
        
        operation = self.operations[operation_id]
        
        operation.status = OperationStatus.CANCELLED
        operation.message = message
        operation.completed_at = datetime.utcnow().isoformat()
        operation.updated_at = operation.completed_at
        
        logger.info(f"Operation {operation_id} cancelled: {message}")
        
        # Send cancellation notification
        await self._send_update(operation_id)
    
    def get_operation(self, operation_id: str) -> Optional[OperationInfo]:
        """
        Get operation information
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            OperationInfo if found, None otherwise
        """
        return self.operations.get(operation_id)
    
    def get_user_operations(self, user_id: str) -> list[OperationInfo]:
        """
        Get all operations for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of OperationInfo for the user
        """
        return [
            op for op in self.operations.values()
            if op.user_id == user_id
        ]
    
    def cleanup_completed_operations(self, max_age_hours: int = 24):
        """
        Remove old completed operations
        
        Args:
            max_age_hours: Maximum age in hours for completed operations
        """
        from datetime import timedelta
        
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=max_age_hours)
        
        to_remove = []
        
        for operation_id, operation in self.operations.items():
            if operation.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
                if operation.completed_at:
                    completed_time = datetime.fromisoformat(operation.completed_at)
                    if completed_time < cutoff:
                        to_remove.append(operation_id)
        
        for operation_id in to_remove:
            del self.operations[operation_id]
            logger.debug(f"Cleaned up old operation {operation_id}")
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old operations")
    
    async def _send_update(self, operation_id: str):
        """
        Send WebSocket update for an operation
        
        Args:
            operation_id: Operation identifier
        """
        if not self.websocket_manager:
            return
        
        operation = self.operations.get(operation_id)
        if not operation:
            return
        
        from websocket_manager import WebSocketMessage
        
        # Create update message
        message = WebSocketMessage(
            type="processing_status",
            data={
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "status": operation.status,
                "progress": operation.progress,
                "message": operation.message,
                "result": operation.result,
                "error": operation.error
            }
        )
        
        # Send to user
        await self.websocket_manager.send_personal_message(operation.user_id, message)


# Global operation tracker instance
operation_tracker = OperationTracker()

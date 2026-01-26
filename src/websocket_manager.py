#!/usr/bin/env python3
"""
WebSocket Manager for Real-time Communication
Handles WebSocket connections, room-based broadcasting, and heartbeat monitoring
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    
    def model_post_init(self, __context):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection"""
    user_id: str
    business_name: Optional[str] = None
    industry_code: Optional[str] = None
    turnover_tier: Optional[str] = None
    connected_at: str
    last_heartbeat: str
    rooms: Set[str] = set()


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates
    
    Features:
    - Connection lifecycle management (connect, disconnect, heartbeat)
    - Room-based broadcasting for user-specific updates
    - Automatic cleanup of stale connections
    """
    
    def __init__(self):
        # Active connections: user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connection info: user_id -> ConnectionInfo
        self.connection_info: Dict[str, ConnectionInfo] = {}
        
        # Rooms: room_name -> Set[user_id]
        self.rooms: Dict[str, Set[str]] = {}
        
        # Heartbeat interval in seconds
        self.heartbeat_interval = 30
        
        # Heartbeat timeout in seconds (disconnect if no heartbeat)
        self.heartbeat_timeout = 90
        
        logger.info("WebSocket Manager initialized")
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        business_name: Optional[str] = None,
        industry_code: Optional[str] = None,
        turnover_tier: Optional[str] = None
    ):
        """
        Accept and register a new WebSocket connection
        
        Args:
            websocket: FastAPI WebSocket instance
            user_id: Unique user identifier
            business_name: User's business name
            industry_code: User's industry classification
            turnover_tier: User's turnover tier
        """
        await websocket.accept()
        
        # Store connection
        self.active_connections[user_id] = websocket
        
        # Store connection info
        now = datetime.utcnow().isoformat()
        self.connection_info[user_id] = ConnectionInfo(
            user_id=user_id,
            business_name=business_name,
            industry_code=industry_code,
            turnover_tier=turnover_tier,
            connected_at=now,
            last_heartbeat=now,
            rooms=set()
        )
        
        logger.info(f"WebSocket connected: user_id={user_id}, business={business_name}")
        
        # Send connection confirmation
        await self.send_personal_message(
            user_id,
            WebSocketMessage(
                type="connection_established",
                data={
                    "user_id": user_id,
                    "message": "Connected to MicroCFO real-time updates",
                    "heartbeat_interval": self.heartbeat_interval
                }
            )
        )
    
    def disconnect(self, user_id: str):
        """
        Disconnect and cleanup a WebSocket connection
        
        Args:
            user_id: User identifier to disconnect
        """
        if user_id in self.active_connections:
            # Remove from all rooms
            if user_id in self.connection_info:
                for room in self.connection_info[user_id].rooms:
                    if room in self.rooms:
                        self.rooms[room].discard(user_id)
                        if not self.rooms[room]:
                            del self.rooms[room]
            
            # Remove connection
            del self.active_connections[user_id]
            
            # Remove connection info
            if user_id in self.connection_info:
                del self.connection_info[user_id]
            
            logger.info(f"WebSocket disconnected: user_id={user_id}")
    
    async def send_personal_message(self, user_id: str, message: WebSocketMessage):
        """
        Send a message to a specific user
        
        Args:
            user_id: Target user identifier
            message: Message to send
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_json(message.model_dump())
                logger.debug(f"Sent message to user {user_id}: {message.type}")
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_room(self, room: str, message: WebSocketMessage):
        """
        Broadcast a message to all users in a room
        
        Args:
            room: Room name
            message: Message to broadcast
        """
        if room not in self.rooms:
            logger.debug(f"Room {room} has no members")
            return
        
        # Get all users in the room
        user_ids = list(self.rooms[room])
        
        logger.info(f"Broadcasting to room {room}: {len(user_ids)} users")
        
        # Send to all users
        for user_id in user_ids:
            await self.send_personal_message(user_id, message)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """
        Broadcast a message to all connected users
        
        Args:
            message: Message to broadcast
        """
        logger.info(f"Broadcasting to all users: {len(self.active_connections)} connections")
        
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(user_id, message)
    
    def join_room(self, user_id: str, room: str):
        """
        Add a user to a room
        
        Args:
            user_id: User identifier
            room: Room name
        """
        if user_id not in self.active_connections:
            logger.warning(f"Cannot join room: user {user_id} not connected")
            return
        
        # Create room if it doesn't exist
        if room not in self.rooms:
            self.rooms[room] = set()
        
        # Add user to room
        self.rooms[room].add(user_id)
        
        # Update connection info
        if user_id in self.connection_info:
            self.connection_info[user_id].rooms.add(room)
        
        logger.info(f"User {user_id} joined room {room}")
    
    def leave_room(self, user_id: str, room: str):
        """
        Remove a user from a room
        
        Args:
            user_id: User identifier
            room: Room name
        """
        if room in self.rooms:
            self.rooms[room].discard(user_id)
            
            # Remove empty rooms
            if not self.rooms[room]:
                del self.rooms[room]
        
        # Update connection info
        if user_id in self.connection_info:
            self.connection_info[user_id].rooms.discard(room)
        
        logger.info(f"User {user_id} left room {room}")
    
    def update_heartbeat(self, user_id: str):
        """
        Update the last heartbeat timestamp for a user
        
        Args:
            user_id: User identifier
        """
        if user_id in self.connection_info:
            self.connection_info[user_id].last_heartbeat = datetime.utcnow().isoformat()
            logger.debug(f"Heartbeat updated for user {user_id}")
    
    async def check_stale_connections(self):
        """
        Check for stale connections and disconnect them
        Should be called periodically
        """
        now = datetime.utcnow()
        stale_users = []
        
        for user_id, info in self.connection_info.items():
            last_heartbeat = datetime.fromisoformat(info.last_heartbeat)
            elapsed = (now - last_heartbeat).total_seconds()
            
            if elapsed > self.heartbeat_timeout:
                stale_users.append(user_id)
                logger.warning(f"Stale connection detected: user {user_id}, last heartbeat {elapsed}s ago")
        
        # Disconnect stale connections
        for user_id in stale_users:
            self.disconnect(user_id)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_room_members(self, room: str) -> Set[str]:
        """Get all user IDs in a room"""
        return self.rooms.get(room, set()).copy()
    
    def get_user_rooms(self, user_id: str) -> Set[str]:
        """Get all rooms a user is in"""
        if user_id in self.connection_info:
            return self.connection_info[user_id].rooms.copy()
        return set()
    
    def is_connected(self, user_id: str) -> bool:
        """Check if a user is connected"""
        return user_id in self.active_connections


# Global WebSocket manager instance
websocket_manager = WebSocketManager()

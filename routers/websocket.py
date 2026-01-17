#!/usr/bin/env python3
"""
WebSocket Router for Real-time Communication
Handles WebSocket endpoint and message routing
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from pydantic import BaseModel

from websocket_manager import websocket_manager, WebSocketMessage
from middleware.auth import get_current_user_ws

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class InboundMessage(BaseModel):
    """Structure for messages received from clients"""
    type: str
    data: dict


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time communication
    
    Query Parameters:
        token: JWT authentication token
    
    Message Types (Client -> Server):
        - heartbeat: Keep connection alive
        - subscribe_updates: Subscribe to specific update categories
        - unsubscribe_updates: Unsubscribe from update categories
    
    Message Types (Server -> Client):
        - connection_established: Connection confirmation
        - legal_update: New legal notification
        - processing_status: Long-running operation status
        - error: Error message
    """
    user_id = None
    
    try:
        # Authenticate user from token
        if not token:
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "data": {"message": "Authentication token required"},
                "timestamp": None
            })
            await websocket.close(code=1008)  # Policy violation
            return
        
        # Verify token and get user info
        try:
            user_data = await get_current_user_ws(token)
            user_id = user_data.get("user_id")
            business_name = user_data.get("business_name")
            industry_code = user_data.get("industry_code")
            turnover_tier = user_data.get("turnover_tier")
        except Exception as e:
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "data": {"message": f"Authentication failed: {str(e)}"},
                "timestamp": None
            })
            await websocket.close(code=1008)
            return
        
        # Connect user
        await websocket_manager.connect(
            websocket=websocket,
            user_id=user_id,
            business_name=business_name,
            industry_code=industry_code,
            turnover_tier=turnover_tier
        )
        
        # Auto-subscribe to user-specific room
        websocket_manager.join_room(user_id, f"user:{user_id}")
        
        # Auto-subscribe to industry-specific room if available
        if industry_code:
            websocket_manager.join_room(user_id, f"industry:{industry_code}")
        
        # Auto-subscribe to turnover tier room if available
        if turnover_tier:
            websocket_manager.join_room(user_id, f"turnover:{turnover_tier}")
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_dict = json.loads(data)
                
                # Parse message
                try:
                    message = InboundMessage(**message_dict)
                except Exception as e:
                    logger.error(f"Invalid message format from user {user_id}: {e}")
                    await websocket_manager.send_personal_message(
                        user_id,
                        WebSocketMessage(
                            type="error",
                            data={"message": "Invalid message format"}
                        )
                    )
                    continue
                
                # Handle different message types
                if message.type == "heartbeat":
                    # Update heartbeat timestamp
                    websocket_manager.update_heartbeat(user_id)
                    
                    # Send heartbeat acknowledgment
                    await websocket_manager.send_personal_message(
                        user_id,
                        WebSocketMessage(
                            type="heartbeat_ack",
                            data={"status": "alive"}
                        )
                    )
                
                elif message.type == "subscribe_updates":
                    # Subscribe to specific update categories
                    categories = message.data.get("categories", [])
                    
                    for category in categories:
                        room = f"updates:{category}"
                        websocket_manager.join_room(user_id, room)
                    
                    await websocket_manager.send_personal_message(
                        user_id,
                        WebSocketMessage(
                            type="subscription_confirmed",
                            data={
                                "categories": categories,
                                "message": f"Subscribed to {len(categories)} categories"
                            }
                        )
                    )
                    
                    logger.info(f"User {user_id} subscribed to categories: {categories}")
                
                elif message.type == "unsubscribe_updates":
                    # Unsubscribe from specific update categories
                    categories = message.data.get("categories", [])
                    
                    for category in categories:
                        room = f"updates:{category}"
                        websocket_manager.leave_room(user_id, room)
                    
                    await websocket_manager.send_personal_message(
                        user_id,
                        WebSocketMessage(
                            type="unsubscription_confirmed",
                            data={
                                "categories": categories,
                                "message": f"Unsubscribed from {len(categories)} categories"
                            }
                        )
                    )
                    
                    logger.info(f"User {user_id} unsubscribed from categories: {categories}")
                
                else:
                    # Unknown message type
                    logger.warning(f"Unknown message type from user {user_id}: {message.type}")
                    await websocket_manager.send_personal_message(
                        user_id,
                        WebSocketMessage(
                            type="error",
                            data={"message": f"Unknown message type: {message.type}"}
                        )
                    )
            
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected normally: user {user_id}")
                break
            
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error from user {user_id}: {e}")
                await websocket_manager.send_personal_message(
                    user_id,
                    WebSocketMessage(
                        type="error",
                        data={"message": "Invalid JSON format"}
                    )
                )
            
            except Exception as e:
                logger.error(f"Error handling message from user {user_id}: {e}", exc_info=True)
                await websocket_manager.send_personal_message(
                    user_id,
                    WebSocketMessage(
                        type="error",
                        data={"message": "Internal server error"}
                    )
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
    
    finally:
        # Cleanup on disconnect
        if user_id:
            websocket_manager.disconnect(user_id)


@router.get("/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics
    
    Returns:
        Connection statistics including active connections and rooms
    """
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "total_rooms": len(websocket_manager.rooms),
        "rooms": {
            room: len(members)
            for room, members in websocket_manager.rooms.items()
        }
    }

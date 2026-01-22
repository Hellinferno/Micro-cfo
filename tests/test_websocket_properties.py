#!/usr/bin/env python3
"""
Property-Based Tests for WebSocket Real-time Features
Tests WebSocket connection management, real-time updates, and resilience
"""

import pytest
import asyncio
import json
from hypothesis import given, settings, strategies as st
from hypothesis import assume
from datetime import datetime
from typing import List, Dict

from websocket_manager import WebSocketManager, WebSocketMessage, ConnectionInfo
from operation_tracker import OperationTracker, OperationStatus


# Test fixtures
@pytest.fixture
def ws_manager():
    """Create a fresh WebSocket manager for each test"""
    return WebSocketManager()


@pytest.fixture
def op_tracker():
    """Create a fresh operation tracker for each test"""
    return OperationTracker()


# Mock WebSocket class for testing
class MockWebSocket:
    """Mock WebSocket for testing without actual network connections"""
    
    def __init__(self):
        self.messages = []
        self.closed = False
        self.accepted = False
    
    async def accept(self):
        """Mock accept method"""
        self.accepted = True
    
    async def send_json(self, data: dict):
        """Mock send_json method"""
        if self.closed:
            raise RuntimeError("WebSocket is closed")
        self.messages.append(data)
    
    async def close(self, code: int = 1000):
        """Mock close method"""
        self.closed = True
    
    def get_messages(self) -> List[dict]:
        """Get all sent messages"""
        return self.messages.copy()
    
    def clear_messages(self):
        """Clear message history"""
        self.messages.clear()


# Hypothesis strategies
user_id_strategy = st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd'),
    whitelist_characters='_-'
))

business_name_strategy = st.text(min_size=1, max_size=100)

industry_code_strategy = st.sampled_from([
    'textile', 'trading', 'manufacturing', 'technology', 'services'
])

turnover_tier_strategy = st.sampled_from([
    '< 5Cr', '5-20Cr', '> 20Cr'
])

room_name_strategy = st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd'),
    whitelist_characters='_-:'
))

message_type_strategy = st.sampled_from([
    'legal_update', 'processing_status', 'error'  # Removed 'connection_established' as it's a system message
])


# Property 3: Real-time Update Delivery
# For any relevant legal update or long-running operation status change,
# all connected clients who should receive the update based on their business
# profile should receive it within the specified time window.

@pytest.mark.asyncio
@given(
    user_ids=st.lists(user_id_strategy, min_size=1, max_size=10, unique=True),
    industry_codes=st.lists(industry_code_strategy, min_size=1, max_size=5),
    message_type=message_type_strategy
)
@settings(max_examples=100, deadline=None)
async def test_property_3_real_time_update_delivery(
    user_ids: List[str],
    industry_codes: List[str],
    message_type: str
):
    """
    Feature: frontend-backend-integration, Property 3: Real-time Update Delivery
    
    Validates: Requirements 3.1, 3.2, 3.4
    
    Property: For any relevant update, all connected clients who should receive
    the update based on their business profile should receive it.
    
    Test Strategy:
    1. Connect multiple users with different industry codes
    2. Send an industry-specific update
    3. Verify only users in that industry receive the update
    4. Verify all users in that industry receive the update
    """
    ws_manager = WebSocketManager()
    
    # Create mock websockets and connect users
    websockets = {}
    for user_id in user_ids:
        # Assign random industry to each user
        industry = industry_codes[hash(user_id) % len(industry_codes)]
        
        mock_ws = MockWebSocket()
        websockets[user_id] = mock_ws
        
        # Connect user
        await ws_manager.connect(
            websocket=mock_ws,
            user_id=user_id,
            business_name=f"Business {user_id}",
            industry_code=industry,
            turnover_tier="5-20Cr"
        )
        
        # Join industry room
        ws_manager.join_room(user_id, f"industry:{industry}")
    
    # For each industry, send an update and verify delivery
    for target_industry in industry_codes:
        # Clear previous messages
        for ws in websockets.values():
            ws.clear_messages()
        
        # Create industry-specific update
        update_message = WebSocketMessage(
            type=message_type,
            data={
                "title": f"Update for {target_industry}",
                "industry": target_industry,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Broadcast to industry room
        await ws_manager.broadcast_to_room(f"industry:{target_industry}", update_message)
        
        # Verify delivery
        for user_id, mock_ws in websockets.items():
            user_industry = ws_manager.connection_info[user_id].industry_code
            
            # Check if user should receive the update
            should_receive = (user_industry == target_industry)
            
            # Get messages sent to this user (excluding connection_established)
            user_messages = [
                msg for msg in mock_ws.get_messages()
                if msg.get('type') != 'connection_established'
            ]
            
            if should_receive:
                # User in target industry should receive the update
                assert len(user_messages) > 0, \
                    f"User {user_id} in industry {user_industry} should receive update for {target_industry}"
                
                # Verify message content
                received_update = user_messages[-1]
                assert received_update['type'] == message_type
                assert received_update['data']['industry'] == target_industry
            else:
                # User not in target industry should NOT receive the update
                assert len(user_messages) == 0, \
                    f"User {user_id} in industry {user_industry} should NOT receive update for {target_industry}"


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    operation_type=st.sampled_from(['invoice_scan', 'compliance_check', 'subsidy_search']),
    progress_updates=st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=10)
)
@settings(max_examples=100, deadline=None)
async def test_property_3_operation_progress_updates(
    user_id: str,
    operation_type: str,
    progress_updates: List[int]
):
    """
    Feature: frontend-backend-integration, Property 3: Real-time Update Delivery
    
    Validates: Requirements 3.2
    
    Property: For any long-running operation, progress updates should be
    delivered to the user in order.
    
    Test Strategy:
    1. Create an operation for a user
    2. Send multiple progress updates
    3. Verify all updates are received in order
    4. Verify progress values are monotonically increasing (or equal)
    """
    ws_manager = WebSocketManager()
    op_tracker = OperationTracker(websocket_manager=ws_manager)
    
    # Connect user
    mock_ws = MockWebSocket()
    await ws_manager.connect(
        websocket=mock_ws,
        user_id=user_id,
        business_name=f"Business {user_id}"
    )
    
    # Clear connection message
    mock_ws.clear_messages()
    
    # Create operation
    operation_id = op_tracker.create_operation(
        user_id=user_id,
        operation_type=operation_type,
        initial_message="Starting operation"
    )
    
    # Wait for initial message
    await asyncio.sleep(0.1)
    
    # Sort progress updates to ensure monotonic progression
    sorted_progress = sorted(progress_updates)
    
    # Send progress updates
    for progress in sorted_progress:
        await op_tracker.update_progress(
            operation_id,
            progress=progress,
            message=f"Progress: {progress}%"
        )
        await asyncio.sleep(0.05)  # Small delay to ensure ordering
    
    # Get all processing_status messages
    messages = mock_ws.get_messages()
    status_messages = [
        msg for msg in messages
        if msg.get('type') == 'processing_status'
    ]
    
    # Verify we received updates
    assert len(status_messages) >= len(sorted_progress), \
        f"Should receive at least {len(sorted_progress)} status updates"
    
    # Verify progress values are in order
    received_progress = [msg['data']['progress'] for msg in status_messages]
    
    # Progress should be monotonically non-decreasing
    for i in range(len(received_progress) - 1):
        assert received_progress[i] <= received_progress[i + 1], \
            f"Progress should be non-decreasing: {received_progress[i]} > {received_progress[i + 1]}"


@pytest.mark.asyncio
@given(
    user_ids=st.lists(user_id_strategy, min_size=2, max_size=10, unique=True),
    message_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, deadline=None)
async def test_property_3_broadcast_to_all_users(
    user_ids: List[str],
    message_data: Dict
):
    """
    Feature: frontend-backend-integration, Property 3: Real-time Update Delivery
    
    Validates: Requirements 3.1, 3.4
    
    Property: When broadcasting to all users, every connected user should
    receive the message exactly once.
    
    Test Strategy:
    1. Connect multiple users
    2. Broadcast a message to all users
    3. Verify each user receives exactly one copy of the message
    """
    ws_manager = WebSocketManager()
    
    # Connect all users
    websockets = {}
    for user_id in user_ids:
        mock_ws = MockWebSocket()
        websockets[user_id] = mock_ws
        
        await ws_manager.connect(
            websocket=mock_ws,
            user_id=user_id,
            business_name=f"Business {user_id}"
        )
        
        # Clear connection message
        mock_ws.clear_messages()
    
    # Create broadcast message
    broadcast_message = WebSocketMessage(
        type="legal_update",
        data=message_data
    )
    
    # Broadcast to all users
    await ws_manager.broadcast_to_all(broadcast_message)
    
    # Verify each user received exactly one message
    for user_id, mock_ws in websockets.items():
        messages = mock_ws.get_messages()
        
        # Should receive exactly one message
        assert len(messages) == 1, \
            f"User {user_id} should receive exactly 1 message, got {len(messages)}"
        
        # Verify message content
        received_msg = messages[0]
        assert received_msg['type'] == "legal_update"
        assert received_msg['data'] == message_data


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    rooms=st.lists(room_name_strategy, min_size=1, max_size=5, unique=True)
)
@settings(max_examples=100, deadline=None)
async def test_property_3_room_based_filtering(
    user_id: str,
    rooms: List[str]
):
    """
    Feature: frontend-backend-integration, Property 3: Real-time Update Delivery
    
    Validates: Requirements 3.4
    
    Property: Users should only receive messages for rooms they have joined.
    
    Test Strategy:
    1. Connect a user
    2. Join some rooms but not others
    3. Send messages to all rooms
    4. Verify user only receives messages from joined rooms
    """
    ws_manager = WebSocketManager()
    
    # Connect user
    mock_ws = MockWebSocket()
    await ws_manager.connect(
        websocket=mock_ws,
        user_id=user_id,
        business_name=f"Business {user_id}"
    )
    
    # Clear connection message
    mock_ws.clear_messages()
    
    # Join half of the rooms (at least 1)
    joined_rooms = rooms[:max(1, len(rooms) // 2)]
    not_joined_rooms = rooms[len(joined_rooms):]
    
    for room in joined_rooms:
        ws_manager.join_room(user_id, room)
    
    # Send messages to all rooms
    for room in rooms:
        message = WebSocketMessage(
            type="test_message",
            data={"room": room, "content": f"Message for {room}"}
        )
        await ws_manager.broadcast_to_room(room, message)
    
    # Get received messages
    messages = mock_ws.get_messages()
    received_rooms = [msg['data']['room'] for msg in messages]
    
    # Verify user received messages only from joined rooms
    assert len(received_rooms) == len(joined_rooms), \
        f"Should receive {len(joined_rooms)} messages, got {len(received_rooms)}"
    
    for room in received_rooms:
        assert room in joined_rooms, \
            f"Received message from room {room} which was not joined"
    
    for room in not_joined_rooms:
        assert room not in received_rooms, \
            f"Should not receive message from room {room} which was not joined"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


# Property 9: WebSocket Connection Resilience
# For any WebSocket connection, the system should maintain the connection
# during normal operation and handle connection drops gracefully with
# automatic reconnection capabilities.

@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    business_name=business_name_strategy,
    industry_code=industry_code_strategy
)
@settings(max_examples=100, deadline=None)
async def test_property_9_connection_lifecycle(
    user_id: str,
    business_name: str,
    industry_code: str
):
    """
    Feature: frontend-backend-integration, Property 9: WebSocket Connection Resilience
    
    Validates: Requirements 3.3, 3.5
    
    Property: For any user, connecting and then disconnecting should properly
    clean up all resources and room memberships.
    
    Test Strategy:
    1. Connect a user
    2. Join multiple rooms
    3. Disconnect the user
    4. Verify all resources are cleaned up
    """
    ws_manager = WebSocketManager()
    
    # Connect user
    mock_ws = MockWebSocket()
    await ws_manager.connect(
        websocket=mock_ws,
        user_id=user_id,
        business_name=business_name,
        industry_code=industry_code,
        turnover_tier="5-20Cr"
    )
    
    # Verify connection is established
    assert ws_manager.is_connected(user_id), \
        f"User {user_id} should be connected"
    assert user_id in ws_manager.connection_info, \
        f"User {user_id} should have connection info"
    
    # Join some rooms
    rooms = [f"room_{i}" for i in range(3)]
    for room in rooms:
        ws_manager.join_room(user_id, room)
    
    # Verify rooms are joined
    user_rooms = ws_manager.get_user_rooms(user_id)
    assert len(user_rooms) == len(rooms), \
        f"User should be in {len(rooms)} rooms"
    
    # Disconnect user
    ws_manager.disconnect(user_id)
    
    # Verify cleanup
    assert not ws_manager.is_connected(user_id), \
        f"User {user_id} should be disconnected"
    assert user_id not in ws_manager.connection_info, \
        f"User {user_id} connection info should be removed"
    
    # Verify rooms are cleaned up
    for room in rooms:
        room_members = ws_manager.get_room_members(room)
        assert user_id not in room_members, \
            f"User {user_id} should be removed from room {room}"


@pytest.mark.asyncio
@given(
    user_ids=st.lists(user_id_strategy, min_size=2, max_size=10, unique=True),
    disconnect_indices=st.lists(st.integers(min_value=0, max_value=9), min_size=1, max_size=5, unique=True)
)
@settings(max_examples=100, deadline=None)
async def test_property_9_partial_disconnection_resilience(
    user_ids: List[str],
    disconnect_indices: List[int]
):
    """
    Feature: frontend-backend-integration, Property 9: WebSocket Connection Resilience
    
    Validates: Requirements 3.3, 3.5
    
    Property: When some users disconnect, other users should continue to
    receive messages normally.
    
    Test Strategy:
    1. Connect multiple users
    2. Disconnect some users
    3. Send broadcast message
    4. Verify only connected users receive the message
    """
    # Filter disconnect indices to valid range
    valid_disconnect_indices = [i for i in disconnect_indices if i < len(user_ids)]
    assume(len(valid_disconnect_indices) > 0)
    assume(len(valid_disconnect_indices) < len(user_ids))  # Don't disconnect everyone
    
    ws_manager = WebSocketManager()
    
    # Connect all users
    websockets = {}
    for user_id in user_ids:
        mock_ws = MockWebSocket()
        websockets[user_id] = mock_ws
        
        await ws_manager.connect(
            websocket=mock_ws,
            user_id=user_id,
            business_name=f"Business {user_id}"
        )
    
    # Disconnect some users
    disconnected_users = [user_ids[i] for i in valid_disconnect_indices]
    for user_id in disconnected_users:
        ws_manager.disconnect(user_id)
    
    # Clear messages for all websockets
    for ws in websockets.values():
        ws.clear_messages()
    
    # Send broadcast message
    test_message = WebSocketMessage(
        type="test_message",
        data={"content": "Test broadcast after disconnection"}
    )
    await ws_manager.broadcast_to_all(test_message)
    
    # Verify delivery
    for user_id, mock_ws in websockets.items():
        messages = mock_ws.get_messages()
        
        if user_id in disconnected_users:
            # Disconnected users should not receive messages
            assert len(messages) == 0, \
                f"Disconnected user {user_id} should not receive messages"
        else:
            # Connected users should receive the message
            assert len(messages) == 1, \
                f"Connected user {user_id} should receive exactly 1 message"
            assert messages[0]['type'] == "test_message"


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    heartbeat_count=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, deadline=None)
async def test_property_9_heartbeat_updates(
    user_id: str,
    heartbeat_count: int
):
    """
    Feature: frontend-backend-integration, Property 9: WebSocket Connection Resilience
    
    Validates: Requirements 3.3, 3.5
    
    Property: Heartbeat updates should maintain connection freshness and
    prevent premature disconnection.
    
    Test Strategy:
    1. Connect a user
    2. Send multiple heartbeat updates
    3. Verify connection remains active
    4. Verify heartbeat timestamp is updated
    """
    ws_manager = WebSocketManager()
    
    # Connect user
    mock_ws = MockWebSocket()
    await ws_manager.connect(
        websocket=mock_ws,
        user_id=user_id,
        business_name=f"Business {user_id}"
    )
    
    # Get initial heartbeat timestamp
    initial_heartbeat = ws_manager.connection_info[user_id].last_heartbeat
    
    # Send heartbeat updates
    for i in range(heartbeat_count):
        await asyncio.sleep(0.01)  # Small delay to ensure timestamp changes
        ws_manager.update_heartbeat(user_id)
    
    # Verify connection is still active
    assert ws_manager.is_connected(user_id), \
        f"User {user_id} should still be connected after {heartbeat_count} heartbeats"
    
    # Verify heartbeat timestamp was updated
    final_heartbeat = ws_manager.connection_info[user_id].last_heartbeat
    assert final_heartbeat > initial_heartbeat, \
        f"Heartbeat timestamp should be updated: {initial_heartbeat} -> {final_heartbeat}"


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    room=room_name_strategy
)
@settings(max_examples=100, deadline=None)
async def test_property_9_room_membership_persistence(
    user_id: str,
    room: str
):
    """
    Feature: frontend-backend-integration, Property 9: WebSocket Connection Resilience
    
    Validates: Requirements 3.3
    
    Property: Room memberships should persist throughout the connection
    lifecycle until explicitly removed or disconnected.
    
    Test Strategy:
    1. Connect a user
    2. Join a room
    3. Send multiple messages to the room
    4. Verify user receives all messages
    5. Leave the room
    6. Send another message
    7. Verify user does not receive it
    """
    ws_manager = WebSocketManager()
    
    # Connect user
    mock_ws = MockWebSocket()
    await ws_manager.connect(
        websocket=mock_ws,
        user_id=user_id,
        business_name=f"Business {user_id}"
    )
    
    # Clear connection message
    mock_ws.clear_messages()
    
    # Join room
    ws_manager.join_room(user_id, room)
    
    # Send multiple messages to the room
    message_count = 5
    for i in range(message_count):
        message = WebSocketMessage(
            type="test_message",
            data={"sequence": i, "room": room}
        )
        await ws_manager.broadcast_to_room(room, message)
    
    # Verify user received all messages
    messages = mock_ws.get_messages()
    assert len(messages) == message_count, \
        f"User should receive {message_count} messages while in room"
    
    # Clear messages
    mock_ws.clear_messages()
    
    # Leave room
    ws_manager.leave_room(user_id, room)
    
    # Send another message to the room
    final_message = WebSocketMessage(
        type="test_message",
        data={"sequence": message_count, "room": room}
    )
    await ws_manager.broadcast_to_room(room, final_message)
    
    # Verify user did not receive the message
    messages = mock_ws.get_messages()
    assert len(messages) == 0, \
        f"User should not receive messages after leaving room"


@pytest.mark.asyncio
@given(
    user_ids=st.lists(user_id_strategy, min_size=1, max_size=10, unique=True)
)
@settings(max_examples=100, deadline=None)
async def test_property_9_concurrent_connections(
    user_ids: List[str]
):
    """
    Feature: frontend-backend-integration, Property 9: WebSocket Connection Resilience
    
    Validates: Requirements 3.3
    
    Property: The system should handle multiple concurrent connections
    without interference.
    
    Test Strategy:
    1. Connect multiple users concurrently
    2. Verify all connections are established
    3. Send personal messages to each user
    4. Verify each user receives only their own messages
    """
    ws_manager = WebSocketManager()
    
    # Connect all users concurrently
    websockets = {}
    connect_tasks = []
    
    for user_id in user_ids:
        mock_ws = MockWebSocket()
        websockets[user_id] = mock_ws
        connect_tasks.append(
            ws_manager.connect(
                websocket=mock_ws,
                user_id=user_id,
                business_name=f"Business {user_id}"
            )
        )
    
    # Wait for all connections
    await asyncio.gather(*connect_tasks)
    
    # Verify all connections are established
    assert ws_manager.get_connection_count() == len(user_ids), \
        f"Should have {len(user_ids)} active connections"
    
    # Clear connection messages
    for ws in websockets.values():
        ws.clear_messages()
    
    # Send personal message to each user
    for user_id in user_ids:
        message = WebSocketMessage(
            type="personal_message",
            data={"recipient": user_id, "content": f"Message for {user_id}"}
        )
        await ws_manager.send_personal_message(user_id, message)
    
    # Verify each user received only their own message
    for user_id, mock_ws in websockets.items():
        messages = mock_ws.get_messages()
        
        assert len(messages) == 1, \
            f"User {user_id} should receive exactly 1 message"
        
        received_msg = messages[0]
        assert received_msg['data']['recipient'] == user_id, \
            f"User {user_id} should receive their own message"

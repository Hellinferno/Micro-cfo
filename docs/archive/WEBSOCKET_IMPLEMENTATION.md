# WebSocket Real-time Features Implementation

## Overview

Successfully implemented comprehensive WebSocket functionality for real-time communication in the MicroCFO Integration Server. This implementation enables live updates for legal notifications, operation progress tracking, and bidirectional communication between the server and connected clients.

## Components Implemented

### 1. WebSocket Manager (`websocket_manager.py`)

Core WebSocket connection management system with the following features:

- **Connection Lifecycle Management**
  - Accept and register new WebSocket connections
  - Track connection metadata (user_id, business_name, industry_code, turnover_tier)
  - Graceful disconnection and resource cleanup
  - Automatic stale connection detection (90-second timeout)

- **Room-based Broadcasting**
  - Create and manage virtual rooms for targeted messaging
  - User-specific rooms (`user:{user_id}`)
  - Industry-specific rooms (`industry:{industry_code}`)
  - Turnover tier rooms (`turnover:{tier}`)
  - Custom category rooms (`updates:{category}`)

- **Heartbeat Monitoring**
  - 30-second heartbeat interval
  - 90-second timeout for stale connections
  - Automatic cleanup of inactive connections

- **Message Delivery**
  - Personal messages to specific users
  - Room-based broadcasts
  - Global broadcasts to all connected users

### 2. WebSocket Router (`routers/websocket.py`)

FastAPI WebSocket endpoint with authentication and message routing:

- **Endpoint**: `/ws/connect?token={jwt_token}`
- **Authentication**: JWT token-based authentication via query parameter
- **Auto-subscription**: Automatic room joining based on user profile
  - User-specific room
  - Industry-specific room
  - Turnover tier room

- **Message Types (Client → Server)**:
  - `heartbeat`: Keep connection alive
  - `subscribe_updates`: Subscribe to specific update categories
  - `unsubscribe_updates`: Unsubscribe from categories

- **Message Types (Server → Client)**:
  - `connection_established`: Connection confirmation
  - `legal_update`: New legal notification
  - `processing_status`: Long-running operation status
  - `heartbeat_ack`: Heartbeat acknowledgment
  - `error`: Error messages

### 3. Operation Tracker (`operation_tracker.py`)

Tracks long-running operations with real-time progress updates:

- **Operation Management**
  - Unique operation ID generation (UUID)
  - Progress tracking (0-100%)
  - Status tracking (pending, processing, completed, failed, cancelled)
  - Result and error storage

- **Automatic WebSocket Updates**
  - Progress updates sent automatically to users
  - Completion notifications
  - Failure notifications with error details

- **Cleanup**
  - Automatic cleanup of old completed operations (24-hour retention)
  - Hourly cleanup task

### 4. Legal Sentinel Integration

Enhanced `sentinel_monitor.py` with WebSocket support:

- **Real-time Legal Alerts**
  - Push notifications to connected clients
  - User profile-based filtering
  - Industry-specific broadcasts
  - Personal alerts for highly relevant updates

- **Dual Alert System**
  - Legacy WhatsApp alerts (console output)
  - Real-time WebSocket alerts

### 5. Visual Auditor Integration

Updated `routers/visual_auditor.py` with operation tracking:

- **Progress Updates for Document Processing**
  - File validation progress (10%)
  - File saving progress (20%)
  - File conversion progress (40%)
  - AI processing progress (60%)
  - Result formatting progress (80%)
  - Completion (100%)

- **Real-time Status Updates**
  - Sent via WebSocket during document upload and processing
  - Includes operation ID for client-side tracking

## Integration with Main Server

Updated `integration_server.py` with:

- WebSocket router inclusion
- WebSocket manager initialization
- Operation tracker initialization with WebSocket support
- Legal Sentinel initialization with WebSocket support
- Background tasks:
  - Heartbeat checker (runs every 60 seconds)
  - Operation cleanup (runs every hour)

## Property-Based Tests

Comprehensive test suite (`test_websocket_properties.py`) with 9 tests covering:

### Property 3: Real-time Update Delivery (4 tests)
- Industry-specific update filtering and delivery
- Operation progress update ordering
- Broadcast to all users
- Room-based message filtering

### Property 9: WebSocket Connection Resilience (5 tests)
- Connection lifecycle and cleanup
- Partial disconnection resilience
- Heartbeat updates
- Room membership persistence
- Concurrent connections

**All tests passed with 100 iterations each using Hypothesis.**

## Requirements Validated

✅ **Requirement 3.1**: Legal Sentinel pushes notifications to connected clients  
✅ **Requirement 3.2**: Long-running operations provide status updates via WebSocket  
✅ **Requirement 3.3**: WebSocket connections maintained for real-time features  
✅ **Requirement 3.4**: User profile changes update monitoring filters immediately  
✅ **Requirement 3.5**: Connection drops handled gracefully with reconnection support  

## Usage Examples

### Client Connection (JavaScript)

```javascript
// Connect with JWT token
const token = "your-jwt-token";
const ws = new WebSocket(`ws://localhost:8000/ws/connect?token=${token}`);

// Handle connection
ws.onopen = () => {
  console.log("Connected to MicroCFO real-time updates");
};

// Handle messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'connection_established':
      console.log("Connection confirmed:", message.data);
      break;
    
    case 'legal_update':
      console.log("New legal update:", message.data);
      // Display notification to user
      break;
    
    case 'processing_status':
      console.log("Operation progress:", message.data.progress + "%");
      // Update progress bar
      break;
    
    case 'heartbeat_ack':
      // Connection is alive
      break;
  }
};

// Send heartbeat every 30 seconds
setInterval(() => {
  ws.send(JSON.stringify({
    type: 'heartbeat',
    data: {}
  }));
}, 30000);

// Subscribe to specific updates
ws.send(JSON.stringify({
  type: 'subscribe_updates',
  data: {
    categories: ['gst', 'income_tax', 'companies_act']
  }
}));
```

### Server-side Broadcasting (Python)

```python
from websocket_manager import websocket_manager, WebSocketMessage

# Send personal message
await websocket_manager.send_personal_message(
    user_id="user_123",
    message=WebSocketMessage(
        type="legal_update",
        data={
            "title": "New GST Amendment",
            "relevance": "high"
        }
    )
)

# Broadcast to industry
await websocket_manager.broadcast_to_room(
    room="industry:textile",
    message=WebSocketMessage(
        type="legal_update",
        data={
            "title": "Textile Industry Update",
            "source": "CBIC"
        }
    )
)

# Broadcast to all users
await websocket_manager.broadcast_to_all(
    message=WebSocketMessage(
        type="system_announcement",
        data={
            "message": "System maintenance scheduled"
        }
    )
)
```

## Architecture Benefits

1. **Scalability**: Room-based architecture allows efficient message routing
2. **Resilience**: Automatic stale connection detection and cleanup
3. **Flexibility**: Easy to add new message types and rooms
4. **Testability**: Comprehensive property-based tests ensure correctness
5. **Security**: JWT authentication for all WebSocket connections
6. **Performance**: Async/await throughout for non-blocking operations

## Next Steps

The WebSocket infrastructure is now ready for:
- Frontend integration with React
- Additional real-time features (chat, notifications, etc.)
- Monitoring and analytics dashboards
- Load testing and performance optimization

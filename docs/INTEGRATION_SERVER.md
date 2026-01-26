# MicroCFO Integration Server

FastAPI-based integration layer that bridges the React frontend with the MCP server backend.

## Features

- ✅ FastAPI application with async support
- ✅ CORS configuration for frontend communication
- ✅ Structured project organization with routers and middleware
- ✅ Environment-based configuration
- ✅ Health check endpoint for monitoring
- ✅ Error handling with user-friendly messages
- ✅ Security middleware (Trusted Host)
- ✅ Comprehensive logging

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn[standard] python-multipart
```

### 2. Run the Server

```bash
# Development mode with hot reload
python integration_server.py

# Or using uvicorn directly
uvicorn integration_server:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the Server

```bash
# Run automated tests
python test_integration_server.py

# Manual testing
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/status
```

## Configuration

The server can be configured using environment variables. Copy `.env.integration` to `.env` and modify as needed:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Frontend Configuration  
FRONTEND_URL=http://localhost:5173

# Security Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
```

## API Endpoints

### System Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check for monitoring
- `GET /api/v1/status` - API version status

### Agent Endpoints (Coming in subsequent tasks)

- `POST /api/v1/agents/visual-auditor/scan-invoice` - Agent A (Visual Auditor)
- `POST /api/v1/agents/legal-sentinel/check-compliance` - Agent B (Legal Sentinel)
- `POST /api/v1/agents/subsidy-hunter/find-subsidies` - Agent C (Subsidy Hunter)
- `POST /api/v1/agents/negotiator/generate-draft` - Agent D (Negotiator)

### Authentication Endpoints (Coming in task 8)

- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/auth/profile` - User profile

## Project Structure

```
├── integration_server.py      # Main FastAPI application
├── config.py                  # Configuration management
├── routers/                   # API route modules (future)
├── middleware/                # Custom middleware (future)
├── test_integration_server.py # Test suite
└── .env.integration          # Environment configuration template
```

## Development

### Adding New Endpoints

1. Create router modules in `routers/` directory
2. Import and include routers in `integration_server.py`
3. Add tests in `test_integration_server.py`

### Running Tests

```bash
# Run integration tests
python test_integration_server.py

# Check server imports
python -c "import integration_server; print('✅ Server imports successfully')"
```

## Next Steps

This foundation server is ready for:

1. **Task 2**: MCP Bridge implementation
2. **Task 3-6**: Agent endpoint implementation  
3. **Task 8**: Authentication system
4. **Task 9**: WebSocket support for real-time features

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 7.3**: CORS configuration for frontend domain communication ✅
- **Requirement 7.4**: Health check endpoints for monitoring ✅

The server provides a solid foundation for the complete frontend-backend integration as specified in the design document.
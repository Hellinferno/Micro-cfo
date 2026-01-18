# Frontend-Backend Integration Guide

## Overview

The MicroCFO frontend (React/Vite) is now connected to the FastAPI backend (`integration_server.py`) for real-time invoice processing and AI-powered financial operations.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  React Frontend │ ◄─────► │ FastAPI Backend  │ ◄─────► │  MCP Server │
│   (Vite/Axios)  │  REST   │ (integration_    │   MCP   │  (server.py)│
│                 │  + WS   │   server.py)     │ Bridge  │             │
└─────────────────┘         └──────────────────┘         └─────────────┘
```

## Key Changes Made

### 1. Frontend API Service (`frontend/src/services/api.js`)
- ✅ Already configured with proper endpoints
- ✅ Supports all 4 agents (Visual Auditor, Legal Sentinel, Subsidy Hunter, Negotiator)
- ✅ WebSocket manager for real-time updates
- ✅ Async task polling for long-running operations
- ✅ Authentication with JWT tokens

### 2. Chat Component (`frontend/src/pages/Chat.jsx`)
- ✅ Integrated real API calls instead of mock timeouts
- ✅ File upload handling with validation
- ✅ Real-time invoice processing feedback
- ✅ Action cards for next steps
- ✅ Error handling and user feedback

### 3. Input Bar (`frontend/src/components/Chat/InputBar.jsx`)
- ✅ File upload button with file picker
- ✅ File validation (PDF, PNG, JPG, max 50MB)
- ✅ File preview before upload
- ✅ Processing state indicators
- ✅ Disabled state during processing

### 4. Action Card (`frontend/src/components/Chat/ActionCard.jsx`)
- ✅ Dynamic action buttons
- ✅ Multiple card types (success, warning, info)
- ✅ Click handlers for follow-up actions
- ✅ Flexible data structure

## API Endpoints Used

### Visual Auditor (Agent A)
```javascript
// Upload and process invoice
POST /api/v1/agents/visual-auditor/upload-document
- Multipart form data with file
- Returns invoice data with line items, totals, compliance flags

// Scan invoice from URL/base64
POST /api/v1/agents/visual-auditor/scan-invoice
- JSON body with image_url or use_mock flag
```

### Legal Sentinel (Agent B)
```javascript
POST /api/v1/agents/legal-sentinel/search
POST /api/v1/agents/legal-sentinel/assess-risk
```

### Subsidy Hunter (Agent C)
```javascript
POST /api/v1/agents/subsidy-hunter/search
POST /api/v1/agents/subsidy-hunter/find-for-invoice
```

### Negotiator (Agent D)
```javascript
POST /api/v1/agents/negotiator/generate-email
```

## Setup Instructions

### 1. Backend Setup

```bash
# Start the FastAPI integration server
python integration_server.py

# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Create environment file
cp .env.example .env.development

# Start development server
npm run dev

# Frontend runs on http://localhost:5173
```

### 3. Environment Configuration

Edit `frontend/.env.development`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

For production:
```env
VITE_API_BASE_URL=https://your-production-api.com
```

## Testing the Integration

### 1. Test File Upload

1. Open the frontend at `http://localhost:5173`
2. Navigate to the Chat page
3. Click the paperclip icon or camera icon
4. Select an invoice file (PDF, PNG, or JPG)
5. Click Send to upload

**Expected Result:**
- File uploads to `/api/v1/agents/visual-auditor/upload-document`
- Backend processes with Agent A (Visual Auditor)
- Chat displays invoice details (vendor, date, total, tax, line items)
- Action card appears with next steps

### 2. Test API Directly

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API status
curl http://localhost:8000/api/v1/status

# Test file upload
curl -X POST http://localhost:8000/api/v1/agents/visual-auditor/upload-document \
  -F "file=@sample_invoice.png" \
  -F "process_immediately=true"
```

### 3. Test with Mock Data

```javascript
// In browser console
const response = await fetch('http://localhost:8000/api/v1/agents/visual-auditor/scan-invoice', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ use_mock: true })
});
const data = await response.json();
console.log(data);
```

## File Upload Flow

```
User selects file
      ↓
Frontend validates (type, size)
      ↓
FormData created with file
      ↓
POST to /upload-document
      ↓
Backend validates file
      ↓
File saved with UUID
      ↓
MCP Bridge calls Agent A
      ↓
Invoice data extracted
      ↓
Response sent to frontend
      ↓
Chat displays results
      ↓
Temp file cleaned up
```

## Error Handling

### Frontend
- File type validation (PDF, PNG, JPG only)
- File size validation (max 50MB)
- Network error handling
- User-friendly error messages

### Backend
- File validation (magic bytes, structure)
- Size limits enforced
- Secure file storage with UUID
- Automatic cleanup of temp files
- Comprehensive error logging

## WebSocket Support (Optional)

For real-time progress updates:

```javascript
import { WebSocketManager } from './services/api';

const wsManager = new WebSocketManager();
wsManager.connect(userId);

wsManager.on('task_progress', (data) => {
  console.log('Progress:', data.progress, data.message);
});

wsManager.on('task_complete', (data) => {
  console.log('Complete:', data.result);
});
```

## CORS Configuration

Backend CORS is configured in `config.py`:
```python
cors:
  allowed_origins:
    - http://localhost:5173  # Vite dev server
    - http://localhost:3000  # Alternative port
  allow_credentials: true
  allow_methods: ["*"]
  allow_headers: ["*"]
```

## Security Considerations

1. **File Upload Security**
   - File type validation (extension + MIME type + magic bytes)
   - Size limits enforced
   - Secure UUID filenames
   - Temporary storage with cleanup

2. **Authentication**
   - JWT tokens stored in localStorage
   - Automatic token inclusion in requests
   - Token refresh handling

3. **Rate Limiting**
   - Backend rate limiting middleware
   - Per-user request limits

## Troubleshooting

### Issue: CORS errors
**Solution:** Ensure backend is running and CORS origins include frontend URL

### Issue: File upload fails
**Solution:** 
- Check file type (PDF, PNG, JPG only)
- Check file size (max 50MB)
- Verify backend is running
- Check backend logs for errors

### Issue: API returns 404
**Solution:**
- Verify backend is running on port 8000
- Check VITE_API_BASE_URL in .env file
- Ensure API endpoints match

### Issue: No response from backend
**Solution:**
- Check backend logs: `python integration_server.py`
- Verify network connectivity
- Check browser console for errors

## Next Steps

1. **Implement remaining agents:**
   - Legal Sentinel integration
   - Subsidy Hunter integration
   - Negotiator integration

2. **Add WebSocket support:**
   - Real-time progress updates
   - Live notifications

3. **Enhance UI:**
   - Loading states
   - Progress bars
   - Better error messages

4. **Add authentication:**
   - Login/register flow
   - Protected routes
   - User profile management

## Development Tips

- Use browser DevTools Network tab to inspect API calls
- Check backend logs for detailed error messages
- Use `/docs` endpoint for API documentation
- Test with mock data first (`use_mock: true`)
- Monitor WebSocket connections in DevTools

## Production Deployment

1. Build frontend:
```bash
cd frontend
npm run build
```

2. Update environment:
```env
VITE_API_BASE_URL=https://api.microcfo.com
```

3. Deploy backend with proper CORS origins
4. Serve frontend build from CDN or static hosting
5. Configure SSL/TLS for both frontend and backend

## Support

For issues or questions:
- Check backend logs: `logs/microcfo.log`
- Check frontend console for errors
- Review API documentation: `http://localhost:8000/docs`
- Test endpoints with curl or Postman

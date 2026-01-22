# Async Task Queue Implementation Guide

## 🎯 What Problem Does This Solve?

### The Problem
When a user uploads an invoice for scanning, the AI processing takes 10-15 seconds. During this time:
- ❌ The HTTP request is blocked, waiting for response
- ❌ The server can't handle other requests efficiently
- ❌ User's browser shows "loading..." with no progress updates
- ❌ If the connection drops, the work is lost
- ❌ Timeouts can occur on slow operations

### The Solution: Async Task Queues
Instead of processing immediately, we:
1. ✅ Accept the request and return a **Task ID** instantly (< 100ms)
2. ✅ Queue the work for background processing
3. ✅ User polls for status or receives WebSocket updates
4. ✅ Show real-time progress (10%, 50%, 90%, 100%)
5. ✅ Retrieve results when ready

## 🏗️ Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │────────▶│  FastAPI     │────────▶│   Redis     │
│   (React)   │         │  Server      │         │   Broker    │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                         │
      │                        │                         ▼
      │                        │                  ┌─────────────┐
      │                        │                  │   Celery    │
      │                        │                  │   Workers   │
      │                        │                  └─────────────┘
      │                        │                         │
      │                        │                         ▼
      │                        │                  ┌─────────────┐
      │                        │                  │  MCP Bridge │
      │                        │                  │  (AI Tasks) │
      │                        │                  └─────────────┘
      │                        │                         │
      └────────────────────────┴─────────────────────────┘
              Poll for status / Get results
```

## 📦 Components

### 1. **Redis** - Message Broker & Result Backend
- Stores task queue (pending tasks)
- Stores task results (completed/failed)
- Acts as communication layer between API and workers

### 2. **Celery** - Task Queue Framework
- Manages task distribution to workers
- Handles retries, timeouts, and failures
- Provides task status tracking
- Supports periodic tasks (Celery Beat)

### 3. **Celery Workers** - Background Processors
- Execute heavy AI operations
- Run independently from web server
- Can scale horizontally (add more workers)
- Process tasks from specific queues

### 4. **Flower** - Monitoring Dashboard
- Web UI to monitor tasks
- View queue statistics
- Track worker health
- Debug failed tasks

## 🚀 How It Works

### Example: Invoice Scanning Flow

#### Step 1: User Uploads Invoice
```javascript
// Frontend
const response = await fetch('/api/tasks/invoice/scan', {
  method: 'POST',
  body: formData
});

const { task_id } = await response.json();
// Returns immediately: { task_id: "abc-123", status: "submitted" }
```

#### Step 2: Server Queues Task
```python
# Backend (routers/tasks.py)
task = scan_invoice_async.apply_async(
    args=[file_path, user_id],
    task_id=file_id
)
return {"task_id": task.id, "status": "submitted"}
```

#### Step 3: Worker Processes Task
```python
# Worker (tasks/visual_auditor_tasks.py)
@celery_app.task(bind=True)
def scan_invoice_async(self, file_path, user_id):
    # Update progress: 10%
    self.update_state(state='PROCESSING', meta={'progress': 10})
    
    # Call AI model
    result = bridge.call_tool('scan_invoice_document', {...})
    
    # Update progress: 90%
    self.update_state(state='PROCESSING', meta={'progress': 90})
    
    return {'status': 'success', 'invoice': result}
```

#### Step 4: Frontend Polls for Status
```javascript
// Poll every 2 seconds
const pollStatus = async (taskId) => {
  const response = await fetch(`/api/tasks/status/${taskId}`);
  const { status, progress, result } = await response.json();
  
  if (status === 'processing') {
    updateProgressBar(progress); // Show 10%, 50%, 90%
    setTimeout(() => pollStatus(taskId), 2000);
  } else if (status === 'success') {
    displayResult(result);
  }
};
```

#### Step 5: Retrieve Final Result
```javascript
// When status is 'success'
const response = await fetch(`/api/tasks/result/${taskId}`);
const { result } = await response.json();
// Display invoice data to user
```

## 📋 Task Queues

We use separate queues for different agent types:

| Queue Name | Purpose | Priority | Workers |
|------------|---------|----------|---------|
| `visual_auditor` | Invoice scanning (Agent A) | High | 2-4 |
| `legal_sentinel` | Legal compliance search (Agent B) | Medium | 2-3 |
| `subsidy_hunter` | Subsidy search (Agent C) | Medium | 1-2 |
| `negotiator` | Email generation (Agent D) | Low | 1-2 |
| `default` | Miscellaneous tasks | Low | 1 |

## 🔧 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

New dependencies added:
- `celery[redis]` - Task queue framework
- `redis` - Python Redis client
- `flower` - Monitoring dashboard
- `kombu` - Messaging library

### 2. Start Redis Server
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# Mac: brew install redis
```

### 3. Start Celery Workers
```bash
# Start worker for all queues
celery -A celery_app worker --loglevel=info

# Start worker for specific queue
celery -A celery_app worker -Q visual_auditor --loglevel=info

# Start multiple workers (production)
celery -A celery_app worker -Q visual_auditor --concurrency=4 --loglevel=info
```

### 4. Start Celery Beat (Periodic Tasks)
```bash
# For scheduled tasks (legal monitoring every 6 hours)
celery -A celery_app beat --loglevel=info
```

### 5. Start Flower Monitoring
```bash
# Web dashboard at http://localhost:5555
celery -A celery_app flower --port=5555
```

### 6. Start FastAPI Server
```bash
uvicorn integration_server:app --reload
```

## 🐳 Docker Compose Configuration

Add to `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  celery_worker:
    build: .
    command: celery -A celery_app worker --loglevel=info --concurrency=4
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/microcfo
    volumes:
      - ./temp_uploads:/app/temp_uploads

  celery_beat:
    build: .
    command: celery -A celery_app beat --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

  flower:
    build: .
    command: celery -A celery_app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - celery_worker
    environment:
      - REDIS_URL=redis://redis:6379/0

volumes:
  redis_data:
```

## 📊 API Endpoints

### Submit Tasks

#### POST `/api/tasks/invoice/scan`
Upload invoice for async scanning
```json
// Request: multipart/form-data with file
// Response:
{
  "task_id": "abc-123-def-456",
  "status": "submitted",
  "message": "Invoice scan submitted for processing",
  "submitted_at": "2026-01-18T10:30:00Z"
}
```

#### POST `/api/tasks/legal/search`
Submit legal compliance search
```json
// Request:
{
  "query": "GST compliance for textile exports",
  "user_profile": {
    "turnover": 8000000,
    "sector": "Textile"
  }
}

// Response:
{
  "task_id": "xyz-789",
  "status": "submitted",
  "message": "Legal search submitted for processing"
}
```

### Check Status

#### GET `/api/tasks/status/{task_id}`
Poll for task status and progress
```json
// Response (Processing):
{
  "task_id": "abc-123",
  "status": "processing",
  "progress": 45,
  "meta": {
    "status": "Extracting text from document...",
    "progress": 45
  }
}

// Response (Success):
{
  "task_id": "abc-123",
  "status": "success",
  "progress": 100,
  "result": {
    "status": "success",
    "invoice": { /* invoice data */ }
  }
}

// Response (Failed):
{
  "task_id": "abc-123",
  "status": "failed",
  "error": "Failed to process image: Invalid format"
}
```

### Get Results

#### GET `/api/tasks/result/{task_id}`
Retrieve completed task result
```json
// Response:
{
  "task_id": "abc-123",
  "status": "success",
  "result": {
    "invoice": {
      "invoice_number": "INV-2024-001",
      "vendor_name": "ABC Suppliers",
      "total_amount": 50000.00,
      // ... more fields
    }
  }
}
```

### Cancel Task

#### DELETE `/api/tasks/cancel/{task_id}`
Cancel a running task
```json
// Response:
{
  "task_id": "abc-123",
  "status": "cancelled",
  "message": "Task cancellation requested"
}
```

### Queue Statistics

#### GET `/api/tasks/queue/stats`
Get queue and worker statistics (admin)
```json
// Response:
{
  "active_tasks": {
    "worker1": [/* active tasks */]
  },
  "scheduled_tasks": {/* scheduled tasks */},
  "reserved_tasks": {/* reserved tasks */}
}
```

## 🎨 Frontend Integration

### React Hook for Task Polling

```javascript
import { useState, useEffect } from 'react';

export const useTaskStatus = (taskId) => {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!taskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/tasks/status/${taskId}`);
        const data = await response.json();

        setStatus(data.status);
        setProgress(data.progress || 0);

        if (data.status === 'success') {
          setResult(data.result);
          clearInterval(pollInterval);
        } else if (data.status === 'failed') {
          setError(data.error);
          clearInterval(pollInterval);
        }
      } catch (err) {
        setError(err.message);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [taskId]);

  return { status, progress, result, error };
};
```

### Usage Example

```javascript
function InvoiceUpload() {
  const [taskId, setTaskId] = useState(null);
  const { status, progress, result, error } = useTaskStatus(taskId);

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/tasks/invoice/scan', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    setTaskId(data.task_id);
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
      
      {status === 'processing' && (
        <ProgressBar value={progress} label={`Processing: ${progress}%`} />
      )}
      
      {status === 'success' && (
        <InvoiceDisplay data={result.invoice} />
      )}
      
      {status === 'failed' && (
        <ErrorMessage error={error} />
      )}
    </div>
  );
}
```

## 🔍 Monitoring with Flower

Access Flower dashboard at `http://localhost:5555`:

- **Tasks**: View all tasks (pending, active, completed, failed)
- **Workers**: Monitor worker health and performance
- **Broker**: Check Redis connection and queue sizes
- **Monitor**: Real-time task execution graphs

## ⚡ Performance Benefits

### Before (Synchronous)
- Request time: 10-15 seconds
- Concurrent requests: Limited by server threads
- User experience: Blocking, no progress updates
- Failure handling: Lost work on timeout

### After (Asynchronous)
- Request time: < 100ms (instant response)
- Concurrent requests: Unlimited (queued)
- User experience: Non-blocking with progress
- Failure handling: Automatic retries, persistent queue

## 🎯 Best Practices

1. **Task Timeouts**: Set reasonable time limits (5 minutes)
2. **Retry Logic**: Retry failed tasks with exponential backoff
3. **Result Expiration**: Clean up old results (1 hour default)
4. **Queue Separation**: Use dedicated queues for different priorities
5. **Worker Scaling**: Add more workers for high-load queues
6. **Monitoring**: Use Flower to track performance
7. **Error Handling**: Log failures and notify users
8. **Progress Updates**: Update task state for better UX

## 🐛 Troubleshooting

### Redis Connection Failed
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check Redis connection
redis-cli -h localhost -p 6379
```

### Worker Not Processing Tasks
```bash
# Check worker logs
celery -A celery_app worker --loglevel=debug

# Inspect active workers
celery -A celery_app inspect active
```

### Tasks Stuck in Pending
```bash
# Check queue size
redis-cli LLEN celery

# Purge queue (careful!)
celery -A celery_app purge
```

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

## 🎓 Summary

Async task queues transform your application from:
- ❌ Slow, blocking operations
- ❌ Poor user experience
- ❌ Limited scalability

To:
- ✅ Fast, responsive API
- ✅ Real-time progress updates
- ✅ Horizontal scalability
- ✅ Robust error handling
- ✅ Professional user experience

Your users get instant feedback, and your system can handle hundreds of concurrent AI operations efficiently!

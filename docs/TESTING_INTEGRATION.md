# Testing Frontend-Backend Integration

## Quick Start

### Option 1: Using Startup Scripts (Recommended)

**Windows PowerShell:**
```powershell
.\start-dev.ps1
```

**Windows CMD:**
```cmd
start-dev.bat
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
python integration_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Test Checklist

### ✅ 1. Backend Health Check

Open browser and visit:
- http://localhost:8000/health
- http://localhost:8000/api/v1/status

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "MicroCFO Integration Server is running",
  "version": "1.0.0",
  "environment": "development"
}
```

### ✅ 2. Frontend Loading

Open browser and visit:
- http://localhost:5173

**Expected:**
- Login page or Chat interface loads
- No console errors
- Tailwind CSS styles applied

### ✅ 3. File Upload Test

1. Navigate to Chat page
2. Click paperclip icon (📎)
3. Select a test invoice file:
   - Use `sample_invoice.png` or `test_invoice.png` from project root
   - Or any PDF/PNG/JPG invoice
4. Click Send button

**Expected Behavior:**
- File preview appears
- "Processing your invoice..." message shows
- After 2-5 seconds, invoice details appear:
  - Vendor name
  - Invoice date
  - Total amount
  - Tax amount
  - Line items
- Action card appears with next steps

**Check Backend Logs:**
```
INFO: Processing file upload: invoice.png (image/png)
INFO: File saved: <uuid>.png (12345 bytes)
INFO: File <uuid> processed successfully
```

### ✅ 4. API Direct Test (Using curl)

**Test Mock Invoice Scan:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/visual-auditor/scan-invoice \
  -H "Content-Type: application/json" \
  -d "{\"use_mock\": true}"
```

**Expected Response:**
```json
{
  "vendor_name": "Acme Corp",
  "invoice_date": "2024-01-15",
  "total_amount": 15000.0,
  "tax_amount": 2700.0,
  "line_items": [...]
}
```

**Test File Upload:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/visual-auditor/upload-document \
  -F "file=@sample_invoice.png" \
  -F "process_immediately=true"
```

### ✅ 5. Browser Console Test

Open browser console (F12) and run:

```javascript
// Test API connection
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log);

// Test mock invoice scan
fetch('http://localhost:8000/api/v1/agents/visual-auditor/scan-invoice', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ use_mock: true })
})
  .then(r => r.json())
  .then(console.log);
```

### ✅ 6. Network Tab Inspection

1. Open DevTools (F12)
2. Go to Network tab
3. Upload a file in the Chat interface
4. Look for request to `/upload-document`

**Expected:**
- Status: 200 OK
- Method: POST
- Type: multipart/form-data
- Response contains invoice_data object

### ✅ 7. Error Handling Test

**Test 1: Invalid File Type**
1. Try uploading a .txt or .docx file
2. Expected: "Please upload a PDF, PNG, or JPG file" alert

**Test 2: Large File**
1. Try uploading a file > 50MB
2. Expected: "File size must be less than 50MB" alert

**Test 3: Backend Offline**
1. Stop backend server
2. Try uploading a file
3. Expected: Error message in chat

## Common Issues & Solutions

### Issue: CORS Error
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Solution:**
- Ensure backend is running
- Check `config.py` has `http://localhost:5173` in allowed_origins
- Restart backend server

### Issue: 404 Not Found
```
POST http://localhost:8000/api/v1/agents/visual-auditor/upload-document 404
```

**Solution:**
- Verify backend is running on port 8000
- Check endpoint URL in `frontend/src/services/api.js`
- Verify router is registered in `integration_server.py`

### Issue: File Upload Hangs
**Solution:**
- Check backend logs for errors
- Verify file size is under 50MB
- Check temp_uploads directory permissions
- Ensure MCP bridge is initialized

### Issue: No Response Data
**Solution:**
- Check backend logs for processing errors
- Verify MCP server (server.py) is accessible
- Test with mock data first: `use_mock: true`

### Issue: Frontend Won't Start
```
Error: Cannot find module 'react'
```

**Solution:**
```bash
cd frontend
npm install
npm run dev
```

## Performance Testing

### Test Large File Upload
```bash
# Create a large test file (10MB)
python -c "open('large_test.pdf', 'wb').write(b'0' * 10485760)"

# Upload it
curl -X POST http://localhost:8000/api/v1/agents/visual-auditor/upload-document \
  -F "file=@large_test.pdf" \
  -F "process_immediately=false"
```

**Expected:**
- Upload completes within 5-10 seconds
- File saved successfully
- No memory issues

### Test Concurrent Uploads
Open multiple browser tabs and upload files simultaneously.

**Expected:**
- All uploads process successfully
- No race conditions
- Proper error handling

## Integration Test Script

Create `test_integration.py`:

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    print("✅ Health check passed")

def test_mock_scan():
    r = requests.post(
        f"{BASE_URL}/api/v1/agents/visual-auditor/scan-invoice",
        json={"use_mock": True}
    )
    assert r.status_code == 200
    data = r.json()
    assert "vendor_name" in data
    print("✅ Mock scan passed")

def test_file_upload():
    with open("sample_invoice.png", "rb") as f:
        files = {"file": f}
        data = {"process_immediately": "true"}
        r = requests.post(
            f"{BASE_URL}/api/v1/agents/visual-auditor/upload-document",
            files=files,
            data=data
        )
    assert r.status_code == 200
    result = r.json()
    assert result["success"] == True
    print("✅ File upload passed")

if __name__ == "__main__":
    print("Running integration tests...")
    test_health()
    test_mock_scan()
    test_file_upload()
    print("\n🎉 All tests passed!")
```

Run with:
```bash
python test_integration.py
```

## Monitoring

### Backend Logs
```bash
# View live logs
tail -f logs/microcfo.log

# View error logs
tail -f logs/errors.log

# View audit logs
tail -f logs/audit.log
```

### Frontend Console
- Open DevTools (F12)
- Check Console tab for errors
- Check Network tab for API calls
- Check Application tab for localStorage

## Success Criteria

✅ Backend starts without errors
✅ Frontend starts without errors
✅ Health endpoint returns 200
✅ File upload works end-to-end
✅ Invoice data displays correctly
✅ Action cards appear
✅ Error handling works
✅ No CORS errors
✅ No console errors
✅ Proper loading states

## Next Steps After Testing

1. **Test Other Agents:**
   - Legal Sentinel
   - Subsidy Hunter
   - Negotiator

2. **Add Authentication:**
   - Test login flow
   - Test protected routes
   - Test token refresh

3. **Test WebSocket:**
   - Real-time updates
   - Progress notifications
   - Connection handling

4. **Performance Testing:**
   - Load testing
   - Stress testing
   - Memory profiling

## Support

If tests fail:
1. Check both backend and frontend logs
2. Verify all dependencies are installed
3. Ensure ports 8000 and 5173 are available
4. Review FRONTEND_INTEGRATION.md for detailed setup
5. Check GitHub issues or create a new one

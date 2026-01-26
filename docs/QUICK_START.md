# 🚀 Quick Start Guide - Frontend-Backend Integration

## Start Servers (Choose One)

### Windows PowerShell
```powershell
.\start-dev.ps1
```

### Windows CMD
```cmd
start-dev.bat
```

### Manual (Any OS)
```bash
# Terminal 1 - Backend
python integration_server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Access Points

- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Test Upload

1. Open http://localhost:5173
2. Go to Chat page
3. Click 📎 (paperclip icon)
4. Select invoice file (PDF/PNG/JPG)
5. Click Send ✨

## Expected Result

```
✅ Invoice processed successfully!

Vendor: Acme Corp
Date: 2024-01-15
Total: ₹15,000
Tax: ₹2,700
Items: 3

[Action Card: What would you like to do next?]
```

## Quick Tests

### Test Backend Health
```bash
curl http://localhost:8000/health
```

### Test Mock Invoice
```bash
curl -X POST http://localhost:8000/api/v1/agents/visual-auditor/scan-invoice \
  -H "Content-Type: application/json" \
  -d '{"use_mock": true}'
```

### Test File Upload
```bash
curl -X POST http://localhost:8000/api/v1/agents/visual-auditor/upload-document \
  -F "file=@sample_invoice.png" \
  -F "process_immediately=true"
```

## Troubleshooting

### CORS Error
- Ensure backend is running
- Check `config.py` has `http://localhost:5173` in allowed_origins

### 404 Error
- Verify backend is on port 8000
- Check endpoint URLs in `frontend/src/services/api.js`

### File Upload Fails
- Check file type (PDF, PNG, JPG only)
- Check file size (max 50MB)
- Check backend logs: `logs/microcfo.log`

## Documentation

- **INTEGRATION_SUMMARY.md** - Quick overview
- **FRONTEND_INTEGRATION.md** - Detailed guide
- **TESTING_INTEGRATION.md** - Testing procedures

## What's Connected

✅ File upload with validation
✅ Invoice processing via Agent A
✅ Real-time feedback
✅ Error handling
✅ Action cards

## What's Next

⏳ Legal Sentinel integration
⏳ Subsidy Hunter integration
⏳ Negotiator integration
⏳ WebSocket real-time updates

---

**Need help?** Check the logs:
- Backend: `logs/microcfo.log`
- Frontend: Browser console (F12)

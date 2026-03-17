# MicroCFO Setup Guide - Complete Product Wiring

## 🎯 Current Status: P0 Priorities COMPLETED

### ✅ Completed Tasks

1. **P0: Real Authentication** - Login/Register → JWT → Frontend State
   - Created `/api/v1/auth/login` and `/api/v1/auth/register` endpoints
   - Frontend Login page connected to real API
   - JWT token stored in localStorage
   - User context injected into all protected routes
   - Sidebar shows real user data

2. **P0: Dashboard Connected to Real API**
   - Created `/api/v1/dashboard/summary` endpoint
   - Dashboard fetches real metrics, invoices, alerts, subsidies
   - Graceful fallback to mock data if API unavailable

3. **P0: Environment Configuration**
   - Created `.env` file with all required API keys
   - Documented how to get Gemini API key

---

## 🚀 Quick Start Guide

### Step 1: Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Step 2: Setup Database

```bash
# PostgreSQL (Recommended for production)
# Create database and user
psql -U postgres
CREATE DATABASE microcfo;
CREATE USER microcfo WITH PASSWORD 'changeme';
GRANT ALL PRIVILEGES ON DATABASE microcfo TO microcfo;
\q

# Initialize tables
python -c "from src.database import init_db; init_db()"
```

### Step 3: Configure Environment Variables

1. **Edit `.env` file** (already created in project root)

2. **Get your Gemini API Key** (REQUIRED for AI agents):
   - Visit: https://makersuite.google.com/app/apikey
   - Create API key
   - Add to `.env`:
   ```
   GEMINI_API_KEY=your-actual-key-here
   ```

3. **Update other settings** (optional):
   ```
   SECRET_KEY=generate-a-random-32-char-string-here
   DATABASE_URL=postgresql://microcfo:changeme@localhost:5432/microcfo
   ENCRYPTION_KEY=another-random-32-char-string
   ```

### Step 4: Run Legal Document Ingestion (Populate ChromaDB)

```bash
# Ensure you have legal PDFs in data/initial_acts directory
# Run ingestion script
python scripts/ingest_legal_documents.py

# Verify ingestion
python scripts/ingest_legal_documents.py --verify-only
```

**Expected Output:**
```
📚 Legal Document Ingestion Starting
   Documents directory: data/initial_acts
   Vector database: legal_db
📄 Processing: CGST_Act_2017.pdf
   ✅ Extracted 245 chunks
   ✅ Added to vector database
...
📊 INGESTION SUMMARY
   Total documents: 16
   Successfully processed: 16
   Total chunks in DB: 3,450
```

### Step 5: Start the Application

```bash
# Terminal 1: Backend
python main.py
# Backend runs on http://localhost:8000

# Terminal 2: Frontend
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

### Step 6: Test Authentication

1. Visit http://localhost:5173/login
2. **Register a new account**:
   - Email: `test@example.com`
   - Password: `test1234` (min 8 chars)
   - Full Name: `Test User`
   - Company: `Test Corp Pvt Ltd`
3. Click "Create Account"
4. You'll be redirected to Dashboard

---

## 📋 Testing All Agents

### Agent A: Visual Auditor (Invoice Scanner)

```bash
curl -X POST http://localhost:8000/api/v1/invoices/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/invoice.pdf"
```

### Agent B: Legal Sentinel (Compliance Query)

```bash
curl -X POST http://localhost:8000/api/v1/compliance/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the ITC eligibility criteria?"}'
```

### Agent C: Subsidy Hunter

```bash
curl -X POST http://localhost:8000/api/v1/subsidies/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sector": "Textile", "turnover_range": "5-20Cr"}'
```

### Agent D: Negotiator

```bash
curl -X POST http://localhost:8000/api/v1/negotiation/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vendor_name": "ABC Suppliers", "amount": 50000, "days_overdue": 30}'
```

---

## 🗂️ File Structure Overview

```
d:\CFO\
├── backend/
│   └── api/v1/routes/
│       ├── auth.py          # ✅ NEW: Authentication endpoints
│       ├── dashboard.py     # ✅ NEW: Dashboard metrics
│       ├── chat.py          # Chat/Orchestrator
│       ├── invoices.py      # Visual Auditor
│       ├── compliance.py    # Legal Sentinel
│       ├── subsidies.py     # Subsidy Hunter
│       └── negotiation.py   # Negotiator
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Login.jsx    # ✅ UPDATED: Real auth
│       │   └── Dashboard.jsx # ✅ UPDATED: Real API
│       ├── components/
│       │   └── Layout/
│       │       ├── MainLayout.jsx
│       │       └── Sidebar.jsx # ✅ UPDATED: User data
│       └── services/
│           └── api.js       # ✅ UPDATED: Auth endpoints
├── scripts/
│   ├── ingest_legal_documents.py  # ✅ Run this to populate ChromaDB
│   └── seed_data.py
├── src/
│   ├── models.py          # SQLAlchemy models
│   ├── auth.py            # JWT handling
│   └── legal_ingestion.py # PDF processing
├── .env                   # ✅ CREATED: Your API keys
└── main.py                # FastAPI app
```

---

## 🔧 Troubleshooting

### "Module not found" errors

```bash
# Ensure you're in project root
cd d:\CFO

# Add to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:d:\CFO
```

### Database connection errors

```bash
# Check PostgreSQL is running
pg_ctl status

# Verify .env DATABASE_URL
echo $DATABASE_URL
```

### Frontend can't connect to backend

```bash
# Check backend is running on port 8000
curl http://localhost:8000/api/v1/health

# Check frontend .env or vite.config.js
# VITE_API_URL should be http://localhost:8000
```

### Gemini API errors

```bash
# Verify API key is set
echo $GEMINI_API_KEY

# Test API key
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## 📊 Next Steps (Remaining Priorities)

### P1 Tasks (High Priority)

1. **User Profile API** - Add sector/turnover/state fields
   - Endpoint: `PUT /api/v1/auth/profile`
   - Already partially implemented

2. **Query History API** - Wire History page
   - Endpoint: `GET /api/v1/chat/conversations`
   - Needs DB implementation

3. **Alembic Migrations** - For PostgreSQL schema management
   ```bash
   alembic init alembic
   alembic revision --autogenerate -m "Initial"
   alembic upgrade head
   ```

4. **Seed Subsidy Database** - Real scheme data
   ```bash
   python scripts/seed_scheme_db.py
   ```

### P2 Tasks (Medium Priority)

1. **Add Basic Tests**
   ```bash
   pytest tests/
   ```

2. **Settings Page**
   - Connect to profile API
   - Add password change
   - Notification preferences

---

## 🎉 Success Criteria

You'll know everything is working when:

- ✅ Can register/login and see JWT in localStorage
- ✅ Dashboard shows real user data in sidebar
- ✅ Can query Legal Sentinel and get answers from ingested documents
- ✅ All 4 agents respond via API endpoints
- ✅ No mock data being used (except graceful fallbacks)

---

## 📞 Support

For issues or questions:
- Check `README.md` for detailed documentation
- Review `CODE_REVIEW_FIXES.md` for recent fixes
- Inspect browser console for frontend errors
- Check `logs/` directory for backend errors

---

**Last Updated**: March 17, 2026
**Status**: P0 Complete - Ready for Testing

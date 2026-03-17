# MicroCFO - Complete Setup Guide

AI-powered financial compliance platform for Indian MSMEs

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/)
- **Redis 7+** (optional) - [Download](https://redis.io/download/)

### 1. Clone and Setup

```bash
# Navigate to project directory
cd d:\CFO

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/Linux/Mac
source venv/bin/activate
```

### 2. Install Backend Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e .
```

### 3. Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install Node packages
npm install

# Return to root
cd ..
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required: GEMINI_API_KEY or OPENROUTER_API_KEY
# Optional: Database URLs, Redis, AWS, etc.
```

**Minimum required in `.env`:**
```env
SECRET_KEY=your-secret-key-min-32-characters-long
GEMINI_API_KEY=your-gemini-api-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/microcfo
```

### 5. Initialize Database

```bash
# Create PostgreSQL database
psql -U postgres
CREATE DATABASE microcfo;
\q

# Or use SQLite for development (no setup needed)
# Just update DATABASE_URL in .env:
# DATABASE_URL=sqlite:///./microcfo.db
```

### 6. Run the Application

#### Option A: Run Backend and Frontend Separately

**Terminal 1 - Backend:**
```bash
# Activate venv first
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix

# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

#### Option B: Use Docker (Recommended for Production)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### 7. Access the Application

- **Frontend:** http://localhost:5173 (dev) or http://localhost (prod)
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Redoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## 📁 Project Structure

```
microcfo/
├── backend/                 # Backend code
│   ├── agents/             # AI Agents (A, B, C, D)
│   ├── api/                # API routes
│   ├── app/                # App configuration
│   └── core/               # Core utilities
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utilities
│   └── public/             # Static assets
├── src/                    # Core backend modules
│   ├── models.py           # Database models
│   ├── database.py         # Database config
│   ├── auth.py             # Authentication
│   └── server.py           # MCP server
├── routers/                # API routers
├── legal_db/               # Legal vector database
├── scheme_db/              # Subsidy database
├── main.py                 # FastAPI entry point
├── docker-compose.yml      # Docker orchestration
└── requirements.txt        # Python dependencies
```

## 🔑 Key Features

### Agent A - Visual Auditor
- **Invoice Scanning:** Upload PNG/JPG/PDF invoices
- **Data Extraction:** Vendor, amounts, dates, GSTIN, line items
- **Fraud Detection:** Tampering, handwriting, inconsistencies
- **Compliance Check:** ITC eligibility, blocked credits
- **Auto-Triggers:** Subsidy alerts for capital goods >₹1L

### Agent B - Legal Sentinel
- **Structure-Aware RAG:** CA-logic based legal text chunking
- **Vector Database:** ChromaDB with semantic search
- **Context Filtering:** Turnover-based compliance filtering
- **Real-time Monitoring:** Government website scraping

### Agent C - Subsidy Hunter
- **Scheme Discovery:** 248+ government schemes database
- **Intelligent Matching:** Sector, CAPEX, state-based filtering
- **Eligibility Assessment:** Automatic benefit calculation
- **Application Tracking:** Status monitoring

### Agent D - Negotiator
- **Smart Intent Detection:** Credit extension, payment chase, early payment
- **A/B Testing:** Relationship vs transactional approaches
- **Multi-format:** Email + Telegram message generation
- **Cash Flow Intelligence:** Context-aware recommendations

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agent_a.py -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## 📚 API Documentation

### Key Endpoints

#### Chat
```bash
POST /api/v1/chat/message
{
  "message": "Can I claim ITC on office supplies?",
  "agent": "auto",
  "context": []
}
```

#### Invoice Analysis
```bash
POST /api/v1/invoices/analyze
Content-Type: multipart/form-data
file: <invoice_image>
```

#### Compliance Query
```bash
POST /api/v1/compliance/query
{
  "query": "What are blocked credits?",
  "user_context": {"turnover": "3 crore", "sector": "Manufacturing"}
}
```

#### Subsidy Search
```bash
POST /api/v1/subsidies/search
{
  "sector": "Textile",
  "capex": 1000000,
  "state": "Gujarat"
}
```

#### Negotiation Draft
```bash
POST /api/v1/negotiation/generate
{
  "invoice_data": {
    "vendor_name": "ABC Suppliers",
    "amount": 50000,
    "due_date": "2024-02-01"
  },
  "negotiation_context": "Need 15 days extension"
}
```

## 🔒 Security

### Best Practices Implemented

- ✅ AES-256 encryption for sensitive data
- ✅ JWT authentication with 24h expiry
- ✅ bcrypt password hashing (12 rounds)
- ✅ CORS with whitelist-only origins
- ✅ Rate limiting (100 req/min per user)
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS prevention (output encoding)
- ✅ HTTPS enforcement in production

### Environment Variables

**NEVER commit `.env` file to git!**

```bash
# Add to .gitignore
.env
.env.local
.env.production
```

## 🚀 Deployment

### Production Deployment with Docker

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Railway/Heroku Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Vercel (Frontend Only)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy frontend
cd frontend
vercel --prod
```

## 🛠 Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check PostgreSQL is running
pg_isready

# Verify DATABASE_URL in .env
# Ensure database exists
```

**2. Module Not Found**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**3. Port Already in Use**
```bash
# Kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Unix
lsof -ti:8000 | xargs kill -9
```

**4. Frontend Build Error**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**5. API Key Issues**
```bash
# Verify API key is set
echo $GEMINI_API_KEY

# Test API connection
python test_gemini_direct.py
```

## 📖 Additional Resources

- [Design Document](design.md) - System architecture
- [Requirements](requirements.md) - Functional requirements
- [API Documentation](docs/API.md) - Complete API reference
- [Security Guide](SECURITY.md) - Security best practices
- [Contributing](CONTRIBUTING.md) - Contribution guidelines

## 🤝 Support

- **Documentation:** https://microcfo.com/docs
- **Issues:** https://github.com/microcfo/microcfo/issues
- **Discussions:** https://github.com/microcfo/microcfo/discussions
- **Email:** support@microcfo.com

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for Indian MSMEs**

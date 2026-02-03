# MicroCFO - Technical Design Document

**Version**: 2.1.0  
**Last Updated**: February 3, 2026  
**Status**: ✅ Production Ready

---

## Table of Contents
1. [System Architecture](#1-system-architecture)
2. [Component Design](#2-component-design)
3. [Database Design](#3-database-design)
4. [API Design](#4-api-design)
5. [Security Architecture](#5-security-architecture)
6. [Technology Stack](#6-technology-stack)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   React UI   │  │  Disclaimer  │  │  File Upload │          │
│  │   (Vite)     │  │    Modal     │  │   Handler    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTPS/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Integration Server (FastAPI)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Middleware Stack                       │  │
│  │  • Authentication  • Authorization  • Rate Limiting       │  │
│  │  • Audit Logging   • Disclaimer     • Error Handling     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      API Routers                          │  │
│  │  • Visual Auditor  • Legal Sentinel  • Subsidy Hunter    │  │
│  │  • Negotiator      • ERP Export      • Onboarding        │  │
│  │  • Orchestrator (The Brain)                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Server (server.py)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Agent A    │  │   Agent B    │  │   Agent C    │          │
│  │   Visual     │  │    Legal     │  │   Subsidy    │          │
│  │   Auditor    │  │   Sentinel   │  │   Hunter     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐                                              │
│  │   Agent D    │                                              │
│  │  Negotiator  │                                              │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │   ChromaDB   │    │   AWS S3     │
│  (Encrypted) │    │   (Vector)   │    │ (Optional)   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 1.2 Architecture Layers

| Layer | Technology | Port | Responsibilities |
|-------|------------|------|------------------|
| Frontend | React 18 + Vite | 5173 | UI, file upload, WebSocket |
| API Gateway | FastAPI | 8000 | Routing, middleware, auth |
| Business Logic | FastMCP | - | AI agents, orchestration |
| Data | PostgreSQL, ChromaDB | 5432, - | Storage, vector search |

---

## 2. Component Design

### 2.1 Agent A - Visual Auditor

**Purpose**: Process invoice images to extract structured data and detect fraud.

```
Image Input → Gemini 2.5 Flash → Fraud Detection → Categorization → Orchestrator
```

**Data Model**:
```python
class Invoice(BaseModel):
    vendor_name: str
    invoice_date: str  # YYYY-MM-DD
    total_amount: float
    tax_amount: float
    line_items: List[LineItem]
    gstin: Optional[str]
    is_handwritten: bool
    tampering_detected: bool
    compliance_flags: List[str]
    confidence_score: float

class LineItem(BaseModel):
    description: str
    amount: float
    category: str  # Capital Goods | Raw Material | Personal | Service
```

**Categories**:
| Category | Examples | ITC Eligibility |
|----------|----------|-----------------|
| Capital Goods | Machinery, equipment, vehicles | Yes |
| Raw Material | Production inputs, components | Yes |
| Personal/Entertainment | Food, alcohol, personal items | No (Section 17(5)) |
| Service | Consulting, software, maintenance | Yes |

### 2.2 Agent B - Legislative Sentinel

**Purpose**: Structure-aware RAG for legal compliance with turnover filtering.

```
Query → Context Fetcher → Hybrid Search → Filter → Risk Assessment
```

**Vector Database**: ChromaDB with all-MiniLM-L6-v2 embeddings

**Metadata Fields**:
- `law_type`: GST, Income Tax, Companies Act
- `section_number`: For keyword search
- `turnover_threshold`: For filtering
- `sector_tag`: Industry-specific

### 2.3 Agent C - Subsidy Hunter

**Purpose**: Discover applicable government subsidies based on user profile.

**Scheme Database**: SQLite with government schemes (PLI, TUFS, MSME, etc.)

### 2.4 Agent D - Negotiator

**Purpose**: Generate professional negotiation content with A/B testing.

```
Financial Context → Router Logic → Vendor CRM → Gemini 3 Flash → Draft Output
```

**Intents**:
| Intent | Trigger | Strategy |
|--------|---------|----------|
| Credit Extension | Cash flow tight | Request more time |
| Payment Chase | Overdue receivables | Professional reminder |
| Early Payment | Cash surplus | Offer discount |

**⚠️ GUARDRAIL**: Draft-only mode - NEVER auto-send

### 2.5 Orchestrator (The Brain)

**Purpose**: Manage multi-step workflows across agents.

**Document Lifecycle**:
1. Visual Audit (Agent A)
2. State Persistence (WorkflowState)
3. Decision Logic (Check thresholds)
4. Negotiation (Agent D) if needed
5. Human Approval

---

## 3. Database Design

### 3.1 Entity Relationship

```
Users ──1:1── UserProfiles
  │
  │ 1:N
  ├── Invoices ──1:1── WorkflowStates
  ├── LegalQueries
  ├── SubsidyApplications
  ├── Negotiations
  └── AuditLogs

VendorProfiles (standalone, linked by vendor_name)
```

### 3.2 Key Tables

**users**: Authentication and basic info
**user_profiles**: Company details, industry, turnover tier
**invoices**: Processed invoice data (encrypted amounts)
**workflow_states**: Multi-step workflow tracking
**vendor_profiles**: Negotiation history and tactics
**audit_logs**: Comprehensive action logging

### 3.3 Encrypted Columns (AES-256)
- GSTIN, PAN
- Amounts (total, tax, taxable)
- Vendor names
- Addresses

---

## 4. API Design

### 4.1 Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/visual-auditor/process` | POST | Process invoice image |
| `/api/legal-sentinel/query` | POST | Query legal database |
| `/api/subsidy-hunter/discover` | POST | Find applicable subsidies |
| `/api/negotiator/generate` | POST | Generate negotiation draft |
| `/api/workflow/process-document` | POST | Full document lifecycle |
| `/api/erp/export/{format}` | POST | Export to ERP |
| `/api/onboarding/complete` | POST | Complete user onboarding |

### 4.2 Authentication
- JWT Bearer tokens
- Token expiry: 24 hours
- Refresh token support

### 4.3 Rate Limiting
- 100 requests/minute per user
- 10 concurrent invoice processing

---

## 5. Security Architecture

### 5.1 Data Protection

| Layer | Protection |
|-------|------------|
| Transit | HTTPS/TLS 1.3 |
| Rest (DB) | AES-256 Fernet |
| Rest (Files) | S3 SSE or local encryption |
| Passwords | bcrypt hashing |

### 5.2 Audit Trail

**Logged Actions** (30+ types):
- User authentication events
- Invoice processing
- Legal queries
- Negotiation drafts
- Export operations
- Admin actions

**Severity Levels**: INFO, WARNING, ERROR, CRITICAL

### 5.3 Guardrails

| Component | Guardrail |
|-----------|-----------|
| Negotiator | Draft-only, never auto-send |
| Invoice | Manual verification required |
| High Amount | Flag > ₹50,000 |
| Legal | Recommend professional consultation |

### 5.4 Disclaimers

**7 Disclaimer Types**:
1. General AI Assistant
2. Legal Advice
3. Financial Advice
4. Tax Advice
5. Negotiation
6. Invoice Processing
7. Subsidy Application

---

## 6. Technology Stack

### 6.1 Backend
| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python 3.7+) |
| MCP Server | FastMCP |
| Database | PostgreSQL |
| Vector DB | ChromaDB |
| Cache | Redis (optional) |
| Task Queue | Celery + Redis |

### 6.2 Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| State | React Query |

### 6.3 AI/ML
| Component | Technology |
|-----------|------------|
| Invoice Processing | Gemini 2.5 Flash |
| Content Generation | Gemini 3 Flash |
| Fallback | OpenRouter (GPT-4V) |
| Embeddings | all-MiniLM-L6-v2 |

### 6.4 Infrastructure
| Component | Technology |
|-----------|------------|
| File Storage | AWS S3 / Local |
| Deployment | Docker, Heroku |
| CI/CD | GitHub Actions |
| Monitoring | Structured logging |

---

## 7. Project Structure

```
CFO/
├── src/                    # Core application source
│   ├── server.py           # MCP Server entry point
│   ├── integration_server.py # FastAPI server
│   ├── models.py           # Database models
│   ├── database.py         # Database configuration
│   ├── encryption.py       # AES-256 encryption
│   └── ...                 # Other modules
├── routers/                # API route handlers
├── middleware/             # Auth, audit, rate limiting
├── tasks/                  # Celery background tasks
├── frontend/               # React application
├── tests/                  # Test suite
├── config/                 # Configuration files
├── data/                   # Data files and samples
├── scripts/                # Utility scripts
└── hackathon/              # Documentation
```

---

## 8. Deployment

### 8.1 Environment Variables

```env
# Database
DATABASE_URL=postgresql://...

# AI APIs
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...

# Storage
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=...

# Security
SECRET_KEY=...
ENCRYPTION_KEY=...
```

### 8.2 Quick Start

```bash
# Backend
pip install -r requirements.txt
python src/integration_server.py

# Frontend
cd frontend && npm install && npm run dev
```

---

## 9. Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Invoice Processing | < 30s | ✅ |
| Legal Query | < 5s | ✅ |
| API Response (P95) | < 2s | ✅ |
| Uptime | 99.5% | ✅ |

# MicroCFO - Design Document

## Document Information
- **Version**: 2.0.0
- **Last Updated**: January 20, 2026
- **Status**: Approved ✅
- **Authors**: MicroCFO Development Team

---

## Table of Contents
1. [System Architecture](#1-system-architecture)
2. [Component Design](#2-component-design)
3. [Database Design](#3-database-design)
4. [API Design](#4-api-design)
5. [Security Architecture](#5-security-architecture)
6. [Data Flow Diagrams](#6-data-flow-diagrams)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Technology Stack](#8-technology-stack)
9. [Design Patterns](#9-design-patterns)
10. [Performance Considerations](#10-performance-considerations)

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
                              │
                              │ HTTPS/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Integration Server                          │
│                        (FastAPI)                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Middleware Stack                       │  │
│  │  • Authentication  • Authorization  • Rate Limiting       │  │
│  │  • Audit Logging   • Disclaimer     • Error Handling     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      API Routers                          │  │
│  │  • Visual Auditor  • Legal Sentinel  • Subsidy Hunter    │  │
│  │  • Negotiator      • ERP Export      • Onboarding        │  │
│  │  • Audit Logs      • WebSocket       • Tasks             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Server                               │
│                      (server.py)                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Agent A    │  │   Agent B    │  │   Agent C    │          │
│  │    Visual    │  │    Legal     │  │   Subsidy    │          │
│  │   Auditor    │  │   Sentinel   │  │   Hunter     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │   Agent D    │  │ Orchestrator │                            │
│  │  Negotiator  │  │    Logic     │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │   ChromaDB   │    │   AWS S3     │
│   Database   │    │    Vector    │    │ File Storage │
│              │    │   Database   │    │  (Optional)  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Encrypted   │    │    Legal     │    │   Invoice    │
│    Data      │    │   Chunks     │    │    Images    │
│  (AES-256)   │    │  Embeddings  │    │  (Encrypted) │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 1.2 Architecture Layers

#### 1.2.1 Presentation Layer (Frontend)
- **Technology**: React 18 + Vite
- **Port**: 5173 (development)
- **Responsibilities**:
  - User interface rendering
  - Form validation and input handling
  - File upload management
  - Real-time WebSocket communication
  - Disclaimer modal display
  - Session management

#### 1.2.2 API Gateway Layer (Integration Server)
- **Technology**: FastAPI (Python 3.7+)
- **Port**: 8000
- **Responsibilities**:
  - HTTP request routing
  - Middleware orchestration
  - Authentication and authorization
  - Rate limiting and throttling
  - Audit trail logging
  - Error handling and response formatting
  - WebSocket connection management

#### 1.2.3 Business Logic Layer (MCP Server)
- **Technology**: FastMCP (Model Context Protocol)
- **Responsibilities**:
  - AI agent orchestration
  - Invoice processing (Agent A)
  - Legal compliance checking (Agent B)
  - Subsidy discovery (Agent C)
  - Negotiation content generation (Agent D)
  - Inter-agent communication

#### 1.2.4 Data Layer
- **PostgreSQL**: Structured data storage with encryption
- **ChromaDB**: Vector embeddings for semantic search
- **AWS S3**: File storage with server-side encryption
- **Local Storage**: Fallback for S3 unavailability

### 1.3 Communication Protocols

#### 1.3.1 Frontend ↔ Integration Server
- **Protocol**: HTTPS/REST API
- **Format**: JSON
- **Authentication**: JWT Bearer tokens
- **CORS**: Configured for localhost:5173

#### 1.3.2 Integration Server ↔ MCP Server
- **Protocol**: Model Context Protocol (MCP)
- **Format**: JSON-RPC
- **Communication**: Synchronous tool calls

#### 1.3.3 Real-time Communication
- **Protocol**: WebSocket (WSS)
- **Use Cases**:
  - Legal notification alerts
  - Long-running task progress
  - System status updates
  - Heartbeat monitoring


---

## 2. Component Design

### 2.1 Agent A - Visual Auditor

#### 2.1.1 Purpose
Process invoice images using Gemini 2.5 Flash to extract structured data, detect fraud, and check compliance.

#### 2.1.2 Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Visual Auditor                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Image      │  │   Gemini     │  │   Fraud      │ │
│  │   Loader     │→ │   2.5 Flash  │→ │  Detection   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                              │          │
│                                              ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Orchestrator │← │  Compliance  │← │  Category    │ │
│  │   Trigger    │  │   Checker    │  │  Classifier  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 2.1.3 Key Components

**Image Loader**
- Supports: URL, base64, local file path
- Formats: PDF, PNG, JPG, JPEG
- Max size: 50 MB
- Converts to PIL Image format

**Gemini Vision API**
- Model: gemini-2.5-flash
- Fallback: OpenRouter (GPT-4V)
- Timeout: 30 seconds
- Structured JSON output

**Fraud Detection**
- Tampering detection (font mismatches, blurred numbers)
- Handwritten bill identification
- Confidence scoring (0.0 to 1.0)
- Flags for manual review

**Category Classifier**
- Capital Goods (machinery, equipment)
- Raw Material (production inputs)
- Personal/Entertainment (non-deductible)
- Service (consulting, software)

**Compliance Checker**
- GSTIN validation
- ITC eligibility checking
- Invoice staleness (>30 days)
- Section 17(5) validation

**Orchestrator Trigger**
- Auto-triggers Agent C for capital goods > ₹1 Lakh
- Auto-triggers Agent B for personal items
- Adds alerts to invoice response

#### 2.1.4 Data Models
```python
class LineItem(BaseModel):
    description: str
    amount: float
    category: str  # Capital Goods, Raw Material, Personal/Entertainment, Service

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
```

#### 2.1.5 Processing Flow
1. Receive image (URL/base64/file)
2. Load and validate image format
3. Send to Gemini with auditor prompt
4. Parse JSON response
5. Apply Python-side validations
6. Trigger orchestrator logic
7. Return structured invoice data

### 2.2 Agent B - Legislative Sentinel

#### 2.2.1 Purpose
Structure-aware RAG system for legal compliance queries with turnover-based filtering.

#### 2.2.2 Architecture
```
┌─────────────────────────────────────────────────────────┐
│                  Legislative Sentinel                    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Query     │  │   Context    │  │   Vector     │ │
│  │   Parser     │→ │   Fetcher    │→ │   Search     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                              │          │
│                                              ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │     Risk     │← │   Context    │← │   Hybrid     │ │
│  │  Assessment  │  │   Filter     │  │   Search     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 2.2.3 Key Components

**Legal Document Processor**
- Structure-aware text splitting
- Recognizes: Section, Rule, Notification, Proviso
- Preserves parent-child relationships
- Metadata extraction (turnover, sector, dates)

**Vector Database (ChromaDB)**
- Embedding model: all-MiniLM-L6-v2
- Chunk size: Variable (structure-aware)
- Metadata fields: law_type, section_number, turnover_threshold, sector_tag
- Persistent storage: legal_db/

**Hybrid Search**
- Semantic search: Vector similarity
- Keyword search: Section numbers
- Combined scoring algorithm
- Top-k results: 5

**Context Filter**
- Turnover tier matching (< 5Cr, 5-20Cr, > 50Cr)
- Sector-specific filtering
- Exemption checking
- Relevance scoring

**Risk Assessment**
- Risk levels: LOW, MEDIUM, HIGH
- Keyword analysis (penalty, fine, blocked)
- Conservative CA-style interpretation
- Professional consultation recommendations

#### 2.2.4 Data Models
```python
class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class LegalRisk(BaseModel):
    risk_level: RiskLevel
    relevant_section: str
    compliant_action: str

class UserProfile(BaseModel):
    business_name: str
    turnover_tier: str  # < 5Cr, 5-20Cr, > 50Cr
    gst_registration_type: str
    industry_code: str
```

#### 2.2.5 Real-time Monitoring
**Legal Sentinel Monitor**
- Scheduled scraping: Daily
- Sources: CBIC, MCA, Income Tax Department
- Relevance checking: User profile matching
- Alert delivery: WhatsApp, Email, WebSocket
- Seen notifications tracking

### 2.3 Agent C - Subsidy Hunter

#### 2.3.1 Purpose
Discover applicable government subsidies based on sector, turnover, and capital expenditure.

#### 2.3.2 Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Subsidy Hunter                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Scheme     │  │   Profile    │  │   Scheme     │ │
│  │  Database    │→ │   Matcher    │→ │   Search     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                              │          │
│                                              ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Application │← │   Benefit    │← │ Eligibility  │ │
│  │   Guidance   │  │ Calculation  │  │   Checker    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 2.3.3 Key Components

**Scheme Database (ChromaDB)**
- Government schemes: PLI, TUFS, MSME, PMFME
- Eligibility criteria storage
- Application deadlines
- Benefit calculation formulas

**Profile Matcher**
- Industry-based filtering (12 industries)
- Turnover tier matching
- Location-based schemes
- Investment threshold checking

**Benefit Calculator**
- Percentage-based subsidies
- Fixed amount subsidies
- Conditional benefits
- Maximum cap enforcement

**Application Guidance**
- Required documents list
- Application process steps
- Deadline tracking
- Compliance requirements

#### 2.3.4 Supported Industries
1. Textile & Apparel
2. Manufacturing
3. Technology & IT
4. Trading & Distribution
5. Professional Services
6. Retail
7. Construction & Real Estate
8. Healthcare & Pharma
9. Education & Training
10. Hospitality & Tourism
11. Agriculture & Agri-business
12. Other

### 2.4 Agent D - Negotiator

#### 2.4.1 Purpose
Generate professional negotiation content (emails, WhatsApp) based on cash flow analysis.

#### 2.4.2 Architecture
```
┌─────────────────────────────────────────────────────────┐
│                      Negotiator                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Router     │  │   Strategy   │  │   Gemini     │ │
│  │   Logic      │→ │   Selector   │→ │  3 Flash     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                              │          │
│                                              ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Draft      │← │     A/B      │← │   Content    │ │
│  │   Storage    │  │   Testing    │  │  Generator   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 2.4.3 Key Components

**Router Logic**
- Cash flow analysis
- Intent determination
- Strategy selection
- Context evaluation

**Negotiation Intents**
1. **Credit Extension**: Cash flow tight, need payment delay
2. **Payment Chase**: Receivable overdue, need collection
3. **Early Payment Offer**: Cash surplus, offer discount

**Content Generator (Gemini 3 Flash)**
- Indian business communication style
- Invoice-specific references
- Tone variations (relationship vs transactional)
- WhatsApp (< 160 chars) and email formats

**A/B Testing**
- Option A: Relationship-focused, apologetic
- Option B: Transactional, direct
- Strategy explanation for each

**Draft-Only Mode (Guardrail)**
- NEVER auto-sends emails
- Always requires user approval
- Prominent disclaimer display
- Audit trail logging

#### 2.4.4 Data Models
```python
class NegotiationIntent(str, Enum):
    CREDIT_EXTENSION = "credit_extension"
    PAYMENT_CHASE = "payment_chase"
    EARLY_PAYMENT_OFFER = "early_payment_offer"

class NegotiationDraft(BaseModel):
    intent: NegotiationIntent
    strategy_explanation: str
    whatsapp_message: str
    formal_email: str
    option_a: str  # Relationship-focused
    option_b: str  # Transactional
```


---

## 3. Database Design

### 3.1 PostgreSQL Schema

#### 3.1.1 Entity Relationship Diagram
```
┌─────────────┐       ┌─────────────────┐
│    Users    │──1:1──│  UserProfiles   │
└─────────────┘       └─────────────────┘
      │
      │ 1:N
      ├──────────────┬──────────────┬──────────────┬──────────────┐
      │              │              │              │              │
      ▼              ▼              ▼              ▼              ▼
┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐
│ Invoices │  │ LegalQueries │  │   Subsidy    │  │Negotia-  │  │  Audit   │
│          │  │              │  │ Applications │  │  tions   │  │   Logs   │
└──────────┘  └──────────────┘  └──────────────┘  └──────────┘  └──────────┘
```

#### 3.1.2 Table Definitions

**users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    company_name VARCHAR(255),
    business_sector VARCHAR(100),
    turnover_tier VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);
```

**user_profiles** (Encrypted Fields)
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_type VARCHAR(100),
    gst_number TEXT,  -- Encrypted with AES-256
    pan_number TEXT,  -- Encrypted with AES-256
    registered_address TEXT,  -- Encrypted with AES-256
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**invoices** (Encrypted Fields)
```sql
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invoice_number TEXT,  -- Encrypted
    vendor_name TEXT,  -- Encrypted
    invoice_date DATE,
    due_date DATE,
    total_amount TEXT,  -- Encrypted numeric
    tax_amount TEXT,  -- Encrypted numeric
    currency VARCHAR(10) DEFAULT 'INR',
    status VARCHAR(50) DEFAULT 'pending',
    file_path TEXT,  -- Encrypted S3 key
    extracted_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_invoices_user_status ON invoices(user_id, status);
```

**legal_queries**
```sql
CREATE TABLE legal_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    response_text TEXT,
    risk_level VARCHAR(20),
    relevant_sections JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_legal_queries_user_created ON legal_queries(user_id, created_at);
```

**subsidy_applications**
```sql
CREATE TABLE subsidy_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheme_name VARCHAR(255),
    scheme_description TEXT,
    eligibility_status VARCHAR(50),
    application_status VARCHAR(50) DEFAULT 'draft',
    applied_date DATE,
    scheme_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_subsidy_apps_user_status ON subsidy_applications(user_id, application_status);
```

**negotiations** (Encrypted Fields)
```sql
CREATE TABLE negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vendor_name TEXT,  -- Encrypted
    negotiation_type VARCHAR(100),
    email_content TEXT,  -- Encrypted
    status VARCHAR(50) DEFAULT 'draft',
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**audit_logs** (Append-Only)
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

### 3.2 ChromaDB Vector Database

#### 3.2.1 Collections

**legal_chunks**
- **Purpose**: Store legal document chunks with embeddings
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Metadata Schema**:
  ```python
  {
      "law_type": str,  # GST, Income Tax, Companies Act
      "section_number": str,
      "turnover_threshold": float,  # in rupees
      "sector_tag": str,
      "effective_date": str,  # ISO format
      "chunk_type": str  # main, proviso, sub_clause
  }
  ```

**scheme_chunks**
- **Purpose**: Store government subsidy schemes
- **Metadata Schema**:
  ```python
  {
      "scheme_name": str,
      "industry": str,
      "min_investment": float,
      "max_investment": float,
      "benefit_percentage": float,
      "deadline": str
  }
  ```

#### 3.2.2 Storage Structure
```
legal_db/
├── chroma.sqlite3                    # SQLite metadata store
├── 39062cb3-fc7d-435a-88fd-6cb87754db71/  # Collection ID
│   ├── data_level0.bin              # Vector data
│   ├── header.bin                   # Collection header
│   ├── length.bin                   # Vector lengths
│   └── link_lists.bin               # HNSW index
└── seen_notifications.json          # Monitoring state
```

### 3.3 File Storage (AWS S3 / Local)

#### 3.3.1 S3 Bucket Structure
```
microcfo-invoices/
├── {user_id}/
│   ├── invoices/
│   │   ├── {invoice_id}.png
│   │   ├── {invoice_id}.pdf
│   │   └── ...
│   └── exports/
│       ├── tally_{timestamp}.xml
│       ├── zoho_{timestamp}.json
│       └── ...
```

#### 3.3.2 Encryption
- **Server-Side Encryption**: SSE-S3 or SSE-KMS
- **Client-Side Encryption**: Optional for sensitive files
- **Access Control**: IAM roles with least privilege

#### 3.3.3 Local Fallback
```
temp_uploads/
├── {uuid}.png
├── {uuid}.pdf
└── ...
```


---

## 4. API Design

### 4.1 API Structure

#### 4.1.1 Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.microcfo.com`
- **API Version**: `/api/v1`

#### 4.1.2 Authentication
- **Method**: JWT Bearer Token
- **Header**: `Authorization: Bearer <token>`
- **Token Expiration**: 24 hours
- **Refresh**: Re-login required

### 4.2 Endpoint Categories

#### 4.2.1 Authentication Endpoints
```
POST   /api/v1/auth/register          # User registration
POST   /api/v1/auth/login             # User login
GET    /api/v1/auth/me                # Get current user
PUT    /api/v1/auth/profile           # Update profile
POST   /api/v1/auth/logout            # Logout
```

#### 4.2.2 Onboarding Endpoints
```
POST   /api/v1/onboarding/start       # Start onboarding flow
POST   /api/v1/onboarding/company     # Save company info
POST   /api/v1/onboarding/industry    # Select industry
POST   /api/v1/onboarding/turnover    # Select turnover tier
POST   /api/v1/onboarding/gst         # GST details
POST   /api/v1/onboarding/complete    # Complete onboarding
GET    /api/v1/onboarding/status      # Get onboarding status
```

#### 4.2.3 Visual Auditor Endpoints (Agent A)
```
POST   /api/v1/visual-auditor/scan-url           # Scan from URL
POST   /api/v1/visual-auditor/scan-upload        # Scan uploaded file
GET    /api/v1/visual-auditor/invoices           # List invoices
GET    /api/v1/visual-auditor/invoices/{id}      # Get invoice details
PUT    /api/v1/visual-auditor/invoices/{id}      # Update invoice
DELETE /api/v1/visual-auditor/invoices/{id}      # Delete invoice
```

#### 4.2.4 Legal Sentinel Endpoints (Agent B)
```
POST   /api/v1/legal-sentinel/query              # Ask legal question
GET    /api/v1/legal-sentinel/history            # Query history
GET    /api/v1/legal-sentinel/notifications      # Get legal alerts
POST   /api/v1/legal-sentinel/subscribe          # Subscribe to alerts
```

#### 4.2.5 Subsidy Hunter Endpoints (Agent C)
```
POST   /api/v1/subsidy-hunter/search             # Search subsidies
GET    /api/v1/subsidy-hunter/schemes            # List all schemes
GET    /api/v1/subsidy-hunter/applications       # User applications
POST   /api/v1/subsidy-hunter/apply              # Apply for subsidy
```

#### 4.2.6 Negotiator Endpoints (Agent D)
```
POST   /api/v1/negotiator/generate               # Generate draft
GET    /api/v1/negotiator/drafts                 # List drafts
GET    /api/v1/negotiator/drafts/{id}            # Get draft
PUT    /api/v1/negotiator/drafts/{id}            # Update draft
DELETE /api/v1/negotiator/drafts/{id}            # Delete draft
```

#### 4.2.7 ERP Export Endpoints
```
POST   /api/v1/erp/export/tally-xml              # Export to Tally XML
POST   /api/v1/erp/export/tally-csv              # Export to Tally CSV
POST   /api/v1/erp/export/zoho                   # Export to Zoho Books
POST   /api/v1/erp/export/csv                    # Export to CSV
POST   /api/v1/erp/export/json                   # Export to JSON
GET    /api/v1/erp/formats                       # List supported formats
```

#### 4.2.8 Audit Trail Endpoints
```
GET    /api/v1/audit/logs                        # Query audit logs
GET    /api/v1/audit/logs/{id}                   # Get log details
GET    /api/v1/audit/export                      # Export logs (CSV/JSON)
GET    /api/v1/audit/stats                       # Audit statistics
```

#### 4.2.9 Async Task Endpoints
```
POST   /api/v1/tasks/submit                      # Submit async task
GET    /api/v1/tasks/{task_id}/status            # Get task status
GET    /api/v1/tasks/{task_id}/result            # Get task result
DELETE /api/v1/tasks/{task_id}                   # Cancel task
```

#### 4.2.10 WebSocket Endpoint
```
WS     /ws/{user_id}                             # WebSocket connection
```

### 4.3 Request/Response Examples

#### 4.3.1 Visual Auditor - Scan Invoice
**Request**:
```http
POST /api/v1/visual-auditor/scan-url
Content-Type: application/json
Authorization: Bearer <token>

{
  "image_url": "https://example.com/invoice.png",
  "use_mock": false
}
```

**Response**:
```json
{
  "vendor_name": "ABC Machinery Pvt Ltd",
  "invoice_date": "2024-01-15",
  "total_amount": 590000.0,
  "tax_amount": 90000.0,
  "gstin": "27AABCU9603R1ZX",
  "line_items": [
    {
      "description": "Industrial Loom Machine",
      "amount": 500000.0,
      "category": "Capital Goods"
    }
  ],
  "is_handwritten": false,
  "tampering_detected": false,
  "compliance_flags": [],
  "confidence_score": 0.95,
  "disclaimer": "This is AI-generated output. Verify with a professional."
}
```

#### 4.3.2 Legal Sentinel - Query
**Request**:
```http
POST /api/v1/legal-sentinel/query
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "Can I claim ITC on food expenses?",
  "user_context": ""
}
```

**Response**:
```json
{
  "risk_level": "HIGH",
  "relevant_section": "Section 17(5) of CGST Act",
  "compliant_action": "ITC blocked for food items unless for resale. Consult CA.",
  "disclaimer": "This is not legal advice. Consult a chartered accountant."
}
```

#### 4.3.3 Negotiator - Generate Draft
**Request**:
```http
POST /api/v1/negotiator/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "counterparty_name": "XYZ Suppliers",
  "amount": 250000.0,
  "transaction_type": "payable",
  "due_date": "2024-02-01",
  "current_cash_position": 100000.0,
  "upcoming_outflows": 150000.0,
  "invoice_id": "INV-2024-001"
}
```

**Response**:
```json
{
  "intent": "credit_extension",
  "strategy_explanation": "Cash flow analysis shows insufficient funds...",
  "whatsapp_message": "Hi XYZ, need 15 days for INV-2024-001...",
  "formal_email": "Dear XYZ Team,\n\nWe value our partnership...",
  "option_a": "RELATIONSHIP-FOCUSED:\nWhatsApp: ...\n\nEmail:\n...",
  "option_b": "TRANSACTIONAL-FOCUSED:\nWhatsApp: ...\n\nEmail:\n...",
  "disclaimer": "DRAFT ONLY - Review before sending. Never auto-sent."
}
```

### 4.4 Error Responses

#### 4.4.1 Standard Error Format
```json
{
  "error": "ValidationError",
  "message": "Invalid input data",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  },
  "timestamp": "2024-01-20T10:30:00Z",
  "request_id": "req_abc123"
}
```

#### 4.4.2 HTTP Status Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **401**: Unauthorized (missing/invalid token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **429**: Too Many Requests (rate limit)
- **500**: Internal Server Error


---

## 5. Security Architecture

### 5.1 Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Security Layers                        │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Layer 1: Network Security (HTTPS/TLS)         │    │
│  └────────────────────────────────────────────────┘    │
│                         │                               │
│  ┌────────────────────────────────────────────────┐    │
│  │  Layer 2: Authentication (JWT)                 │    │
│  └────────────────────────────────────────────────┘    │
│                         │                               │
│  ┌────────────────────────────────────────────────┐    │
│  │  Layer 3: Authorization (RBAC)                 │    │
│  └────────────────────────────────────────────────┘    │
│                         │                               │
│  ┌────────────────────────────────────────────────┐    │
│  │  Layer 4: Rate Limiting (100 req/min)          │    │
│  └────────────────────────────────────────────────┘    │
│                         │                               │
│  ┌────────────────────────────────────────────────┐    │
│  │  Layer 5: Data Encryption (AES-256)            │    │
│  └────────────────────────────────────────────────┘    │
│                         │                               │
│  ┌────────────────────────────────────────────────┐    │
│  │  Layer 6: Audit Logging (All Actions)          │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Authentication & Authorization

#### 5.2.1 JWT Token Structure
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "exp": 1705756800,
  "iat": 1705670400,
  "roles": ["user"]
}
```

#### 5.2.2 Password Security
- **Hashing**: bcrypt with salt rounds = 12
- **Minimum Length**: 8 characters
- **Requirements**: Uppercase, lowercase, number, special char
- **Storage**: Never stored in plaintext

#### 5.2.3 Role-Based Access Control (RBAC)
```python
Roles:
- user: Standard user access
- admin: Full system access
- auditor: Read-only audit access

Permissions:
- invoice:read, invoice:write, invoice:delete
- legal:query, legal:subscribe
- subsidy:search, subsidy:apply
- negotiation:draft, negotiation:send (blocked)
- audit:read, audit:export
```

### 5.3 Data Encryption

#### 5.3.1 Encryption at Rest

**Database Encryption (AES-256 Fernet)**
```python
# Encrypted columns using custom SQLAlchemy types
class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return fernet.encrypt(value.encode()).decode()
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return fernet.decrypt(value.encode()).decode()
        return value
```

**Encrypted Fields**:
- GST Number, PAN Number
- Invoice numbers, vendor names
- Invoice amounts, tax amounts
- Registered addresses
- Negotiation email content
- File paths (S3 keys)

**S3 File Encryption**:
- Server-Side Encryption: SSE-S3 or SSE-KMS
- Automatic encryption on upload
- Transparent decryption on download

#### 5.3.2 Encryption in Transit
- **HTTPS/TLS 1.3**: All API communication
- **WSS**: WebSocket Secure for real-time updates
- **Certificate**: Let's Encrypt or commercial CA

#### 5.3.3 Key Management
```python
# Environment-based key storage
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")  # 32-byte Fernet key
AWS_KMS_KEY_ID = os.getenv("AWS_KMS_KEY_ID")  # For S3 SSE-KMS

# Key rotation strategy
- Rotate encryption keys every 90 days
- Maintain old keys for decryption
- Re-encrypt data with new keys
```

### 5.4 Audit Trail System

#### 5.4.1 Logged Actions (30+ Types)
```python
# Authentication
- USER_LOGIN, USER_LOGOUT, USER_REGISTER
- PASSWORD_CHANGE, TOKEN_REFRESH

# Invoice Operations
- INVOICE_SCAN, INVOICE_VIEW, INVOICE_UPDATE, INVOICE_DELETE
- INVOICE_EXPORT

# Legal Operations
- LEGAL_QUERY, LEGAL_SUBSCRIBE, LEGAL_NOTIFICATION_VIEW

# Subsidy Operations
- SUBSIDY_SEARCH, SUBSIDY_APPLICATION_CREATE, SUBSIDY_APPLICATION_SUBMIT

# Negotiation Operations
- NEGOTIATION_DRAFT_CREATE, NEGOTIATION_DRAFT_VIEW, NEGOTIATION_DRAFT_UPDATE

# System Operations
- SETTINGS_UPDATE, PROFILE_UPDATE, AUDIT_LOG_EXPORT
```

#### 5.4.2 Audit Log Structure
```python
{
    "id": "uuid",
    "user_id": "uuid",
    "action": "INVOICE_SCAN",
    "resource_type": "invoice",
    "resource_id": "uuid",
    "details": {
        "vendor_name": "ABC Corp",
        "amount": 50000.0,
        "confidence_score": 0.95
    },
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "severity": "INFO",  # INFO, WARNING, ERROR, CRITICAL
    "created_at": "2024-01-20T10:30:00Z"
}
```

#### 5.4.3 Audit Trail Features
- **Append-Only**: Cannot be modified or deleted
- **Tamper-Proof**: Cryptographic hashing (optional)
- **Retention**: 7 years (compliance requirement)
- **Export**: CSV, JSON formats
- **Search**: By user, action, date range, resource

### 5.5 Legal Disclaimers & Guardrails

#### 5.5.1 Disclaimer Types
1. **General**: AI assistant, not a CA
2. **Legal**: Not legal advice
3. **Financial**: Not financial advice
4. **Tax**: Not tax advice
5. **Negotiation**: Draft only, never auto-sent
6. **Invoice**: Verify with professional
7. **Subsidy**: Check eligibility criteria

#### 5.5.2 Guardrails
```python
# Negotiator: Draft-Only Mode
- NEVER auto-send emails
- Always require user approval
- Display prominent warning
- Log all draft generations

# Invoice Processing: Verification Required
- No auto-approval
- Manual verification for amounts > ₹50,000
- Flag suspicious invoices

# Legal Queries: Professional Consultation
- Recommend CA consultation for HIGH risk
- Disclaimer on every response
- Conservative interpretations
```

#### 5.5.3 Disclaimer Display
- **First Visit**: Modal with acceptance required
- **Persistent Banner**: Always visible after acceptance
- **API Responses**: Disclaimer field in JSON
- **Session Tracking**: Cookie-based acceptance

### 5.6 Rate Limiting

#### 5.6.1 Rate Limit Configuration
```python
# Per-user limits
- 100 requests per minute
- 1000 requests per hour
- 10000 requests per day

# Per-endpoint limits
- Invoice scan: 20 per hour
- Legal query: 50 per hour
- Subsidy search: 30 per hour
- Negotiation draft: 10 per hour
```

#### 5.6.2 Rate Limit Response
```json
{
  "error": "RateLimitExceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60,
  "limit": 100,
  "remaining": 0,
  "reset": 1705670460
}
```

### 5.7 Input Validation

#### 5.7.1 Validation Rules
```python
# Email validation
- RFC 5322 compliant
- Max length: 255 characters

# GSTIN validation
- Format: 15 characters
- Pattern: \d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}

# PAN validation
- Format: 10 characters
- Pattern: [A-Z]{5}\d{4}[A-Z]{1}

# Amount validation
- Positive numbers only
- Max: 999,999,999.99
- Decimal places: 2

# File upload validation
- Max size: 50 MB
- Allowed types: PDF, PNG, JPG, JPEG
- Virus scanning (optional)
```


---

## 6. Data Flow Diagrams

### 6.1 Invoice Processing Flow (Agent A)

```
User uploads invoice → Frontend UI
    ↓
POST /api/v1/visual-auditor/scan-upload
    ↓
Integration Server (Middleware: Auth, Rate Limit, Audit)
    ↓
Visual Auditor Router validates file → Store in S3/local
    ↓
MCP Bridge calls Agent A: scan_invoice_document
    ↓
MCP Server (Agent A):
  1. Load image from S3/local
  2. Send to Gemini 2.5 Flash
  3. Parse JSON response
  4. Apply validations
  5. Trigger orchestrator
    ↓
Return structured invoice → Integration Server
    ↓
Save to PostgreSQL (encrypted) + Add disclaimer + Log audit
    ↓
Return JSON response → Frontend UI displays data
```

### 6.2 Legal Query Flow (Agent B)

```
User asks legal question → Frontend UI
    ↓
POST /api/v1/legal-sentinel/query
    ↓
Integration Server (Middleware: Auth, Cache Check)
    ↓
Legal Sentinel Router gets user profile → Call MCP Bridge
    ↓
MCP Server (Agent B):
  1. Fetch user profile (turnover tier)
  2. Query ChromaDB (hybrid search)
  3. Filter by turnover threshold
  4. Assess risk level
  5. Generate compliant action
    ↓
Return legal risk assessment → Integration Server
    ↓
Save to PostgreSQL + Cache result (1 hour) + Add disclaimer + Log audit
    ↓
Return JSON response → Frontend UI displays risk
```

### 6.3 Real-time Legal Monitoring Flow

```
Legal Sentinel Monitor (Background - Daily):
  1. Scrape Government Websites (CBIC, MCA, Income Tax)
  2. Extract Notifications
  3. Check User Relevance (turnover, industry, subscription)
    ↓
Send alerts to relevant users:
  - WebSocket: Real-time notification
  - WhatsApp: Business API message
  - Email: Notification email
    ↓
User receives alert on device
```

### 6.4 ERP Export Flow

```
User selects invoices → Frontend UI
    ↓
POST /api/v1/erp/export/tally-xml
    ↓
Integration Server - ERP Export Router:
  1. Fetch invoices from PostgreSQL
  2. Decrypt sensitive fields
  3. Transform to Tally XML format
  4. Generate voucher entries
  5. Create download file
    ↓
Return file download → Frontend UI downloads XML
```


---

## 7. Deployment Architecture

### 7.1 Development Environment

```
Developer Machine:
  - Frontend (localhost:5173)
  - Backend (localhost:8000)
  - PostgreSQL (:5432)
  - ChromaDB (local)
```

### 7.2 Docker Deployment

```
Docker Compose Stack:
  - frontend (nginx:alpine) - Port 80
  - backend (python:3.9-slim) - Port 8000
  - postgres (postgres:14) - Port 5432
  - redis (redis:7-alpine) - Port 6379
```

### 7.3 Production Architecture (AWS)

```
AWS Cloud:
  - CloudFront CDN (Static assets, SSL/TLS)
  - Application Load Balancer (HTTPS, Health checks)
  - ECS Tasks (Backend Containers) x3
  - RDS PostgreSQL (Multi-AZ, Encrypted, Automated backups)
  - S3 Bucket (Invoice images, Export files, SSE)
  - ElastiCache Redis (Session storage, Rate limiting)
```

### 7.4 Scaling Strategy

#### Horizontal Scaling
- Frontend: CloudFront + S3 (auto-scales)
- Backend: ECS Auto Scaling (2-10 tasks)
- Database: RDS Read Replicas (1-3 replicas)

#### Vertical Scaling
- Backend: t3.medium → t3.large → t3.xlarge
- Database: db.t3.medium → db.r5.large → db.r5.xlarge

#### Caching Strategy
- Redis: Session data, rate limit counters
- Application Cache: Legal query results (1 hour TTL)
- CDN Cache: Static assets (24 hours TTL)


---

## 8. Technology Stack

### 8.1 Frontend Technologies
- **React 18**: UI library with hooks
- **Vite 4**: Build tool and dev server
- **React Router 6**: Client-side routing
- **Tailwind CSS 3**: Utility-first CSS framework
- **Headless UI**: Unstyled accessible components
- **Heroicons**: SVG icon library
- **Axios**: Promise-based HTTP client
- **WebSocket API**: Native WebSocket for real-time

### 8.2 Backend Technologies
- **Python 3.7+**: Programming language
- **FastAPI 0.104+**: Modern web framework
- **Uvicorn**: ASGI server
- **Pydantic 2.0+**: Data validation
- **PostgreSQL 14+**: Relational database
- **SQLAlchemy 2.0+**: ORM
- **Alembic**: Database migrations
- **ChromaDB 0.4+**: Vector database
- **Sentence Transformers**: Embeddings (all-MiniLM-L6-v2)
- **Google Gemini 2.5 Flash**: Vision & text generation
- **cryptography**: Fernet encryption (AES-256)
- **python-jose**: JWT tokens
- **passlib**: Password hashing (bcrypt)
- **boto3**: AWS S3 client
- **Pillow**: Image processing

### 8.3 Infrastructure
- **Docker 24+**: Container runtime
- **Docker Compose**: Multi-container orchestration
- **AWS ECS Fargate**: Container orchestration
- **AWS RDS PostgreSQL**: Managed database
- **AWS S3**: Object storage
- **AWS CloudFront**: CDN
- **AWS ALB**: Load balancer
- **AWS ElastiCache Redis**: Caching
- **AWS KMS**: Key management

### 8.4 Development Tools
- **Black**: Python code formatter
- **Flake8**: Python linter
- **mypy**: Static type checker
- **ESLint**: JavaScript linter
- **Prettier**: JavaScript formatter
- **pytest**: Python testing framework
- **Swagger/OpenAPI**: Auto-generated API docs

### 8.5 External APIs
- **Google Gemini API**: Vision and text generation
- **OpenRouter API**: Fallback AI provider
- **WhatsApp Business API**: Alert notifications
- **SendGrid/AWS SES**: Email notifications


---

## 9. Design Patterns

### 9.1 Architectural Patterns

#### Layered Architecture
```
Presentation Layer (Frontend)
    ↓
API Gateway Layer (Integration Server)
    ↓
Business Logic Layer (MCP Server)
    ↓
Data Access Layer (Database, Vector DB, S3)
```

#### Microservices Pattern
- Integration Server: API gateway and orchestration
- MCP Server: AI agent business logic
- Legal Sentinel Monitor: Background monitoring service
- Database Services: PostgreSQL, ChromaDB, S3

#### Repository Pattern
```python
class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, invoice: Invoice) -> Invoice:
        db_invoice = InvoiceModel(**invoice.dict())
        self.db.add(db_invoice)
        self.db.commit()
        return db_invoice
```

### 9.2 Design Patterns in Use

#### Middleware Pattern
```python
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(AuthorizationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(DisclaimerMiddleware)
```

#### Factory Pattern
```python
class StorageFactory:
    @staticmethod
    def create_storage(storage_type: str):
        if storage_type == "s3":
            return S3Storage()
        elif storage_type == "local":
            return LocalStorage()
```

#### Strategy Pattern
```python
class NegotiationStrategy:
    def generate_content(self, context: dict) -> str:
        pass

class CreditExtensionStrategy(NegotiationStrategy):
    def generate_content(self, context: dict) -> str:
        # Generate credit extension email
        pass
```

#### Observer Pattern
```python
# WebSocket manager notifies connected clients
class WebSocketManager:
    async def notify(self, user_id: str, message: dict):
        if user_id in self.observers:
            await self.observers[user_id].send_json(message)
```

#### Singleton Pattern
```python
# Global instances
cache_manager = CacheManager()
websocket_manager = WebSocketManager()
operation_tracker = OperationTracker()
```

### 9.3 SOLID Principles

- **Single Responsibility**: Each agent has one responsibility
- **Open/Closed**: Storage interface allows S3 or local without changing code
- **Liskov Substitution**: S3Storage and LocalStorage are interchangeable
- **Interface Segregation**: Separate interfaces for different storage operations
- **Dependency Inversion**: High-level modules depend on abstractions


---

## 10. Performance Considerations

### 10.1 Response Time Targets

| Operation | Target | Acceptable | Notes |
|-----------|--------|------------|-------|
| Invoice Scan | < 30s | < 45s | Depends on Gemini API |
| Legal Query | < 5s | < 10s | With caching |
| Subsidy Search | < 3s | < 5s | Vector search |
| Negotiation Draft | < 10s | < 15s | Gemini generation |
| API Endpoints | < 2s | < 5s | 95th percentile |
| Database Query | < 1s | < 2s | With indexes |

### 10.2 Optimization Strategies

#### Caching
```python
# Legal query caching (1 hour TTL)
cache_key = cache_manager.generate_key(
    "legal_query",
    query=query,
    turnover_tier=user.turnover_tier
)
cached_result = cache_manager.get(cache_key)
if cached_result:
    return cached_result

result = perform_legal_query(query)
cache_manager.set(cache_key, result, ttl=3600)
```

#### Database Indexing
```sql
CREATE INDEX idx_invoices_user_status ON invoices(user_id, status);
CREATE INDEX idx_legal_queries_user_created ON legal_queries(user_id, created_at);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

#### Connection Pooling
```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### Lazy Loading
```python
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model
```

### 10.3 Scalability Considerations

#### Horizontal Scaling
- Stateless Backend: No session state in application
- Load Balancing: ALB distributes traffic
- Database Read Replicas: Separate read and write operations

#### Resource Limits
```python
REQUEST_TIMEOUT = 300  # 5 minutes
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
RATE_LIMIT_PER_MINUTE = 100
RATE_LIMIT_PER_HOUR = 1000
```

### 10.4 Monitoring & Metrics

#### Key Metrics
- Request Rate: Requests per second
- Response Time: P50, P95, P99 latencies
- Error Rate: 4xx and 5xx errors
- Database Connections: Active connections
- Cache Hit Rate: Percentage of cache hits
- Queue Depth: Pending async tasks

#### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_db_connection(),
        "cache": cache_manager.get_stats(),
        "websocket": websocket_manager.get_connection_count()
    }
```

---

## 11. Conclusion

This design document provides a comprehensive technical blueprint for the MicroCFO system.

### 11.1 Key Design Decisions

1. **Layered Architecture**: Clear separation between frontend, API gateway, business logic, and data layers
2. **MCP Protocol**: Standardized communication between integration server and AI agents
3. **Encryption at Rest**: AES-256 encryption for sensitive data in PostgreSQL and S3
4. **Audit Trail**: Comprehensive logging of all user actions for compliance
5. **Draft-Only Mode**: Negotiator never auto-sends emails, always requires approval
6. **Vector Database**: ChromaDB for semantic search of legal documents
7. **Real-time Updates**: WebSocket for live notifications and progress updates
8. **ERP Integration**: Export to Tally, Zoho Books, and standard formats

### 11.2 Future Enhancements

- Multi-language Support: Hindi and regional languages
- Mobile Apps: Native iOS and Android applications
- Advanced Analytics: Business intelligence dashboards
- Machine Learning: Custom models for Indian invoices
- Blockchain: Immutable audit trail using blockchain
- API Marketplace: Third-party integrations

---

**Document Version**: 2.0.0  
**Last Updated**: January 20, 2026  
**Status**: Approved ✅

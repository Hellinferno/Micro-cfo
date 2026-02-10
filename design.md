# MicroCFO - System Design Document

## 1. System Overview

### 1.1 Architecture Philosophy
MicroCFO follows a modular, agent-based architecture where specialized AI agents handle specific domains of financial operations. The system uses FastAPI for the backend, React for the frontend, and integrates with Google Gemini for AI capabilities.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  - Chat Interface  - Document Scanner  - Dashboard          │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API (HTTPS)
┌─────────────────────▼───────────────────────────────────────┐
│                  FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Orchestrator (The Brain)                │   │
│  │  - Message Routing  - Context Management             │   │
│  └──────────┬───────────────────────────────────────────┘   │
│             │                                                │
│  ┌──────────▼──────────┬──────────────┬──────────────────┐  │
│  │   Agent A           │   Agent B    │   Agent C        │  │
│  │ Visual Auditor      │Legal Sentinel│Subsidy Hunter    │  │
│  │ (Invoice Analysis)  │(Compliance)  │(Schemes)         │  │
│  └─────────────────────┴──────────────┴──────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Agent D: Negotiator (Vendor Communication)         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              External Services & Storage                     │
│  - PostgreSQL/SQLite  - ChromaDB  - Google Gemini           │
│  - File Storage       - Redis (Optional)  - S3 (Optional)   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (Web Framework)
- Pydantic (Data Validation)
- SQLAlchemy (ORM)
- Alembic (Database Migrations)
- Google Generative AI (Gemini)

**Frontend:**
- React 18+
- Vite (Build Tool)
- TailwindCSS (Styling)
- Axios (HTTP Client)

**Database:**
- PostgreSQL (Production)
- SQLite (Development)
- ChromaDB (Vector Storage)

**AI/ML:**
- Google Gemini 1.5 Flash (General Queries)
- Google Gemini 2.5 Flash (Vision Tasks)
- sentence-transformers (Embeddings)


## 2. Agent Architecture

### 2.1 Agent A: Visual Auditor

**Purpose**: AI-powered invoice scanning and fraud detection

**Technology**: Google Gemini 2.5 Flash (Multimodal Vision)

**Key Components:**
```python
class VisualAuditor:
    - analyze(file_content, content_type) -> InvoiceData
    - analyze_from_url(image_url) -> InvoiceData
    - _get_analysis_prompt() -> str
    - _parse_response(response_text) -> InvoiceData
```

**Data Flow:**
1. User uploads invoice (PNG/JPG/PDF) or provides URL
2. Image converted to base64 or passed as URL
3. Gemini Vision API analyzes image with structured prompt
4. Response parsed into InvoiceData model
5. Orchestrator triggers Agent B/C based on content

**Output Schema:**
```python
class InvoiceData(BaseModel):
    vendor_name: str
    invoice_date: Optional[str]
    total_amount: float
    tax_amount: float
    gstin: Optional[str]
    line_items: List[LineItem]
    is_handwritten: bool
    tampering_detected: bool
    confidence_score: float
    compliance_flags: List[str]
    is_valid_business_expense: bool
    summary: Optional[str]
```

**Fraud Detection Logic:**
- Mismatched fonts detection
- Blurred/tampered number identification
- Handwritten override detection
- GSTIN validation
- Date staleness checking (>30 days)

**Orchestrator Triggers:**
- Capital Goods >₹1L → Agent C (Subsidy Hunter)
- Personal/Entertainment items → Agent B (Legal Sentinel)

### 2.2 Agent B: Legal Sentinel

**Purpose**: AI-powered compliance checking with Structure-Aware RAG

**Technology**: Google Gemini 1.5 Flash + ChromaDB + sentence-transformers

**Key Components:**
```python
class LegalSentinel:
    - analyze(query, user_context) -> ComplianceResult
    - _get_prompt(query, context) -> str
    - _parse_response(response_text) -> ComplianceResult
```

**RAG Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  1. Legal Document Ingestion (legal_ingestion.py)      │
│     - Structure-Aware Text Splitting                    │
│     - Metadata Extraction (turnover, sector, dates)     │
│     - CA-Logic Based Chunking                           │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│  2. Vector Database (vector_database.py)                │
│     - ChromaDB Storage                                  │
│     - Sentence Transformer Embeddings                   │
│     - Semantic Search                                   │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│  3. Context-Aware Retrieval                             │
│     - User Profile Filtering (turnover, sector)         │
│     - Hybrid Search (keyword + semantic)                │
│     - Conservative CA-Style Responses                   │
└─────────────────────────────────────────────────────────┘
```

**Legal Text Splitting Strategy:**
- Recognizes: `Section X`, `Rule Y`, `Notification No.`
- Preserves: `Provided that...` clauses with parent sections
- Maintains: Sub-clause `(a), (b), (c)` relationships

**Metadata Extraction:**
- Turnover Thresholds: "turnover exceeds 5 crore" → 50000000
- Sector Tags: Textile, Manufacturing, Technology, Works Contract
- Effective Dates: Automatic date extraction from notifications
- Law Types: GST, Income Tax, Companies Act classification

**Output Schema:**
```python
class ComplianceResult(BaseModel):
    risk_level: str  # LOW, MEDIUM, HIGH
    relevant_section: str
    explanation: str
    compliant_action: str
```

**Real-time Monitoring:**
- Government website scraping (CBIC, MCA, Income Tax)
- User relevance checking
- Telegram Bot API integration for alerts


### 2.3 Agent C: Subsidy Hunter

**Purpose**: Government scheme discovery with intelligent matching

**Technology**: Web Scraping (BeautifulSoup4) + Optional Firecrawl Integration

**Key Components:**
```python
class SubsidyHunter:
    - find_subsidies(sector, capex, state) -> List[Subsidy]
    - search_by_query(query) -> List[Subsidy]
    - _extract_sector_from_query(query) -> str
    - _extract_amount_from_query(query) -> float
    - refresh_schemes() -> int
```

**Search Strategy:**
1. Extract sector from natural language query
2. Extract CAPEX amount (supports crore, lakh, raw numbers)
3. Scrape government portals (StartupIndia, MyScheme)
4. Filter by sector keywords
5. Filter by CAPEX thresholds
6. Calculate match scores
7. Return top 5 schemes

**Sector Keywords Mapping:**
```python
sector_keywords = {
    "manufacturing": ["manufacturing", "factory", "plant", "production"],
    "textile": ["textile", "garment", "apparel", "fabric"],
    "food_processing": ["food", "dairy", "beverage", "bakery"],
    "agriculture": ["farm", "agri", "rural", "village"],
    "it": ["it", "software", "tech", "digital"],
    "pharma": ["pharma", "drug", "medicine", "medical"],
    "women_entrepreneur": ["women", "woman", "female"],
    "services": ["service", "consulting", "hotel", "tourism"]
}
```

**Output Schema:**
```python
class Subsidy(BaseModel):
    name: str
    benefit: str
    eligibility: str
    ministry: str
    link: Optional[str]
    max_subsidy: Optional[str]
    match_score: Optional[float]
    documents_required: List[str]
```

**Caching Strategy:**
- In-memory cache for scheme data
- Manual refresh capability
- Cache invalidation on demand

### 2.4 Agent D: Negotiator

**Purpose**: AI-powered vendor negotiation email generation

**Technology**: Google Gemini 1.5 Flash

**Key Components:**
```python
class Negotiator:
    - generate_email(request: NegotiationRequest) -> EmailDraft
    - _get_prompt(request) -> str
    - _parse_response(response_text) -> EmailDraft
```

**Negotiation Strategy:**
```python
class NegotiationIntent(Enum):
    CREDIT_EXTENSION = "credit_extension"      # Cash flow tight
    PAYMENT_CHASE = "payment_chase"            # Overdue receivables
    EARLY_PAYMENT_OFFER = "early_payment_offer" # Cash surplus
```

**Decision Logic:**
- Credit Extension: When `projected_cash_balance < upcoming_outflows`
- Payment Chase: When `invoice_due_date < today`
- Early Payment Offer: When `cash_surplus` is high

**Input Schema:**
```python
class NegotiationRequest(BaseModel):
    invoice_data: Dict[str, Any]
    negotiation_context: str
    vendor_relationship: Optional[str] = "neutral"  # neutral, good, strained
    tone: Optional[str] = "professional"  # professional, firm, polite
```

**Output Schema:**
```python
class EmailDraft(BaseModel):
    subject: str
    body: str
    strategy_explanation: str
```

**A/B Testing Feature:**
- Option A: Relationship-focused approach
- Option B: Transactional approach
- User selects preferred style

### 2.5 Orchestrator

**Purpose**: Intelligent message routing and context management

**Key Components:**
```python
class Orchestrator:
    - process_message(message, preferred_agent, context) -> Dict
    - _determine_agent(message, preferred) -> str
    - _handle_compliance(message) -> Dict
    - _handle_subsidies(message) -> Dict
    - _handle_invoice_question(message) -> Dict
    - _handle_negotiation(message) -> Dict
    - _handle_general(message) -> Dict
```

**Agent Selection Algorithm:**
1. Check if user specified preferred agent
2. Score message against keyword lists:
   - Compliance: gst, tax, itc, compliance, section, law
   - Subsidy: subsidy, scheme, grant, loan, funding
   - Invoice: scan, upload, invoice, bill, document
   - Negotiation: negotiate, email, draft, vendor, payment
3. Select agent with highest score
4. Fallback to general handler if no match

**Context Management:**
- Maintains conversation history
- Passes context to agents
- Tracks agent usage statistics
- Provides suggested follow-up actions


## 3. Database Design

### 3.1 Entity Relationship Diagram

```
┌─────────────┐
│    Users    │
├─────────────┤
│ id (UUID)   │◄─────┐
│ email       │      │
│ password    │      │
│ full_name   │      │
│ company     │      │
│ sector      │      │
│ turnover    │      │
└─────────────┘      │
                     │
┌─────────────────┐  │
│ User Profiles   │  │
├─────────────────┤  │
│ id (UUID)       │  │
│ user_id (FK)    │──┘
│ gst_number*     │
│ pan_number*     │
│ address*        │
│ preferences     │
└─────────────────┘

┌─────────────────┐
│    Invoices     │
├─────────────────┤
│ id (UUID)       │
│ user_id (FK)    │──┐
│ invoice_no*     │  │
│ vendor_name*    │  │
│ invoice_date    │  │
│ total_amount*   │  │
│ tax_amount*     │  │
│ status          │  │
│ file_path*      │  │
│ extracted_data  │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │
│ Legal Queries   │  │
├─────────────────┤  │
│ id (UUID)       │  │
│ user_id (FK)    │──┤
│ query_text      │  │
│ response_text   │  │
│ risk_level      │  │
│ sections        │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │
│ Subsidy Apps    │  │
├─────────────────┤  │
│ id (UUID)       │  │
│ user_id (FK)    │──┤
│ scheme_name     │  │
│ eligibility     │  │
│ status          │  │
│ scheme_data     │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │
│  Negotiations   │  │
├─────────────────┤  │
│ id (UUID)       │  │
│ user_id (FK)    │──┤
│ vendor_name*    │  │
│ type            │  │
│ email_content*  │  │
│ status          │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │
│  Audit Logs     │  │
├─────────────────┤  │
│ id (UUID)       │  │
│ user_id (FK)    │──┘
│ action          │
│ resource_type   │
│ resource_id     │
│ details         │
│ ip_address      │
└─────────────────┘

* = Encrypted fields
```

### 3.2 Encryption Strategy

**Encrypted Fields:**
- user_profiles: gst_number, pan_number, registered_address
- invoices: invoice_number, vendor_name, total_amount, tax_amount, file_path
- negotiations: vendor_name, email_content

**Encryption Method:**
- Algorithm: AES-256-GCM
- Key Management: Environment variable (ENCRYPTION_KEY)
- Key Rotation: Every 90 days (manual process)

**Implementation:**
```python
from cryptography.fernet import Fernet

class EncryptionManager:
    def __init__(self, key: str):
        self.cipher = Fernet(key.encode())
    
    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

### 3.3 Database Migrations

**Migration Tool**: Alembic

**Migration Files:**
- `000_initial_schema.py`: Core tables creation
- `001_add_encryption.py`: Encryption migration
- `002_add_business_profiles.py`: Business profile enhancements
- `003_add_proactive_intelligence.py`: Proactive intelligence tables

**Migration Process:**
1. Generate migration: `alembic revision --autogenerate -m "description"`
2. Review migration file
3. Test on staging environment
4. Apply to production: `alembic upgrade head`
5. Verify data integrity

**Rollback Strategy:**
- Each migration includes `downgrade()` function
- Rollback command: `alembic downgrade -1`
- Database backup before migration


## 4. API Design

### 4.1 API Structure

**Base URL**: `/api/v1`

**Authentication**: JWT Bearer Token

**Response Format**:
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### 4.2 Endpoint Specifications

#### 4.2.1 Health Check
```
GET /health
Response: { "status": "healthy", "app": "MicroCFO", "version": "2.0.0" }
```

#### 4.2.2 Chat API
```
POST /api/v1/chat
Request:
{
  "message": "Can I claim ITC on office supplies?",
  "agent": "auto",  // or "visual_auditor", "legal_sentinel", etc.
  "context": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ]
}

Response:
{
  "success": true,
  "message": "Response text...",
  "agent_used": "legal_sentinel",
  "suggested_actions": ["Check related sections", "Save answer"]
}
```

#### 4.2.3 Invoice Analysis
```
POST /api/v1/invoices/analyze
Content-Type: multipart/form-data
Request: file (PNG/JPG/PDF)

Response:
{
  "success": true,
  "data": {
    "vendor_name": "ABC Suppliers",
    "invoice_date": "2024-01-15",
    "total_amount": 15000.00,
    "tax_amount": 2700.00,
    "gstin": "27AADCB2230M1ZT",
    "line_items": [
      {
        "description": "Office Supplies",
        "amount": 10000.00,
        "category": "Raw Material"
      }
    ],
    "is_handwritten": false,
    "tampering_detected": false,
    "confidence_score": 0.95,
    "compliance_flags": [],
    "is_valid_business_expense": true,
    "summary": "Invoice processed successfully"
  }
}
```

```
POST /api/v1/invoices/analyze-url
Request: { "image_url": "https://example.com/invoice.jpg" }
Response: Same as above
```

#### 4.2.4 Compliance Query
```
POST /api/v1/compliance/query
Request:
{
  "query": "What are the ITC eligibility rules?",
  "user_context": "Turnover: 3 crore, Sector: Manufacturing"
}

Response:
{
  "success": true,
  "data": {
    "risk_level": "MEDIUM",
    "relevant_section": "Section 17(5) of CGST Act, 2017",
    "explanation": "Input Tax Credit has specific blocked categories...",
    "compliant_action": "Review expense categories against blocked ITC list"
  }
}
```

#### 4.2.5 Subsidy Search
```
POST /api/v1/subsidies/search
Request:
{
  "sector": "Textile",
  "capex": 1000000,
  "state": "Gujarat"
}

Response:
{
  "success": true,
  "data": [
    {
      "name": "TUFS Scheme",
      "benefit": "Up to 25% subsidy on capital goods",
      "eligibility": "Textile manufacturers with capex > 10L",
      "ministry": "Ministry of Textiles",
      "link": "https://texmin.nic.in/tufs",
      "max_subsidy": "₹2.5 lakh",
      "match_score": 0.92,
      "documents_required": ["GST Certificate", "Project Report"]
    }
  ]
}
```

#### 4.2.6 Negotiation Email
```
POST /api/v1/negotiation/generate
Request:
{
  "invoice_data": {
    "vendor_name": "XYZ Suppliers",
    "total_amount": 50000,
    "due_date": "2024-02-01"
  },
  "negotiation_context": "Need 15 days extension due to cash flow",
  "vendor_relationship": "good",
  "tone": "professional"
}

Response:
{
  "success": true,
  "data": {
    "subject": "Request for Payment Extension - Invoice #INV-001",
    "body": "Dear XYZ Suppliers,\n\nI hope this email finds you well...",
    "strategy_explanation": "Relationship-focused approach emphasizing partnership"
  }
}
```

### 4.3 Error Handling

**Error Response Format**:
```json
{
  "success": false,
  "message": "User-friendly error message",
  "error": "Technical error details",
  "code": "ERROR_CODE"
}
```

**HTTP Status Codes**:
- 200: Success
- 400: Bad Request (validation error)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 429: Too Many Requests (rate limit)
- 500: Internal Server Error

### 4.4 Rate Limiting

**Limits**:
- General API: 100 requests/minute per user
- Invoice Analysis: 20 requests/minute per user
- Compliance Query: 50 requests/minute per user

**Implementation**: Token bucket algorithm with Redis

**Response Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1612345678
```


## 5. Security Design

### 5.1 Authentication & Authorization

**Authentication Method**: JWT (JSON Web Tokens)

**Token Structure**:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "user",
  "exp": 1612345678,
  "iat": 1612342078
}
```

**Token Lifecycle**:
- Access Token: 24 hours expiry
- Refresh Token: 30 days expiry
- Algorithm: HS256
- Secret Key: Environment variable (SECRET_KEY)

**Authorization Levels**:
- User: Standard access to own data
- Admin: Access to user management
- Super Admin: Full system access

### 5.2 Data Protection

**Encryption at Rest**:
- Algorithm: AES-256-GCM
- Encrypted Fields: PII, financial data, vendor information
- Key Storage: Environment variable (ENCRYPTION_KEY)
- Key Rotation: Every 90 days

**Encryption in Transit**:
- Protocol: TLS 1.3
- Certificate: Let's Encrypt (auto-renewal)
- HSTS: Enabled with 1-year max-age

**Password Security**:
- Hashing: bcrypt
- Salt Rounds: 12
- Minimum Length: 8 characters
- Complexity: Uppercase, lowercase, number, special char

### 5.3 Input Validation

**Validation Strategy**:
- Pydantic models for request validation
- SQL injection prevention via parameterized queries
- XSS prevention via output encoding
- File upload validation (type, size, content)

**File Upload Restrictions**:
- Allowed Types: PNG, JPG, PDF
- Max Size: 10 MB
- Virus Scanning: ClamAV integration (optional)

### 5.4 CORS Configuration

**Allowed Origins**:
- Development: `http://localhost:3000`, `http://localhost:5173`
- Production: Whitelist-only (configured via environment)

**Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS

**Allowed Headers**: Authorization, Content-Type

### 5.5 Audit Logging

**Logged Events**:
- User authentication (login, logout, failed attempts)
- Data access (invoice view, query execution)
- Data modification (create, update, delete)
- Administrative actions (user management, config changes)

**Log Format**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": "uuid",
  "action": "invoice_upload",
  "resource_type": "invoice",
  "resource_id": "uuid",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "details": { "file_size": 1024, "status": "success" }
}
```

**Retention**: 7 years (compliance requirement)

### 5.6 Security Best Practices

**Implemented Measures**:
- Environment-based configuration (no hardcoded secrets)
- Dependency vulnerability scanning (pip-audit)
- Regular security updates
- Principle of least privilege
- Secure session management
- CSRF protection (SameSite cookies)
- Content Security Policy headers

**Compliance**:
- Indian IT Act 2000
- GDPR (for data protection)
- PCI DSS (if payment processing added)


## 6. Frontend Design

### 6.1 Component Architecture

```
src/
├── components/
│   ├── Chat/
│   │   ├── MessageBubble.jsx
│   │   ├── InputBar.jsx
│   │   ├── ActionCard.jsx
│   │   └── InvoiceDrawer.jsx
│   ├── Layout/
│   │   ├── Header.jsx
│   │   ├── Sidebar.jsx
│   │   └── Footer.jsx
│   ├── ui/
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── Modal.jsx
│   │   ├── Badge.jsx
│   │   └── Progress.jsx
│   └── charts/
│       └── Charts.jsx
├── pages/
│   ├── Chat.jsx
│   ├── Dashboard.jsx
│   ├── DocumentScanner.jsx
│   ├── Compliance.jsx
│   └── admin/
│       ├── AdminDashboard.jsx
│       └── SuperAdminDashboard.jsx
├── services/
│   ├── api.js
│   ├── auth.js
│   └── websocket.js
├── hooks/
│   ├── useAuth.js
│   ├── useChat.js
│   └── useInvoice.js
├── utils/
│   ├── formatters.js
│   └── validators.js
└── App.jsx
```

### 6.2 Key Pages

#### 6.2.1 Chat Interface
**Purpose**: Unified conversational interface for all agents

**Features**:
- Message history with role-based styling
- Agent indicator badges
- Suggested action buttons
- File upload for invoice analysis
- Context-aware responses

**State Management**:
```javascript
const [messages, setMessages] = useState([]);
const [loading, setLoading] = useState(false);
const [selectedAgent, setSelectedAgent] = useState('auto');
```

#### 6.2.2 Document Scanner
**Purpose**: Invoice upload and analysis

**Features**:
- Drag-and-drop file upload
- Camera capture (mobile)
- URL input for remote images
- Real-time analysis progress
- Detailed results display with fraud indicators

#### 6.2.3 Dashboard
**Purpose**: Overview of financial metrics and compliance status

**Features**:
- Invoice statistics (total, pending, flagged)
- Compliance risk summary
- Recent queries
- Subsidy opportunities
- Quick actions

#### 6.2.4 Compliance Center
**Purpose**: Legal query interface and history

**Features**:
- Natural language query input
- Risk level indicators
- Section references with links
- Query history with search
- Quick answer templates

### 6.3 Styling System

**Framework**: TailwindCSS

**Color Palette**:
```css
:root {
  --primary: #3B82F6;      /* Blue */
  --secondary: #10B981;    /* Green */
  --danger: #EF4444;       /* Red */
  --warning: #F59E0B;      /* Amber */
  --info: #06B6D4;         /* Cyan */
  --background: #F9FAFB;   /* Gray-50 */
  --surface: #FFFFFF;      /* White */
  --text-primary: #111827; /* Gray-900 */
  --text-secondary: #6B7280; /* Gray-500 */
}
```

**Typography**:
- Font Family: Inter (sans-serif)
- Headings: 600-700 weight
- Body: 400 weight
- Code: Fira Code (monospace)

**Responsive Breakpoints**:
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

### 6.4 State Management

**Approach**: React Context + Hooks

**Contexts**:
- AuthContext: User authentication state
- ChatContext: Conversation state
- ThemeContext: UI theme preferences

**Example**:
```javascript
const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  
  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    setToken(response.data.token);
    setUser(response.data.user);
    localStorage.setItem('token', response.data.token);
  };
  
  return (
    <AuthContext.Provider value={{ user, token, login }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### 6.5 API Integration

**HTTP Client**: Axios

**Configuration**:
```javascript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor (add auth token)
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor (handle errors)
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```


## 7. Deployment Architecture

### 7.1 Environment Configuration

**Environments**:
- Development: Local development with SQLite
- Staging: Pre-production testing with PostgreSQL
- Production: Live system with full infrastructure

**Configuration Management**:
```bash
# .env.development
DEBUG=True
DATABASE_URL=sqlite:///./microcfo.db
GEMINI_API_KEY=your_dev_key

# .env.production
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:5432/microcfo
GEMINI_API_KEY=your_prod_key
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key
```

### 7.2 Docker Configuration

**Backend Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile**:
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

**Docker Compose**:
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/microcfo
    depends_on:
      - db
    volumes:
      - ./file_storage:/app/file_storage

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=microcfo
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 7.3 Cloud Deployment (AWS Example)

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│                    Route 53 (DNS)                        │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              CloudFront (CDN)                            │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│         Application Load Balancer                        │
└─────────┬───────────────────────┬───────────────────────┘
          │                       │
┌─────────▼─────────┐   ┌────────▼──────────┐
│  ECS/Fargate      │   │  ECS/Fargate      │
│  (Backend)        │   │  (Frontend)       │
│  - FastAPI        │   │  - Nginx          │
│  - Auto-scaling   │   │  - Static files   │
└─────────┬─────────┘   └───────────────────┘
          │
┌─────────▼─────────────────────────────────────┐
│              RDS PostgreSQL                    │
│  - Multi-AZ deployment                         │
│  - Automated backups                           │
│  - Read replicas                               │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│              S3 Bucket                         │
│  - Invoice file storage                        │
│  - Encryption at rest                          │
│  - Lifecycle policies                          │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│         ElastiCache (Redis)                    │
│  - Session storage                             │
│  - Rate limiting                               │
│  - Caching                                     │
└────────────────────────────────────────────────┘
```

**Services**:
- **Compute**: ECS Fargate (serverless containers)
- **Database**: RDS PostgreSQL (Multi-AZ)
- **Storage**: S3 (invoice files)
- **Cache**: ElastiCache Redis
- **CDN**: CloudFront
- **DNS**: Route 53
- **Monitoring**: CloudWatch
- **Secrets**: AWS Secrets Manager

### 7.4 CI/CD Pipeline

**Tools**: GitHub Actions

**Workflow**:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=backend
      - name: Run linting
        run: flake8 backend/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t microcfo:${{ github.sha }} .
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin
          docker push microcfo:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster microcfo --service backend --force-new-deployment
```

### 7.5 Monitoring & Observability

**Metrics**:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connection pool usage
- Cache hit rate

**Logging**:
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized logging (CloudWatch Logs or ELK Stack)

**Alerting**:
- High error rate (> 5%)
- Slow response time (p95 > 2s)
- Database connection failures
- Disk space usage (> 80%)
- SSL certificate expiry (< 30 days)

**Health Checks**:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": await check_database(),
        "redis": await check_redis(),
        "gemini": check_gemini_api()
    }
```


## 8. Performance Optimization

### 8.1 Backend Optimization

**Database Optimization**:
- Indexed columns: user_id, status, created_at
- Composite indexes for common queries
- Connection pooling (max 20 connections)
- Query optimization with EXPLAIN ANALYZE
- Read replicas for heavy read operations

**Caching Strategy**:
```python
# Redis caching for subsidy schemes
@cache(ttl=3600)  # 1 hour
async def get_all_schemes():
    return await scraper.fetch_schemes()

# In-memory caching for legal chunks
@lru_cache(maxsize=1000)
def get_legal_chunk(chunk_id: str):
    return db.query(LegalChunk).filter_by(id=chunk_id).first()
```

**API Response Optimization**:
- Pagination for list endpoints (default: 20 items)
- Field selection (sparse fieldsets)
- Response compression (gzip)
- ETags for conditional requests

**Async Processing**:
- Background tasks for heavy operations
- Celery for distributed task queue
- WebSocket for real-time updates

### 8.2 Frontend Optimization

**Code Splitting**:
```javascript
// Lazy load routes
const Dashboard = lazy(() => import('./pages/Dashboard'));
const DocumentScanner = lazy(() => import('./pages/DocumentScanner'));

// Suspense wrapper
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/scanner" element={<DocumentScanner />} />
  </Routes>
</Suspense>
```

**Asset Optimization**:
- Image compression (WebP format)
- SVG for icons
- Font subsetting
- Tree shaking for unused code
- Minification and bundling

**Performance Metrics**:
- First Contentful Paint (FCP) < 1.5s
- Largest Contentful Paint (LCP) < 2.5s
- Time to Interactive (TTI) < 3.5s
- Cumulative Layout Shift (CLS) < 0.1

### 8.3 AI Service Optimization

**Prompt Optimization**:
- Concise, structured prompts
- JSON-only output format
- Temperature: 0.3 (deterministic)
- Max tokens: 1000 (cost control)

**Retry Strategy**:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(APIError)
)
async def call_gemini_api(prompt: str):
    return await model.generate_content(prompt)
```

**Fallback Mechanism**:
- Mock data when API unavailable
- Cached responses for common queries
- Graceful degradation messages

## 9. Testing Strategy

### 9.1 Unit Testing

**Framework**: pytest

**Coverage Target**: 80%

**Example**:
```python
def test_visual_auditor_parse_response():
    auditor = VisualAuditor()
    response_text = '{"vendor_name": "Test Vendor", "total_amount": 1000}'
    result = auditor._parse_response(response_text)
    assert result.vendor_name == "Test Vendor"
    assert result.total_amount == 1000
```

### 9.2 Integration Testing

**Scope**: API endpoints, database operations, external services

**Example**:
```python
@pytest.mark.asyncio
async def test_invoice_analysis_endpoint(client):
    with open("test_invoice.jpg", "rb") as f:
        response = await client.post(
            "/api/v1/invoices/analyze",
            files={"file": f}
        )
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### 9.3 End-to-End Testing

**Framework**: Playwright

**Scenarios**:
- User registration and login
- Invoice upload and analysis
- Compliance query submission
- Subsidy search
- Negotiation email generation

### 9.4 Performance Testing

**Tool**: Locust

**Scenarios**:
- 100 concurrent users
- 1000 requests/minute
- Sustained load for 30 minutes

**Metrics**:
- Response time percentiles
- Error rate
- Throughput

### 9.5 Security Testing

**Tools**:
- OWASP ZAP (vulnerability scanning)
- Bandit (Python security linting)
- npm audit (dependency vulnerabilities)

**Tests**:
- SQL injection attempts
- XSS attacks
- CSRF attacks
- Authentication bypass
- Authorization escalation

## 10. Disaster Recovery

### 10.1 Backup Strategy

**Database Backups**:
- Automated daily backups (3 AM UTC)
- Retention: 30 days
- Point-in-time recovery: 7 days
- Backup verification: Weekly restore tests

**File Storage Backups**:
- S3 versioning enabled
- Cross-region replication
- Lifecycle policies (archive after 90 days)

### 10.2 Recovery Procedures

**RTO (Recovery Time Objective)**: 4 hours

**RPO (Recovery Point Objective)**: 24 hours

**Recovery Steps**:
1. Identify failure scope
2. Activate backup infrastructure
3. Restore database from latest backup
4. Restore file storage from S3
5. Verify data integrity
6. Switch DNS to backup environment
7. Monitor system health

### 10.3 High Availability

**Database**:
- Multi-AZ deployment
- Automatic failover (< 2 minutes)
- Read replicas for load distribution

**Application**:
- Multi-container deployment
- Auto-scaling (min: 2, max: 10)
- Health checks every 30 seconds
- Automatic container replacement

**Load Balancing**:
- Application Load Balancer
- Health checks on /health endpoint
- Connection draining (30 seconds)

## 11. Future Enhancements

### 11.1 Planned Features

**Phase 3 (Q2 2026)**:
- WhatsApp integration for notifications
- Mobile native apps (iOS, Android)
- Advanced analytics dashboard
- Automated GST return filing

**Phase 4 (Q3 2026)**:
- Multi-language support (Tamil, Telugu, Marathi)
- Banking API integration for cash flow analysis
- Contract analysis with NLP
- Predictive analytics for cash flow forecasting

### 11.2 Technical Improvements

**Architecture**:
- Microservices migration
- Event-driven architecture (Kafka)
- GraphQL API layer
- Service mesh (Istio)

**AI/ML**:
- Custom fraud detection models
- Fine-tuned LLMs for Indian legal context
- Anomaly detection for compliance
- Recommendation engine for subsidies

**Infrastructure**:
- Kubernetes orchestration
- Multi-region deployment
- Edge computing for faster response
- Serverless functions for background tasks

---

**Document Version**: 1.0  
**Last Updated**: February 10, 2026  
**Status**: Approved  
**Owner**: MicroCFO Development Team  
**Reviewers**: Technical Lead, Security Team, Product Manager

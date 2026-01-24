# MicroCFO - Design Document

## Document Information
- **Version**: 2.1.0
- **Last Updated**: January 24, 2026
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
│  │  • Orchestrator (The Brain)                              │  │
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
│  ┌──────────────┐                                              │
│  │   Agent D    │                                              │
│  │  Negotiator  │                                              │
│  └──────────────┘                                              │
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
  - **Orchestration Logic**: Managing document lifecycles and "The Brain" logic

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

### 2.3 Agent C - Subsidy Hunter

#### 2.3.1 Purpose
Discover applicable government subsidies based on sector, turnover, and capital expenditure.

### 2.4 Agent D - Negotiator

#### 2.4.1 Purpose
Generate professional negotiation content (emails, WhatsApp) based on cash flow analysis and historical vendor behavior.

#### 2.4.2 Architecture
```
┌─────────────────────────────────────────────────────────┐
│                      Negotiator                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Router     │  │ Vendor CRM   │  │   Gemini     │ │
│  │   Logic      │→ │ (Memory)     │→ │  3 Flash     │ │
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
- Intent determination (Credit Extension, Payment Chase, Early Payment)
- Strategy selection

**Vendor CRM (The Memory)**
- Uses `VendorProfile` table
- Tracks negotiation "hardness" score
- Stores successful past tactics
- Analyzes average monthly spend

**Content Generator (Gemini 3 Flash)**
- Indian business communication style
- Invoice-specific references
- Tone variations (relationship vs transactional)
- WhatsApp (< 160 chars) and email formats

**Draft-Only Mode (Guardrail)**
- NEVER auto-sends emails
- Always requires user approval
- Prominent disclaimer display
- Audit trail logging

### 2.5 Orchestrator - The Brain

#### 2.5.1 Purpose
Manages complex, multi-step workflows that span multiple agents and persist state over time.

#### 2.5.2 Document Lifecycle Flow
1. **Visual Audit**: Trigger Agent A to scan invoice.
2. **State Persistence**: Create `WorkflowState` entry with "AUDIT_COMPLETE" status.
3. **Decision Logic**:
   - lookup `VendorProfile`.
   - Check if spend > average or if amount > threshold.
   - Decide if negotiation is needed.
4. **Negotiation (Optional)**: Trigger Agent D to draft email if conditions met.
5. **Human Loop**: Wait for user approval.

#### 2.5.3 Data Persistence
- **WorkflowState Table**: Tracks the current step, context data, and history of actions.
- **Audit History**: JSON trail of all automated decisions and agent outputs.

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
      ▲
      │ 1:1 (Optional)
      │
┌──────────────┐      ┌──────────────┐
│WorkflowStates│      │VendorProfiles│
│ (The Brain)  │      │ (The Memory) │
└──────────────┘      └──────────────┘
```

#### 3.1.2 New Table Definitions

**workflow_states** (The Brain's Memory)
```sql
CREATE TABLE workflow_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    status VARCHAR(50),      -- e.g., "AUDIT_COMPLETE", "NEGOTIATION_DRAFTED"
    current_step VARCHAR(100), -- e.g., "waiting_for_user_approval"
    context_data JSONB,      -- Data passed between agents
    history JSONB,           -- Audit trail of AI decisions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**vendor_profiles** (The Memory)
```sql
CREATE TABLE vendor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE,
    average_spend_monthly FLOAT,
    negotiation_hardness_score FLOAT, -- 1-10 scale
    last_negotiation_date TIMESTAMP WITH TIME ZONE,
    successful_tactics TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

*(Existing table definitions for users, invoices, etc. remain unchanged)*

---

## 4. API Design

### 4.1 New Orchestrator Endpoints

#### 4.1.1 Document Lifecycle
```
POST /workflow/process-document-lifecycle
```
**Purpose**: Orchestrates the full flow from invoice scan to negotiation decision.
**Input**: `{ "image_url": "...", "user_id": "..." }`
**Output**: 
```json
{
  "workflow_id": "uuid",
  "audit_result": { ... },
  "negotiation_needed": true,
  "negotiation_draft": { ... }
}
```

### 4.2 Updated Negotiator Endpoints
*(Existing endpoints remain, now utilizing VendorProfile internally)*

---

## 5. Security Architecture
*(Unchanged from v2.0.0)*

## 6. Data Flow Diagrams
*(Unchanged, visual auditor flow feeds into Orchestrator)*

## 7. Deployment Architecture
*(Unchanged)*

## 8. Technology Stack
*(Unchanged)*

## 9. Design Patterns
- **State Pattern**: `WorkflowState` managing the lifecycle of documents.
- **Repository Pattern**: Abstracting `VendorProfile` access.

## 10. Performance Considerations
- **Orchestration Overhead**: Minimal, as Agent calls are the bottleneck.
- **State Management**: Optimized JSONB queries for workflow history.

---

## 11. Conclusion
This updated design document (v2.1.0) incorporates "The Brain" (Orchestrator) and "The Memory" (Vendor Profiles), enabling MicroCFO to not just process individual requests but to maintain state and context across complex, multi-agent workflows.

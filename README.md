# MicroCFO MCP Server

A lightweight Model Context Protocol (MCP) server for AI-powered financial operations with advanced Legal Sentinel capabilities.

## 🚀 Complete Implementation Status

✅ **Agent A - Visual Auditor** (NEW!)
- **Gemini 2.5 Flash Integration**: Real invoice image processing
- **Fraud Detection**: Tampering, handwriting, missing GSTIN detection
- **Line Item Categorization**: Capital Goods, Raw Material, Personal/Entertainment, Service
- **Orchestrator Triggers**: Auto-connects to Agents B & C
- **Conservative CA-Style Auditing**: When in doubt, flag it

✅ **Agent B - Legislative Sentinel** (Structure-Aware RAG)
- **Smart Legal Text Splitting**: CA-logic based chunking
- **Vector Database**: ChromaDB with semantic search
- **Context Filtering**: Turnover-based compliance filtering
- **Real-time Monitoring**: Government website scraping

✅ **Agent C - Subsidy Hunter**
- **Scheme Database**: Government subsidy discovery
- **Benefit Calculation**: Estimated subsidy amounts
- **Sector-Specific**: Textile, Manufacturing, Technology focus

✅ **Agent D - Negotiator** (NEW!)
- **Router Logic**: AI-powered strategy determination (Credit Extension, Payment Chase, Early Payment Offer)
- **Gemini 3 Flash Integration**: Context-aware content generation
- **A/B Testing**: Relationship-focused vs Transactional approaches
- **Multi-format Output**: WhatsApp messages + Formal emails
- **Cash Flow Intelligence**: Decisions based on financial position

## 🎯 Agent A: The Visual Auditor (Complete Implementation)

### Key Features
- **Multimodal Processing**: Gemini 2.5 Flash for invoice image analysis
- **Structured Data Extraction**: Vendor, amounts, dates, GSTIN, line items
- **Fraud Detection**: Tampering, handwriting, inconsistencies
- **Compliance Checking**: ITC eligibility, stale invoices, missing documentation
- **Orchestrator Integration**: Auto-triggers Agents B & C based on content

### Enhanced Invoice Model
```python
class Invoice(BaseModel):
    vendor_name: str
    invoice_date: str
    total_amount: float
    tax_amount: float
    line_items: List[LineItem]  # With category classification
    gstin: Optional[str] = None
    # Auditor fields
    is_handwritten: bool = False
    tampering_detected: bool = False
    compliance_flags: List[str] = []
    confidence_score: float = 1.0
```

### Line Item Categories
- **Capital Goods**: Machinery, equipment, plant, vehicles
- **Raw Material**: Production inputs, components
- **Personal/Entertainment**: Food, alcohol, personal expenses
- **Service**: Consulting, software, maintenance

### Fraud Detection Capabilities
- **Tampering Detection**: Mismatched fonts, blurred numbers, digital manipulation
- **Handwriting Identification**: Reliability scoring for handwritten bills
- **GSTIN Validation**: Tax charged without proper registration
- **Date Staleness**: ITC eligibility for invoices >30 days old
- **Conservative Flagging**: When in doubt, flag for manual review

### Orchestrator Triggers
- **Capital Goods >₹1L**: Auto-triggers Agent C (Subsidy Hunter)
- **Personal Items**: Auto-triggers Agent B (Legal Sentinel) for ITC compliance
- **Proactive Alerts**: Adds subsidy and compliance warnings to invoice response

## 🆕 Agent D: The Negotiator (Complete Implementation)

### Architecture: OpenAI Router + Gemini 3 Flash

#### Phase 1: Router Logic (The Decision Maker)
Smart strategy determination based on financial context:

```python
class NegotiationIntent(str, Enum):
    CREDIT_EXTENSION = "credit_extension"      # Cash flow tight
    PAYMENT_CHASE = "payment_chase"            # Overdue receivables  
    EARLY_PAYMENT_OFFER = "early_payment_offer" # Cash surplus
```

**Decision Logic:**
- **Credit Extension**: When `projected_cash_balance < upcoming_outflows`
- **Payment Chase**: When `invoice_due_date < today` (Overdue)
- **Early Payment Offer**: When `cash_surplus` is high (proactive optimization)

#### Phase 2: Generator Logic (Gemini 3 Flash)
AI-powered content generation with Indian business communication style:

```python
# Context-aware prompts for each intent
"You are the CFO of an Indian MSME. Your goal is to manage cash flow without burning relationships.

Scenario: {intent} for {vendor_name}
Amount: ₹{amount:,.0f}
Style: {tone} (Relationship vs Transactional)

Generate authentic WhatsApp + Email content referencing Invoice #{invoice_id}"
```

#### Phase 3: A/B Testing (The "Novelty" Feature)
Every negotiation generates two variations:
- **Option A (Relationship Focus)**: "We value our long-term partnership..."
- **Option B (Transactional Focus)**: "Please find attached the invoice overdue by 3 days..."

### Complete MCP Tool Implementation

```python
@mcp.tool()
def generate_negotiation_draft(
    counterparty_name: str,
    amount: float,
    transaction_type: str,  # "payable" or "receivable"
    due_date: str,
    current_cash_position: float,
    upcoming_outflows: float = 0,
    invoice_id: str = None
) -> NegotiationDraft
```

### Business Scenarios

#### Scenario 1: Cash Flow Crunch (Textile MSME)
```python
# Input: ₹8.5L due, only ₹4L available, ₹3.5L outflows
# Router: CREDIT_EXTENSION
# Output: "Hi Gujarat Cotton Mills, need 15 days for Invoice #INV-001 payment. 
#          Cash flow timing issue. Thanks for understanding! 🙏"
```

#### Scenario 2: Overdue Payment Chase (IT Services)
```python
# Input: ₹4.8L overdue by 15 days
# Router: PAYMENT_CHASE  
# Output: "Hi MegaCorp Technologies, gentle reminder for Invoice #INV-002 payment.
#          Let us know if any clarification needed. Thanks! 😊"
```

#### Scenario 3: Early Payment Opportunity (Manufacturing)
```python
# Input: ₹6.5L due, ₹32L available (strong position)
# Router: EARLY_PAYMENT_OFFER
# Output: "Hi Premium Steel Suppliers, can offer early payment for Invoice #INV-003
#          with 2% discount. Win-win for both! Let me know 😊"
```

### Key Features
- **Conservative Financial Logic**: Protects cash flow while maintaining relationships
- **Indian Business Context**: Appropriate tone and communication style
- **Multi-format Output**: WhatsApp (160 chars) + Formal email versions
- **Invoice-specific References**: Uses actual invoice numbers for authenticity
- **Fallback Mode**: Works without API keys using template-based generation

## 🆕 Agent B: The Legislative Sentinel (Structure-Aware RAG)

### Features
- **Smart Legal Text Splitting**: CA-logic based chunking that preserves legal structure
- **Metadata Extraction**: Automatic tagging of turnover thresholds, sectors, dates
- **Vector Database**: ChromaDB with semantic search capabilities
- **Context Filtering**: Filters out irrelevant laws based on user profile
- **Real-time Monitoring**: Automated scraping of government websites for new notifications

### Architecture
```
Legal Sentinel System
├── legal_ingestion.py (Phase 1: Structure-Aware Ingestion)
│   ├── LegalTextSplitter (CA-Logic splitting)
│   ├── Metadata extraction (turnover, sector, dates)
│   └── Smart chunking (preserves provisos and sub-clauses)
├── vector_database.py (Phase 2: Vector Storage)
│   ├── ChromaDB integration
│   ├── Semantic search with sentence-transformers
│   └── Hybrid search (keyword + semantic)
├── server.py (Phase 3: MCP Tool Implementation)
│   ├── Context fetching from user profile
│   ├── Turnover-based filtering
│   └── Conservative CA-style responses
└── sentinel_monitor.py (Phase 4: Real-time Alerts)
    ├── Government website monitoring
    ├── User relevance checking
    └── WhatsApp alert system
```

## Quick Start

### 1. Environment Setup
```bash
python setup.py
```

### 2. Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Unix/Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
```bash
# Set your Gemini API key for Agent A (Visual Auditor)
set GEMINI_API_KEY=your_gemini_api_key_here
set GOOGLE_API_KEY=your_gemini_api_key_here

# Get free API key from: https://makersuite.google.com/app/apikey
```

### 5. Initialize Legal Database
```bash
python setup_legal_db.py
```

### 6. Run Tests
```bash
# Test Agent A (Visual Auditor)
python test_gemini_direct.py
python final_agent_a_test.py

# Test Agent B (Legal Sentinel)
python test_legal_sentinel.py

# Test Agent D (Negotiator)
python test_agent_d_simple.py
python demo_agent_d_negotiator.py

# Test complete demo
python demo_complete_agent_a.py
```

### 7. Start MCP Server
```bash
python server.py
```

### 8. Test with MCP Inspector
```bash
mcp dev server.py
```

## Testing Agent A - Visual Auditor

### Process Real Invoice Images
```python
from server import scan_invoice_document

# Process local image
result = scan_invoice_document('invoice.jpg')

# Process URL
result = scan_invoice_document('https://example.com/invoice.png')

# Process base64 data
result = scan_invoice_document('data:image/jpeg;base64,/9j/4AAQ...')

# Use mock data for testing
result = scan_invoice_document('test', use_mock=True)
```

### Example Scenarios

#### Scenario 1: Textile Machinery Purchase (₹11.8L)
```python
# Invoice contains: Rapier Loom Machine (₹8L) + Warp Feeder (₹1.5L)
# Agent A detects: Capital Goods >₹1L
# Auto-triggers: Agent C (Subsidy Hunter)
# Result: "TUFS Scheme - Up to 25% subsidy (₹2.37L estimated benefit)"
```

#### Scenario 2: Restaurant Bill (₹8.5K)
```python
# Invoice contains: Business Lunch + Alcoholic Beverages
# Agent A detects: Personal/Entertainment items
# Auto-triggers: Agent B (Legal Sentinel)
# Result: "ITC WARNING: Section 17(5) - Food & alcohol not eligible"
```

#### Scenario 3: Suspicious Invoice
```python
# Agent A detects: Tampering, Missing GSTIN, Handwritten, Stale (>30 days)
# Flags: "CRITICAL: Manual verification required"
# Recommendation: "Do not claim ITC without proper documentation"
```

## Testing the Enhanced Legal Sentinel

### Smart Legal Queries
```python
# Test structure-aware responses
check_compliance_law("Can I claim ITC on office supplies if my turnover is 3 crores?")
# Response: "EXEMPT: Your turnover (< 5Cr) is below the 5 crore threshold..."

check_compliance_law("Section 17(5) blocked credits")
# Response: Finds exact section with metadata

check_compliance_law("What are the penalties for late GST filing?")
# Response: Structure-aware search finds Section 47 with specific penalties
```

### Real-time Monitoring
```bash
# Test monitoring once
python sentinel_monitor.py run-once

# Start continuous monitoring
python sentinel_monitor.py
```

## Legal Database Features

### 1. Structure-Aware Text Splitting
- Recognizes `Section X`, `Rule Y`, `Notification No.` patterns
- Preserves `Provided that...` clauses with parent sections
- Maintains sub-clause `(a), (b), (c)` relationships

### 2. Intelligent Metadata Extraction
- **Turnover Thresholds**: "turnover exceeds 5 crore" → 50000000
- **Sector Tags**: Textile, Manufacturing, Technology, Works Contract
- **Effective Dates**: Automatic date extraction from notifications
- **Law Types**: GST, Income Tax, Companies Act classification

### 3. Context-Aware Filtering
- Filters laws based on user's turnover tier
- Sector-specific relevance checking
- Conservative CA-style interpretations

### 4. Hybrid Search Capabilities
- **Keyword Search**: Direct section number lookup
- **Semantic Search**: Concept-based matching
- **Combined Search**: Best of both approaches

## Real-time Legal Monitoring

### Government Sources Monitored
- CBIC (GST notifications)
- MCA (Companies Act updates)
- Income Tax Department notifications

### Alert System
- Automatic relevance checking against user profiles
- WhatsApp Business API integration (configurable)
- Daily monitoring schedule

## File Structure

```
MicroCFO-MCP-Server/
├── server.py                    # Main MCP server with all 4 agents
├── legal_ingestion.py           # Phase 1: Smart legal text processing
├── vector_database.py           # Phase 2: Vector storage & search
├── sentinel_monitor.py          # Phase 4: Real-time monitoring
├── setup_legal_db.py            # Database initialization
├── test_legal_sentinel.py       # Legal Sentinel test suite
├── requirements.txt             # Dependencies (includes google-generativeai)
├── setup.py                     # Environment setup
├── README.md                    # This file
│
├── Agent A Tests & Demos:
├── test_gemini_direct.py        # Direct Gemini 2.5 Flash test
├── final_agent_a_test.py        # Complete Agent A integration test
├── demo_complete_agent_a.py     # Full workflow demonstration
├── test_visual_auditor.py       # Comprehensive test suite
├── demo_visual_auditor.py       # Interactive demo script
│
├── Agent D Tests & Demos:
├── test_agent_d_simple.py       # Direct function testing
├── test_agent_d_negotiator.py   # Comprehensive test suite
└── demo_agent_d_negotiator.py   # Interactive negotiation demo
```

## 🎯 Complete MicroCFO Workflow

### 1. Invoice Processing (Agent A)
```
📸 User uploads invoice image
    ↓
🔍 Gemini 2.5 Flash processes image
    ↓
📊 Structured data extracted (vendor, amounts, items)
    ↓
🕵️ Fraud detection (tampering, handwriting, GSTIN)
    ↓
⚠️ Compliance flags (ITC eligibility, stale invoices)
    ↓
🎯 Orchestrator triggers other agents
```

### 2. Automatic Triggers
```
Capital Goods >₹1L → Agent C (Subsidy Hunter)
Personal Items → Agent B (Legal Sentinel)
Compliance Issues → Conservative warnings
```

### 3. Integrated Response
```
📄 Structured invoice data
🚨 Fraud alerts and compliance warnings
🎯 Proactive subsidy opportunities
📋 Legal compliance guidance
💼 Professional communication templates
```

## Production Deployment

### MCP Server Integration
```python
# Your AI assistant can now call:
scan_invoice_document(image_url)           # Agent A - Visual processing
check_compliance_law(query, context)      # Agent B - Legal guidance  
find_applicable_subsidies(sector, amount) # Agent C - Subsidy discovery
generate_negotiation_draft(counterparty, amount, type, due_date, cash_position) # Agent D - Negotiation
```

### API Capabilities
- **Real-time invoice processing** with Gemini 2.5 Flash
- **Structure-aware legal RAG** with ChromaDB
- **Proactive subsidy discovery** with benefit calculation
- **AI-powered negotiation** with cash flow intelligence
- **Conservative CA-style compliance** checking
- **Automated orchestration** between agents

## 🚀 Ready for Production!

✅ **Agent A**: Gemini 2.5 Flash vision processing with fraud detection  
✅ **Agent B**: Structure-aware legal RAG with turnover filtering  
✅ **Agent C**: Subsidy discovery with benefit calculation  
✅ **Agent D**: Professional communication generation  
✅ **Orchestrator**: Automatic agent triggers and workflow  
✅ **Conservative Approach**: CA-style risk assessment and flagging  

The MicroCFO MCP Server is now a complete autonomous CFO assistant ready for integration with any AI system!
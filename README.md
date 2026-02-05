# MicroCFO

AI-powered financial compliance platform for Indian MSMEs, featuring automated GST reconciliation, legal compliance monitoring, subsidy discovery, and intelligent vendor negotiations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🚀 Key Features

✅ **Agent A - Visual Auditor**
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

✅ **Agent D - Negotiator**
- **Router Logic**: AI-powered strategy determination
- **Gemini 3 Flash Integration**: Context-aware content generation
- **A/B Testing**: Relationship-focused vs Transactional approaches
- **Multi-format Output**: Telegram messages + Formal emails
- **Cash Flow Intelligence**: Decisions based on financial position

✅ **Phase 4: Business Logic & Integration** (NEW!)
- **ERP Adapters**: Export to Tally, Zoho Books, CSV, JSON
- **User Onboarding**: Industry and turnover tier selection
- **Contextual Filtering**: Personalized compliance and subsidies
- **API-First Design**: Production-ready integrations

✅ **Security & Compliance** (NEW!)
- **Data Encryption**: AES-256 encryption at rest
- **Audit Trails**: Comprehensive logging of all actions
- **Legal Disclaimers**: Prominent AI limitation warnings
- **Guardrails**: Draft-only mode, verification required

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

Generate authentic Telegram + Email content referencing Invoice #{invoice_id}"
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
- **Multi-format Output**: Telegram (160 chars) + Formal email versions
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
    └── Telegram alert system
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

### 4. Configure API Keys (IMPORTANT - Security)

**⚠️ NEVER commit API keys to git!**

Create a `.env` file from the template:
```bash
cp .env.example .env
```

Edit `.env` and add your actual API keys:
```bash
# Get your Gemini API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_actual_gemini_key_here

# Or use OpenRouter: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_actual_openrouter_key_here
```

**Alternative: Set environment variables directly**
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your_key_here"

# Unix/Linux/Mac
export GEMINI_API_KEY="your_key_here"
```

**📖 See [SECURITY.md](SECURITY.md) for complete security guidelines**

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

## 🆕 Legal Data Seeding System

The Legal Data Seeding System automates the acquisition and ingestion of foundational Indian legal documents into the MicroCFO vector database. This system establishes the "Base Layer" that powers the Legal Sentinel (Agent B) capabilities.

### Overview

The seeding system consists of three main components:

1. **Seed Downloader** (`scripts/seed_downloader.py`): Downloads legal documents from official government sources
2. **Enhanced Legal Ingestion** (`legal_ingestion.py`): Processes PDFs with structure-aware chunking
3. **Seed Data Processor** (`scripts/seed_data.py`): Orchestrates the end-to-end pipeline

### Quick Start - Seeding the Database

#### Step 1: Download Legal Documents
```bash
# Download all configured legal documents from government sources
python scripts/seed_downloader.py

# Or specify custom output directory
python scripts/seed_downloader.py --output-dir ./my_legal_docs/
```

**What it downloads:**
- ✅ CGST Act 2017 (from CBIC)
- ✅ IGST Act 2017 (from CBIC)
- ✅ Income Tax Act 1961 (from IncomeTaxIndia)
- ✅ Companies Act 2013 (from India Code)
- ✅ PLI Textiles Guidelines (from Texprocil)

**Features:**
- Idempotent downloads (skips existing files)
- SSL error recovery for government sites
- Network timeout handling with exponential backoff
- Comprehensive progress reporting

#### Step 2: Process and Populate Database
```bash
# Process downloaded PDFs and populate vector database
python scripts/seed_data.py

# Or specify custom paths
python scripts/seed_data.py --data-dir ./my_legal_docs/ --db-path ./my_legal_db/
```

**What it does:**
1. Scans for PDF files in the data directory
2. Auto-detects law type from filename
3. Extracts text with page-by-page progress reporting
4. Cleans text (removes headers, footers, page numbers)
5. Splits into structure-aware chunks
6. Extracts metadata (turnover, sector, dates)
7. Generates embeddings using sentence transformers
8. Stores chunks in ChromaDB vector database

**Features:**
- Idempotent processing (skips already-processed documents)
- Duplicate detection using file hashes
- Detailed progress reporting
- Comprehensive error handling
- Processing statistics and summary report

### Expected Output

#### Download Phase
```
INFO - Starting download of 5 documents
INFO - Downloading: Central Goods and Services Tax Act 2017
INFO - URL: https://cbic-gst.gov.in/pdf/cgst-act.pdf
INFO - Successfully downloaded: CGST_Act_2017.pdf (2458624 bytes)
INFO - Downloading: Integrated Goods and Services Tax Act 2017
INFO - Successfully downloaded: IGST_Act_2017.pdf (1234567 bytes)
...
============================================================
Download Summary:
  Total documents: 5
  Successful: 5
  Failed: 0
============================================================
```

#### Processing Phase
```
INFO - SeedDataProcessor initializing...
INFO - ✓ Legal Document Processor initialized successfully
INFO - ✓ Vector Database initialized successfully
INFO - Starting batch document processing
INFO - Found 5 PDF files
[1/5] (20.0%) Document Processing: CGST_Act_2017.pdf
INFO - Processing: CGST_Act_2017.pdf
INFO -   Detected law type: GST
INFO -   Extracting text from 174 pages...
INFO -     Processing page 1/174
INFO -     Processing page 2/174
...
INFO -   ✓ Text extraction complete (174 pages processed)
INFO -   Cleaning extracted text...
INFO -   ✓ Text cleaning complete
INFO -   Chunking text with structure-aware splitting...
INFO -   ✓ Created 245 legal chunks
INFO -   Storing chunks in vector database...
INFO -     Storing chunks 1-25/245 (10.2%)
INFO -     Storing chunks 26-50/245 (20.4%)
...
INFO -   ✓ Storage complete (100%)
INFO -   ✓ Completed in 45.23s

============================================================
LEGAL DATA SEEDING REPORT
============================================================

Summary:
  Total Documents:     5
  Successful:          5
  Failed:              0
  Total Chunks:        1,247
  Total Time:          234.56s

Document Details:
------------------------------------------------------------
  ✓ SUCCESS | CGST_Act_2017.pdf | GST | 245 chunks | 45.23s
  ✓ SUCCESS | IGST_Act_2017.pdf | GST | 198 chunks | 38.12s
  ✓ SUCCESS | Income_Tax_Act_1961.pdf | Income Tax | 512 chunks | 98.45s
  ✓ SUCCESS | Companies_Act_2013.pdf | Corporate Law | 234 chunks | 42.67s
  ✓ SUCCESS | PLI_Textiles_Guidelines.pdf | Subsidy Scheme | 58 chunks | 10.09s
------------------------------------------------------------
Report generated at: 2024-01-15T14:30:45.123456
============================================================
```

### Troubleshooting

#### SSL Certificate Errors
Government websites often have SSL certificate issues. The downloader automatically retries with SSL verification disabled:

```
WARNING - SSL verification failed for https://cbic-gst.gov.in/pdf/cgst-act.pdf, retrying without verification
```

This is expected and handled automatically. The system logs a warning but continues the download.

#### Network Timeouts
If downloads timeout due to slow government servers, the system retries with exponential backoff:

```
WARNING - Timeout on attempt 1/3, retrying in 1s
WARNING - Timeout on attempt 2/3, retrying in 2s
```

The system will retry up to 3 times before giving up on a particular document.

#### Empty or Malformed PDFs
If a PDF cannot be processed or produces no text:

```
WARNING - Empty content after extraction and cleaning for CGST_Act_2017.pdf, skipping document
```

Check the PDF file manually. Some government PDFs may be scanned images without OCR text.

#### Database Initialization Errors
If the vector database fails to initialize:

```
ERROR - Failed to initialize Vector Database at './legal_db/': [Errno 13] Permission denied
Common causes:
  - ChromaDB not installed (pip install chromadb)
  - Sentence transformers not installed (pip install sentence-transformers)
  - Insufficient disk space or permissions
  - Corrupted database files (try deleting the legal_db directory)
```

Follow the suggested fixes:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check disk space: `df -h` (Unix) or `dir` (Windows)
3. Check permissions: Ensure write access to the project directory
4. If corrupted, delete and recreate: `rm -rf legal_db/` then re-run

#### Re-running the Seeding Process
The seeding system is **idempotent** - you can safely re-run it multiple times:

```bash
# Re-running downloads will skip existing files
python scripts/seed_downloader.py
# Output: "File already exists, skipping: CGST_Act_2017.pdf"

# Re-running processing will skip already-processed documents
python scripts/seed_data.py
# Output: "Document CGST_Act_2017.pdf already processed with matching hash"
```

To force re-processing (e.g., after updating the ingestion logic):
1. Delete the vector database: `rm -rf legal_db/`
2. Re-run the processor: `python scripts/seed_data.py`

### Advanced Configuration

#### Adding New Legal Sources
Edit `scripts/seed_downloader.py` and add to the `LEGAL_SOURCES` list:

```python
LEGAL_SOURCES = [
    # ... existing sources ...
    LegalDocumentSource(
        url="https://example.gov.in/new-act.pdf",
        filename="New_Act_2024.pdf",
        description="New Act 2024",
        law_type="GST"  # or "Income Tax", "Corporate Law", "Subsidy Scheme"
    )
]
```

#### Customizing Law Type Detection
The system auto-detects law types from filenames. To customize, edit `legal_ingestion.py`:

```python
def detect_law_type_from_filename(filename: str) -> str:
    # Add your custom patterns here
    if "CUSTOM" in filename_normalized:
        return "Custom Law Type"
    # ... existing patterns ...
```

#### Customizing Metadata Extraction
To extract additional metadata, edit `legal_ingestion.py`:

```python
def extract_metadata_from_text(text: str, law_type: str = "GST") -> Dict[str, Optional[any]]:
    metadata = {
        'turnover_threshold': None,
        'sector_tag': None,
        'effective_date': None,
        'custom_field': None  # Add your custom field
    }
    # Add extraction logic for custom_field
    # ...
```

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Legal Data Seeding System                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   1. Seed Downloader                    │
        │   (scripts/seed_downloader.py)          │
        │                                         │
        │   • Downloads from government sources   │
        │   • SSL error recovery                  │
        │   • Network timeout handling            │
        │   • Idempotent operations               │
        └─────────────────────────────────────────┘
                              │
                              ▼ PDFs saved to ./data/initial_acts/
                              │
        ┌─────────────────────────────────────────┐
        │   2. Seed Data Processor                │
        │   (scripts/seed_data.py)                │
        │                                         │
        │   • Orchestrates processing pipeline    │
        │   • Duplicate detection                 │
        │   • Progress tracking                   │
        │   • Error handling                      │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   3. Legal Ingestion Pipeline           │
        │   (legal_ingestion.py)                  │
        │                                         │
        │   • Auto-detect law type                │
        │   • Extract & clean text                │
        │   • Structure-aware chunking            │
        │   • Metadata extraction                 │
        └─────────────────────────────────────────┘
                              │
                              ▼ Legal chunks with metadata
                              │
        ┌─────────────────────────────────────────┐
        │   4. Vector Database                    │
        │   (vector_database.py)                  │
        │                                         │
        │   • Generate embeddings                 │
        │   • Store in ChromaDB                   │
        │   • Create search indices               │
        │   • Enable semantic search              │
        └─────────────────────────────────────────┘
                              │
                              ▼ Populated vector database
                              │
        ┌─────────────────────────────────────────┐
        │   5. Legal Sentinel (Agent B)           │
        │   (server.py)                           │
        │                                         │
        │   • Query legal database                │
        │   • Context-aware filtering             │
        │   • Conservative CA responses           │
        └─────────────────────────────────────────┘
```

### Data Flow

1. **Download Phase**: Fetch PDFs from official government URLs
2. **Processing Phase**: Extract text, clean, and chunk with structure awareness
3. **Chunking Phase**: Create LegalChunk objects with metadata
4. **Storage Phase**: Generate embeddings and store in ChromaDB
5. **Query Phase**: Legal Sentinel retrieves relevant chunks for user queries

### Key Features

#### Idempotent Operations
- **Download**: Skips files that already exist
- **Processing**: Detects already-processed documents using file hashes
- **Safe Re-execution**: Can re-run the entire pipeline without duplicates

#### Robust Error Handling
- **SSL Errors**: Automatic retry with verification disabled
- **Network Timeouts**: Exponential backoff retry (1s, 2s, 4s)
- **Malformed PDFs**: Graceful handling with detailed error messages
- **Page Extraction Failures**: Continues processing remaining pages

#### Progress Reporting
- **Download Progress**: File-by-file status with sizes
- **Page Progress**: Page-by-page extraction reporting
- **Chunk Progress**: Number of chunks created per document
- **Storage Progress**: Percentage-based storage progress
- **Summary Reports**: Comprehensive statistics at completion

#### Metadata Extraction
- **Turnover Thresholds**: Extracts "5 crore", "50 crore" → numeric rupees
- **Sector Tags**: Identifies Textile, Manufacturing, Technology, Trading
- **Effective Dates**: Extracts dates like "w.e.f. 01-04-2023" → ISO format
- **Section Numbers**: Preserves legal section identifiers
- **Chunk Types**: Classifies as main, proviso, or sub_clause

### File Locations

```
MicroCFO-MCP-Server/
├── scripts/
│   ├── seed_downloader.py      # Download legal documents
│   └── seed_data.py            # Process and populate database
├── data/
│   └── initial_acts/           # Downloaded PDF files (created automatically)
│       ├── CGST_Act_2017.pdf
│       ├── IGST_Act_2017.pdf
│       ├── Income_Tax_Act_1961.pdf
│       ├── Companies_Act_2013.pdf
│       └── PLI_Textiles_Guidelines.pdf
├── legal_db/                   # Vector database storage (created automatically)
│   ├── chroma.sqlite3          # ChromaDB database
│   └── embeddings/             # Vector embeddings
├── legal_ingestion.py          # Enhanced with seeding support
└── vector_database.py          # Vector database operations
```

### Integration with Legal Sentinel

Once the database is seeded, the Legal Sentinel (Agent B) automatically benefits from the expanded base layer:

```python
# Query the seeded database
result = check_compliance_law(
    "What are the ITC eligibility rules for capital goods?",
    user_context={"turnover": 30000000, "sector": "Manufacturing"}
)

# The system will:
# 1. Search the seeded legal chunks
# 2. Filter by turnover (3 crore < 5 crore threshold)
# 3. Apply sector-specific relevance
# 4. Return structure-aware legal guidance
```

### Performance Considerations

- **First Run**: Initial seeding takes 3-5 minutes for all 5 documents
- **Embedding Generation**: Most time-consuming step (sentence transformers)
- **Subsequent Runs**: Idempotent operations make re-runs very fast
- **Database Size**: Expect ~50-100 MB for the complete legal database
- **Memory Usage**: Peak ~2 GB during embedding generation

### Best Practices

1. **Run seeding on a stable network connection** - Government sites can be slow
2. **Ensure sufficient disk space** - At least 500 MB free
3. **Don't interrupt processing** - Let it complete for proper metadata storage
4. **Check the summary report** - Verify all documents processed successfully
5. **Test queries after seeding** - Ensure Legal Sentinel returns relevant results

### Next Steps After Seeding

Once the database is seeded, you can:

1. **Test Legal Sentinel queries**: `python test_legal_sentinel.py`
2. **Start the MCP server**: `python server.py`
3. **Enable real-time monitoring**: `python sentinel_monitor.py`
4. **Query via API**: Use the `check_compliance_law` tool

The Legal Data Seeding System ensures your MicroCFO instance has a comprehensive, up-to-date foundation of Indian legal knowledge for accurate compliance guidance!

## Real-time Legal Monitoring

### Government Sources Monitored
- CBIC (GST notifications)
- MCA (Companies Act updates)
- Income Tax Department notifications

### Alert System
- Automatic relevance checking against user profiles
- Telegram Bot API integration (configurable)
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

## 🆕 Phase 4: Business Logic & Integration

### ERP Adapters
Export invoices directly to your accounting system:

**Supported Formats:**
- **Tally ERP 9 / Tally Prime**: XML (single) and CSV (batch)
- **Zoho Books**: JSON API payload
- **Standard CSV**: For Excel and generic accounting software
- **JSON**: Complete data export for custom integrations

**Usage:**
```bash
# Export to Tally CSV
curl -X POST http://localhost:8000/api/v1/erp-export/export \
  -H "Content-Type: application/json" \
  -d '{"invoice_ids": ["inv-001"], "format": "tally_csv"}'

# Get supported formats
curl http://localhost:8000/api/v1/erp-export/formats
```

### User Onboarding
Capture user context for personalized experience:

**12 Industry Types:**
- Textile & Apparel, Manufacturing, Technology & IT
- Trading, Services, Retail, Construction
- Healthcare, Education, Hospitality, Agriculture, Other

**4 Turnover Tiers:**
- **Micro**: < ₹5 Crore (Composition scheme eligible)
- **Small**: ₹5-20 Crore (MSME benefits)
- **Medium**: ₹20-50 Crore (PLI schemes)
- **Large**: > ₹50 Crore (Full compliance)

**Benefits:**
- Agent B filters legal compliance by turnover tier
- Agent C shows industry-specific subsidies
- Targeted recommendations and alerts

**Usage:**
```bash
# Start onboarding
curl -X POST http://localhost:8000/api/v1/onboarding/start

# Get industries
curl http://localhost:8000/api/v1/onboarding/industries

# Submit industry selection
curl -X POST http://localhost:8000/api/v1/onboarding/step \
  -H "Content-Type: application/json" \
  -d '{"step": "industry_selection", "data": {"industry_type": "textile"}}'
```

## 🔒 Security & Compliance

### Data Encryption
- **At Rest**: AES-256 encryption for sensitive database columns
- **In Transit**: HTTPS/TLS for all API communication
- **S3 Storage**: Server-side encryption (SSE-S3/SSE-KMS)
- **Key Management**: Secure key storage with rotation support

### Audit Trails
- **Comprehensive Logging**: Who, What, When, Where (IP), How
- **30+ Action Types**: All operations tracked
- **Query & Export**: API endpoints for audit log access
- **Retention**: Configurable retention policies

### Legal Disclaimers
- **Prominent Warnings**: "AI assistant, not a chartered accountant"
- **Specific Disclaimers**: Legal, financial, tax, negotiation, invoice, subsidy
- **Guardrails**: Draft-only mode, verification required, no auto-send
- **User Acceptance**: Session-based disclaimer tracking

### Guardrails
- **Negotiator**: NEVER auto-sends emails (draft-only mode enforced)
- **Invoice Processing**: Verification required, no auto-approval
- **Legal Queries**: No legal advice, always recommend professionals
- **High-Amount Flagging**: Transactions over ₹50,000 flagged

## 🚀 Ready for Production!

✅ **Agent A**: Gemini 2.5 Flash vision processing with fraud detection  
✅ **Agent B**: Structure-aware legal RAG with turnover filtering  
✅ **Agent C**: Subsidy discovery with benefit calculation  
✅ **Agent D**: Professional communication generation  
✅ **Orchestrator**: Automatic agent triggers and workflow  
✅ **ERP Integration**: Export to Tally, Zoho Books, CSV, JSON  
✅ **User Onboarding**: Industry and turnover tier selection  
✅ **Security**: Encryption, audit trails, legal disclaimers  
✅ **Compliance**: Guardrails, verification, professional recommendations  

The MicroCFO MCP Server is now a complete, production-ready autonomous CFO assistant with enterprise-grade security and ERP connectivity!
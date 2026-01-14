# Project Structure & Organization

## Root Directory Layout

```
MicroCFO-MCP-Server/
├── server.py                 # Main MCP server with tool endpoints
├── legal_ingestion.py        # Phase 1: Structure-aware legal text processing
├── vector_database.py        # Phase 2: Vector storage & semantic search
├── sentinel_monitor.py       # Phase 4: Real-time legal monitoring
├── setup_legal_db.py         # Database initialization with sample data
├── test_legal_sentinel.py    # Comprehensive test suite
├── requirements.txt          # Python dependencies
├── setup.py                  # Environment setup automation
├── README.md                 # Project documentation
├── .kiro/                    # Kiro IDE configuration
│   └── steering/             # AI assistant guidance documents
├── .vscode/                  # VS Code configuration
├── venv/                     # Python virtual environment
└── legal_db/                 # ChromaDB vector database storage (created at runtime)
```

## Core Module Responsibilities

### server.py - MCP Server Hub
- **Primary Role**: Central MCP server with all tool endpoints
- **Key Components**:
  - Pydantic models (Invoice, LegalRisk, UserProfile)
  - Tool endpoints for 4 agents (A, B, C, D)
  - Resource endpoints for user context
  - Integration with vector database for legal queries

### legal_ingestion.py - Document Processing Engine
- **Primary Role**: Structure-aware legal document processing
- **Key Components**:
  - `LegalTextSplitter`: CA-logic based text chunking
  - `LegalDocumentProcessor`: PDF and text file processing
  - `LegalChunk`: Data structure with metadata
  - Metadata extraction (turnover thresholds, sectors, dates)

### vector_database.py - Search & Storage Layer
- **Primary Role**: Vector database operations and search
- **Key Components**:
  - `LegalVectorDB`: ChromaDB wrapper with legal-specific features
  - Semantic search with sentence transformers
  - Keyword search for section numbers
  - Hybrid search combining both approaches
  - Context-aware filtering based on user profiles

### sentinel_monitor.py - Monitoring & Alerting System
- **Primary Role**: Real-time legal update monitoring
- **Key Components**:
  - `LegalSentinel`: Main monitoring orchestrator
  - Government website scrapers (CBIC, MCA, Income Tax)
  - User relevance checking algorithms
  - WhatsApp alert system integration
  - Scheduled monitoring routines

## Support Files

### setup_legal_db.py - Database Initialization
- Populates vector database with sample legal content
- Creates test data for GST Act and Income Tax Act
- Validates search functionality
- Provides database statistics

### test_legal_sentinel.py - Test Suite
- Comprehensive testing of all components
- Text splitter validation
- Vector database operations testing
- MCP server integration tests
- Monitoring system validation

### setup.py - Environment Automation
- Virtual environment creation
- Dependency installation
- Cross-platform compatibility (Windows/Unix)

## Runtime Directories

### legal_db/ - Vector Database Storage
- **Created by**: ChromaDB during first run
- **Contains**: Vector embeddings, metadata, seen notifications
- **Structure**:
  ```
  legal_db/
  ├── chroma.sqlite3           # ChromaDB database
  ├── embeddings/              # Vector embeddings storage
  └── seen_notifications.json  # Tracking processed notifications
  ```

### venv/ - Python Virtual Environment
- **Created by**: setup.py or manual python -m venv
- **Contains**: Isolated Python dependencies
- **Platform-specific activation scripts**

## Configuration Patterns

### Pydantic Models (server.py)
- `Invoice`: Structured invoice data with optional fields
- `LegalRisk`: Risk assessment with enum-based levels
- `UserProfile`: Business context for filtering
- `RiskLevel`: Enum for LOW/MEDIUM/HIGH risk classification

### Legal Document Structure Recognition
- **Section Pattern**: `Section X` with sub-sections
- **Rule Pattern**: `Rule Y` with clauses
- **Proviso Pattern**: `Provided that...` clauses
- **Sub-clause Pattern**: `(a), (b), (c)` enumeration

### Metadata Schema
- `law_type`: GST, Income Tax, Companies Act
- `section_number`: Legal section identifier
- `turnover_threshold`: Numeric threshold in rupees
- `sector_tag`: Industry classification
- `effective_date`: ISO date format
- `chunk_type`: main, proviso, sub_clause

## Development Workflow

### Phase-based Implementation
- **Phase 1**: Foundation & text processing (legal_ingestion.py)
- **Phase 2**: Vector database & search (vector_database.py)
- **Phase 3**: MCP tool implementation (server.py)
- **Phase 4**: Real-time monitoring (sentinel_monitor.py)

### Testing Strategy
- Unit tests for individual components
- Integration tests for MCP server
- End-to-end tests for complete workflows
- Mock data for external dependencies

### Deployment Considerations
- Single-file MCP server for easy deployment
- Persistent vector database storage
- Configurable monitoring schedules
- Environment-specific configurations
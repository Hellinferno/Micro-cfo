# Technology Stack & Build System

## Core Technologies

### Python Ecosystem
- **Python 3.7+**: Main runtime environment
- **FastMCP**: Model Context Protocol server framework
- **Pydantic**: Data validation and schema definitions
- **HTTPx**: Async HTTP client for web requests

### AI/ML Stack
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: Text embeddings (`all-MiniLM-L6-v2` model)
- **PyTorch**: Deep learning framework (dependency of sentence-transformers)

### Document Processing
- **PyPDF2**: PDF text extraction
- **BeautifulSoup4**: HTML parsing for web scraping
- **lxml**: XML/HTML parser backend

### Automation & Monitoring
- **Schedule**: Task scheduling for monitoring routines
- **Requests**: HTTP library for web scraping

## Environment Setup

### Virtual Environment
```bash
# Create and activate virtual environment
python setup.py

# Manual activation
# Windows
venv\Scripts\activate
# Unix/Linux/Mac
source venv/bin/activate
```

### Dependencies Installation
```bash
pip install -r requirements.txt
```

## Common Commands

### Database Setup
```bash
# Initialize legal database with sample content
python setup_legal_db.py
```

### Testing
```bash
# Run comprehensive test suite
python test_legal_sentinel.py
```

### Server Operations
```bash
# Start MCP server
python server.py

# Test with MCP Inspector
mcp dev server.py
```

### Monitoring
```bash
# Run monitoring once (testing)
python sentinel_monitor.py run-once

# Start continuous monitoring service
python sentinel_monitor.py
```

## Architecture Patterns

### MCP Server Pattern
- Tool endpoints decorated with `@mcp.tool()`
- Resource endpoints with `@mcp.resource()`
- Pydantic models for structured data exchange
- JSON serialization for all responses

### Vector Database Pattern
- Chunked document storage with metadata
- Hybrid search (keyword + semantic)
- Context-aware filtering based on user profiles
- Persistent storage with ChromaDB

### Legal Document Processing
- Structure-aware text splitting (preserves sections, provisos, sub-clauses)
- Metadata extraction (turnover thresholds, sectors, dates)
- CA-logic based chunking for legal context preservation

### Monitoring & Alerting
- Scheduled web scraping of government sources
- User relevance checking based on business profiles
- WhatsApp Business API integration (configurable)

## Development Guidelines

### Code Organization
- Single-responsibility modules (ingestion, vector_db, monitoring)
- Centralized server.py for MCP endpoints
- Separate test files with comprehensive coverage
- Setup scripts for environment and database initialization

### Error Handling
- Graceful fallbacks when vector DB unavailable
- Conservative legal interpretations on errors
- Comprehensive logging for monitoring failures
- User-friendly error messages in MCP responses

### Performance Considerations
- Lazy loading of embedding models
- Persistent vector database storage
- Efficient text chunking algorithms
- Batch processing for document ingestion
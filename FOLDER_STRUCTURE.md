# CFO Project Folder Structure

This document describes the organized folder structure of the CFO project.

## Root Directory Structure

```
CFO/
├── src/                      # Core application source code
├── docs/                     # All documentation files
├── config/                   # Configuration files
├── demos/                    # Demo and example scripts
├── tests/                    # Test files
├── scripts/                  # Utility scripts
├── frontend/                 # Frontend application
├── middleware/               # Middleware components
├── routers/                  # API routers
├── tasks/                    # Background tasks
├── alembic/                  # Database migrations
├── data/                     # Data files and samples
├── logs/                     # Application logs
├── file_storage/             # File storage
├── temp_uploads/             # Temporary upload files
├── legal_db/                 # Legal database
├── scheme_db/                # Scheme database
├── hackathon/                # Hackathon-related files
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup
├── Makefile                  # Build automation
└── README.md                 # Main project README
```

## Directory Descriptions

### `/src` - Source Code
Contains all core Python application files:
- `server.py` - Main server file
- `models.py` - Database models
- `database.py` - Database configuration
- `auth.py` - Authentication
- `encryption.py` - Encryption utilities
- `storage_manager.py` - Storage management
- And other core modules...

### `/docs` - Documentation
All markdown documentation files including:
- Deployment guides
- Developer guides
- Quick references
- Security documentation
- Release notes
- And more...

### `/config` - Configuration
Configuration files for various services:
- `alembic.ini` - Database migration config
- `pytest.ini` - Testing configuration
- `.env.example` - Environment variable template
- `.env.docker` - Docker environment config
- `.env.integration` - Integration environment config
- `init-db.sql` - Database initialization

### `/demos` - Demo Scripts
Demo and example scripts:
- `demo_agent_d_negotiator.py`
- `demo_complete_agent_a.py`
- `demo_legal_sentinel.py`
- `demo_visual_auditor.py`
- And more...

### `/tests` - Tests
All test files and test-related code

### `/scripts` - Utility Scripts
Utility and maintenance scripts

### `/frontend` - Frontend Application
React/Vue frontend application with its own structure

### `/middleware` - Middleware
Authentication, logging, rate limiting, and other middleware components

### `/routers` - API Routers
FastAPI routers for different API endpoints

### `/data` - Data Files
Data files including:
- `/data/samples` - Sample files (invoices, etc.)
- `/data/initial_acts` - Initial data

### `/logs` - Logs
Application log files

## Import Path Updates

Since Python files have been moved to `/src`, you may need to update imports or add the src directory to your Python path. Consider:

1. Using relative imports within the src directory
2. Adding `src` to PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:${PWD}/src"`
3. Installing the package in development mode: `pip install -e .`

## Notes

- Configuration files remain in `/config` for easy access
- Keep `.env` (actual environment file) in root and add to `.gitignore`
- Data directories (`data/`, `logs/`, etc.) are for runtime data
- Frontend has its own self-contained structure

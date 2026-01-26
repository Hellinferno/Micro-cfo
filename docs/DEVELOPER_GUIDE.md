# MicroCFO Developer Guide

This guide provides all the necessary information for developers to set up, run, test, and contribute to the MicroCFO project.

## 1. Project Overview

MicroCFO is an AI-powered financial operations platform featuring a suite of intelligent agents designed to automate and streamline financial workflows for MSMEs. It leverages a Model Context Protocol (MCP) server to coordinate agents that perform tasks like visual auditing of invoices, legislative compliance checks, subsidy hunting, and payment negotiation.

The system is composed of a Python FastAPI backend, a React/Vite frontend, and uses Docker for containerization and orchestration of its services, including a PostgreSQL database, Redis cache, and Celery workers for asynchronous tasks.

### Key Features
- **Agent A (Visual Auditor)**: Processes invoices using Gemini Vision models for data extraction and fraud detection.
- **Agent B (Legislative Sentinel)**: A structure-aware RAG system for legal and compliance inquiries.
- **Agent C (Subsidy Hunter)**: Discovers applicable government subsidies based on business context.
- **Agent D (Negotiator)**: Generates professional communication drafts for financial negotiations.
- **Integrations**: ERP adapters for Tally, Zoho, and others.
- **Security**: Features include data encryption, audit trails, and user-centric guardrails.

## 2. Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker & Docker Compose**: For running the application in a containerized environment (Recommended).
- **Python 3.10+** and `pip`: For local backend development.
- **Node.js 18+** and `npm`: For local frontend development.
- **Git**: For version control.

## 3. Setup and Installation

You can set up the development environment using either Docker (recommended for consistency) or a local manual setup.

### 3.1. Docker Setup (Recommended)

The project is configured to run with Docker Compose, which simplifies the setup of all services (backend, frontend, database, etc.). The `Makefile` contains convenient shortcuts.

1.  **Clone the Repository**:
    ```bash
    git clone <your-repository-url>
    cd MicroCFO
    ```

2.  **Configure Environment Variables**:
    Create a `.env` file by copying the example. This file will be used by the Docker containers.
    ```bash
    cp .env.example .env
    ```
    Now, edit the `.env` file and add your API keys (e.g., `GEMINI_API_KEY`) and any other necessary configurations.
    **⚠️ Important**: Never commit the `.env` file to version control.

3.  **Build and Start the Services**:
    Use the `make dev` command to build the images and start all services in development mode, which includes hot-reloading for both the frontend and backend.
    ```bash
    make dev
    ```
    Alternatively, for a production-like environment, use `make up`.
    ```bash
    make up
    ```

4.  **Accessing the Application**:
    - **Frontend**: [http://localhost:5173](http://localhost:5173) (if running `make dev`) or [http://localhost](http://localhost) (if running `make up`). The frontend port is defined in `docker-compose.dev.yml`.
    - **Backend API**: [http://localhost:8000](http://localhost:8000)
    - **API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
    - **Celery Monitoring (Flower)**: [http://localhost:5555](http://localhost:5555)

5.  **Initialize Databases**:
    After starting the services for the first time, run the database initialization scripts via the `Makefile`.
    ```bash
    make db-init
    ```

### 3.2. Local Manual Setup

This setup is for developers who want to run the frontend and backend services directly on their host machine.

1.  **Clone and Configure**: Follow steps 1 and 2 from the Docker setup.

2.  **Backend Setup**:
    ```bash
    # Create and activate a virtual environment
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt

    # Initialize databases
    python setup_legal_db.py
    python setup_scheme_db.py
    ```

3.  **Frontend Setup**:
    ```bash
    cd frontend
    npm install
    cd ..
    ```

4.  **Run the Development Servers**:
    The project includes helper scripts to start both servers.
    - **PowerShell (Windows)**:
      ```powershell
      .\start-dev.ps1
      ```
    - **Batch (Windows)**:
      ```bat
      .\start-dev.bat
      ```
    These scripts will start the FastAPI backend and the Vite frontend dev server in parallel.

## 4. Project Structure

The repository is organized into a backend (root directory) and a `frontend` directory.

```
/
├── frontend/             # React/Vite frontend application
│   ├── src/              # Source code for the frontend
│   ├── vite.config.js    # Vite configuration
│   └── package.json      # Frontend dependencies and scripts
├── routers/              # FastAPI API routers for different endpoints
├── middleware/           # Custom FastAPI middleware
├── alembic/              # Database migration scripts
├── tasks/                # Celery background task definitions
├── .dockerignore         # Files to ignore in Docker builds
├── docker-compose.yml    # Main Docker Compose file for production
├── docker-compose.dev.yml# Docker Compose overrides for development
├── Dockerfile            # Dockerfile for the backend service
├── Makefile              # Helper commands for Docker and dev tasks
├── requirements.txt      # Python dependencies
├── server.py             # Main MCP server entry point
├── integration_server.py # FastAPI application for integrations
└── ...                   # Other backend modules and configuration
```

## 5. Running Tests

### Backend Tests

The backend uses `pytest`. Tests are located in files named `test_*.py`.

-   **Run all tests (local)**:
    ```bash
    pytest -v
    ```
-   **Run all tests (Docker)**:
    ```bash
    make test
    # Or, to execute in a running container
    docker-compose exec backend pytest -v
    ```

### Frontend Tests & Linting

The frontend uses ESLint for code quality.

-   **Run linter**:
    ```bash
    cd frontend
    npm run lint
    ```

## 6. Database Migrations

The project uses **Alembic** for handling database schema migrations.

1.  **Generate a new migration**:
    After making changes to the SQLAlchemy models in `models.py`, generate a new migration script.
    ```bash
    # Ensure you are in the running backend container or have the local venv active
    alembic revision --autogenerate -m "Your migration message"
    ```

2.  **Apply migrations**:
    To apply all pending migrations to the database:
    ```bash
    alembic upgrade head
    ```
    The `Makefile` has a `db-migrate` target, though it may need to be implemented with the `alembic upgrade head` command.

## 7. Coding Conventions

Please adhere to the following conventions to maintain code quality and consistency.

### Python (Backend)
-   Follow **PEP 8** style guidelines.
-   Use a maximum line length of 127 characters.
-   Use type hints for function signatures.
-   Follow the commit message format outlined in `.github/CONTRIBUTING.md`.

### JavaScript/React (Frontend)
-   Follow the styles enforced by ESLint (`npm run lint`).
-   Use functional components with Hooks.
-   Follow the commit message format outlined in `.github/CONTRIBUTING.md`.

## 8. Deployment

The production environment is deployed using Docker.

-   **Start Production Services**:
    ```bash
    make up
    # or
    make prod
    ```
    This command starts the services in detached mode based on the `docker-compose.yml` file.

-   **Stopping Services**:
    ```bash
    make down
    ```

-   **Cleaning Up**:
    To stop and remove all containers, volumes, and networks, use the `clean` command. **Warning**: This will delete all data in your Docker volumes, including database data.
    ```bash
    make clean
    ```

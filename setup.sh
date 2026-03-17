#!/bin/bash
# MicroCFO Setup Script for Unix/Linux/Mac
# Automates the initial setup process

set -e

echo "============================================"
echo "  MicroCFO - Automated Setup Script"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed"
    echo "Please install Python 3.11+ using your package manager"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "[OK] Python $PYTHON_VERSION found"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "[OK] Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "[OK] pip upgraded"
echo ""

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet
echo "[OK] Dependencies installed"
echo ""

# Check if Node.js is installed
if command -v node &> /dev/null; then
    echo "[OK] Node.js found"
    echo ""
    
    # Install frontend dependencies
    if [ -f "frontend/package.json" ]; then
        echo "Installing frontend dependencies..."
        cd frontend
        npm install --silent
        cd ..
        echo "[OK] Frontend dependencies installed"
    fi
else
    echo "[WARNING] Node.js is not installed"
    echo "Frontend development will not be available"
    echo "Install Node.js from https://nodejs.org/"
fi
echo ""

# Create .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "[OK] .env file created"
    echo ""
    echo "[IMPORTANT] Please edit .env and add your API keys:"
    echo "  - GEMINI_API_KEY (required for AI features)"
    echo "  - DATABASE_URL (optional, defaults to SQLite)"
    echo ""
else
    echo "[OK] .env file already exists"
fi
echo ""

# Initialize database
echo "Initializing database..."
python -c "from src.database import init_db; init_db()" 2>/dev/null || echo "[WARNING] Database initialization failed"
echo "[OK] Database initialized (or skipped)"
echo ""

# Create directories
mkdir -p logs file_storage legal_db scheme_db
echo "[OK] Directories created"
echo ""

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your GEMINI_API_KEY"
echo "  2. Run: uvicorn main:app --reload"
echo "  3. Open: http://localhost:8000/docs"
echo ""
echo "For frontend development:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "============================================"

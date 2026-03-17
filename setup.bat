@echo off
REM MicroCFO Setup Script for Windows
REM Automates the initial setup process

echo ============================================
echo   MicroCFO - Automated Setup Script
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
python -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"
if errorlevel 1 (
    echo [ERROR] Python 3.11 or higher is required
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt --quiet
echo [OK] Dependencies installed
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js is not installed
    echo Frontend development will not be available
    echo Install Node.js from https://nodejs.org/
) else (
    echo [OK] Node.js found
    echo.
    
    REM Install frontend dependencies
    if exist "frontend\package.json" (
        echo Installing frontend dependencies...
        cd frontend
        call npm install --silent
        cd ..
        echo [OK] Frontend dependencies installed
    )
)
echo.

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo [OK] .env file created
    echo.
    echo [IMPORTANT] Please edit .env and add your API keys:
    echo   - GEMINI_API_KEY (required for AI features)
    echo   - DATABASE_URL (optional, defaults to SQLite)
    echo.
) else (
    echo [OK] .env file already exists
)
echo.

REM Initialize database
echo Initializing database...
python -c "from src.database import init_db; init_db()" 2>nul
if errorlevel 1 (
    echo [WARNING] Database initialization failed
    echo You can initialize it manually later
) else (
    echo [OK] Database initialized
)
echo.

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "file_storage" mkdir file_storage
if not exist "legal_db" mkdir legal_db
if not exist "scheme_db" mkdir scheme_db
echo [OK] Directories created
echo.

echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Edit .env and add your GEMINI_API_KEY
echo   2. Run: uvicorn main:app --reload
echo   3. Open: http://localhost:8000/docs
echo.
echo For frontend development:
echo   cd frontend
echo   npm run dev
echo.
echo ============================================
pause

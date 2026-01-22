@echo off
REM MicroCFO Development Startup Script (Batch)
REM Starts both backend and frontend servers

echo.
echo ========================================
echo   MicroCFO Development Environment
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.7+ first.
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js first.
    pause
    exit /b 1
)

echo [OK] Python and Node.js found
echo.

REM Start Backend Server
echo [STARTING] FastAPI Backend Server...
start "MicroCFO Backend" cmd /k "python integration_server.py"
echo [OK] Backend server starting in new window
echo     Backend: http://localhost:8000
echo     API Docs: http://localhost:8000/docs
echo.

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start Frontend Server
echo [STARTING] React Frontend Server...
start "MicroCFO Frontend" cmd /k "cd frontend && npm run dev"
echo [OK] Frontend server starting in new window
echo     Frontend: http://localhost:5173
echo.

echo ========================================
echo   Servers Started Successfully!
echo ========================================
echo.
echo Services:
echo   - Frontend:  http://localhost:5173
echo   - Backend:   http://localhost:8000
echo   - API Docs:  http://localhost:8000/docs
echo.
echo To stop servers, close the terminal windows
echo or press Ctrl+C in each window.
echo.
pause

@echo off
setlocal
title MicroCFO Launcher

echo ===================================================
echo   MicroCFO Startup Debugger
echo ===================================================
echo.

REM 1. Set Project Root
echo [1/5] Determining Project Root...
cd /d "%~dp0"
cd ..
set "PROJECT_ROOT=%CD%"
echo     Root: %PROJECT_ROOT%
echo.

REM 2. Check Virtual Environment
echo [2/5] Checking Backend Environment...
if exist "venv\Scripts\python.exe" (
    echo     [OK] Found venv\Scripts\python.exe
) else (
    echo     [ERROR] venv python not found at: %PROJECT_ROOT%\venv\Scripts\python.exe
    pause
    exit /b 1
)
echo.

REM 3. Check Frontend
echo [3/5] Checking Frontend Directory...
if exist "frontend\package.json" (
    echo     [OK] Found frontend configuration
) else (
    echo     [ERROR] Frontend not found at: %PROJECT_ROOT%\frontend
    pause
    exit /b 1
)
echo.

REM 4. Start Backend
echo [4/5] Launching Backend Server...
echo     Command: venv\Scripts\python.exe integration_server.py
start "MicroCFO Backend" cmd /k "title Backend && venv\Scripts\python.exe integration_server.py || pause"
echo     [OK] Backend window opened
echo.

REM 5. Start Frontend
echo [5/5] Launching Frontend Server...
echo     Command: npm run dev
cd frontend
start "MicroCFO Frontend" cmd /k "title Frontend && npm run dev || pause"
echo     [OK] Frontend window opened
echo.

echo ===================================================
echo   Startup Initiated!
echo ===================================================
echo.
echo Waiting 5 seconds for servers to initialize...
timeout /t 5 /nobreak >nul

echo Opening Browser...
start http://localhost:5173

echo.
echo If the browser shows "Connection Refused":
echo 1. Check the "MicroCFO Backend" window for errors.
echo 2. Check the "MicroCFO Frontend" window for errors.
echo.
pause

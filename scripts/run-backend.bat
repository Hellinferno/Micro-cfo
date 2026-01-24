@echo off
title MicroCFO Backend
echo Starting Backend...
cd /d "%~dp0.."
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)
"venv\Scripts\python.exe" integration_server.py
pause

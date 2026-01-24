@echo off
title MicroCFO Frontend
echo Starting Frontend...
cd /d "%~dp0..\frontend"
npm run dev
pause

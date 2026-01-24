# MicroCFO Development Startup Script (PowerShell)
# Starts both backend and frontend servers

Write-Host "🚀 Starting MicroCFO Development Environment..." -ForegroundColor Cyan
Write-Host ""

# Determine Project Root (parent of the scripts folder)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot
Write-Host "📂 Working Directory: $ProjectRoot" -ForegroundColor Gray

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.7+ first." -ForegroundColor Red
    exit 1
}

# Check if Node.js is available
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python and Node.js found" -ForegroundColor Green
Write-Host ""

# Start Backend Server
Write-Host "📡 Starting FastAPI Backend Server..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:ProjectRoot
    & ".\venv\Scripts\python.exe" integration_server.py
}
Write-Host "✅ Backend server starting (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "   Backend will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start Frontend Server
Write-Host "🎨 Starting React Frontend Server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:ProjectRoot\frontend"
    npm run dev
}
Write-Host "✅ Frontend server starting (Job ID: $($frontendJob.Id))" -ForegroundColor Green
Write-Host "   Frontend will be available at: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎉 MicroCFO Development Environment Started!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Services:" -ForegroundColor White
Write-Host "   • Frontend:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "   • Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "   • API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "🛑 To stop servers:" -ForegroundColor Yellow
Write-Host "   Press Ctrl+C, then run: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 View logs:" -ForegroundColor White
Write-Host "   Backend:  Receive-Job -Id $($backendJob.Id) -Keep" -ForegroundColor Gray
Write-Host "   Frontend: Receive-Job -Id $($frontendJob.Id) -Keep" -ForegroundColor Gray
Write-Host ""

# Monitor jobs
Write-Host "Monitoring servers (Press Ctrl+C to stop)..." -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if jobs are still running
        $backendState = (Get-Job -Id $backendJob.Id).State
        $frontendState = (Get-Job -Id $frontendJob.Id).State
        
        if ($backendState -ne "Running") {
            Write-Host "⚠️  Backend server stopped unexpectedly!" -ForegroundColor Red
            Receive-Job -Id $backendJob.Id
            break
        }
        
        if ($frontendState -ne "Running") {
            Write-Host "⚠️  Frontend server stopped unexpectedly!" -ForegroundColor Red
            Receive-Job -Id $frontendJob.Id
            break
        }
    }
}
finally {
    Write-Host ""
    Write-Host "🛑 Stopping servers..." -ForegroundColor Yellow
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    Write-Host "✅ All servers stopped" -ForegroundColor Green
}

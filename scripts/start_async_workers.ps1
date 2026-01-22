# PowerShell script to start all async task queue components
# Run this script to start Redis, Celery workers, Beat, and Flower

Write-Host "🚀 Starting MicroCFO Async Task Queue System" -ForegroundColor Green
Write-Host ""

# Check if Redis is running
Write-Host "📡 Checking Redis..." -ForegroundColor Cyan
try {
    $redisCheck = redis-cli ping 2>$null
    if ($redisCheck -eq "PONG") {
        Write-Host "✅ Redis is already running" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Redis is not running. Starting Redis..." -ForegroundColor Yellow
    Write-Host "Please start Redis manually or use Docker:" -ForegroundColor Yellow
    Write-Host "  docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

Write-Host ""
Write-Host "🔧 Starting Celery components..." -ForegroundColor Cyan
Write-Host ""

# Function to start a process in a new window
function Start-InNewWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$Color
    )
    
    Write-Host "Starting $Title..." -ForegroundColor $Color
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {
        Write-Host '═══════════════════════════════════════' -ForegroundColor $Color;
        Write-Host '  $Title' -ForegroundColor $Color;
        Write-Host '═══════════════════════════════════════' -ForegroundColor $Color;
        Write-Host '';
        cd '$PWD';
        .\venv\Scripts\Activate.ps1;
        $Command
    }"
}

# Start Celery Worker
Start-InNewWindow `
    -Title "Celery Worker - Visual Auditor Queue" `
    -Command "celery -A celery_app worker -Q visual_auditor --loglevel=info --concurrency=2" `
    -Color "Green"

Start-Sleep -Seconds 2

# Start Celery Worker for Legal Sentinel
Start-InNewWindow `
    -Title "Celery Worker - Legal Sentinel Queue" `
    -Command "celery -A celery_app worker -Q legal_sentinel --loglevel=info --concurrency=2" `
    -Color "Blue"

Start-Sleep -Seconds 2

# Start Celery Worker for Subsidy Hunter
Start-InNewWindow `
    -Title "Celery Worker - Subsidy Hunter Queue" `
    -Command "celery -A celery_app worker -Q subsidy_hunter --loglevel=info --concurrency=1" `
    -Color "Magenta"

Start-Sleep -Seconds 2

# Start Celery Worker for Negotiator
Start-InNewWindow `
    -Title "Celery Worker - Negotiator Queue" `
    -Command "celery -A celery_app worker -Q negotiator --loglevel=info --concurrency=1" `
    -Color "Cyan"

Start-Sleep -Seconds 2

# Start Celery Beat (Periodic Tasks)
Start-InNewWindow `
    -Title "Celery Beat - Periodic Tasks Scheduler" `
    -Command "celery -A celery_app beat --loglevel=info" `
    -Color "Yellow"

Start-Sleep -Seconds 2

# Start Flower (Monitoring Dashboard)
Start-InNewWindow `
    -Title "Flower - Celery Monitoring Dashboard" `
    -Command "celery -A celery_app flower --port=5555" `
    -Color "DarkGreen"

Write-Host ""
Write-Host "✅ All components started!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Access Points:" -ForegroundColor Cyan
Write-Host "  • Flower Dashboard: http://localhost:5555" -ForegroundColor White
Write-Host "  • API Server: http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Monitor your tasks:" -ForegroundColor Cyan
Write-Host "  • Open Flower at http://localhost:5555" -ForegroundColor White
Write-Host "  • View active tasks, workers, and queues" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  To stop all workers:" -ForegroundColor Yellow
Write-Host "  • Close all PowerShell windows" -ForegroundColor White
Write-Host "  • Or press Ctrl+C in each window" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

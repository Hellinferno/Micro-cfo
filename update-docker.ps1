# Docker Update Script for Windows PowerShell
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MicroCFO Docker Update Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    $null = docker ps 2>&1
    Write-Host "Success: Docker is running" -ForegroundColor Green
}
catch {
    Write-Host "Error: Docker is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example" -ForegroundColor Green
        Write-Host "Please edit .env with your configuration" -ForegroundColor Yellow
        Write-Host ""
    }
}

# Show menu
Write-Host "Select update option:" -ForegroundColor Cyan
Write-Host "  1. Quick restart" -ForegroundColor White
Write-Host "  2. Rebuild and restart (recommended)" -ForegroundColor White
Write-Host "  3. Full clean rebuild" -ForegroundColor White
Write-Host "  4. Cancel" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter choice (1-4)"

Write-Host ""

if ($choice -eq "1") {
    Write-Host "Quick restart..." -ForegroundColor Yellow
    docker-compose stop
    docker-compose up -d
}
elseif ($choice -eq "2") {
    Write-Host "Rebuild and restart..." -ForegroundColor Yellow
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
}
elseif ($choice -eq "3") {
    Write-Host "Warning: This removes all data!" -ForegroundColor Red
    $confirm = Read-Host "Type 'yes' to confirm"
    if ($confirm -eq "yes") {
        docker-compose down -v --remove-orphans
        docker-compose build --no-cache
        docker-compose up -d
        Start-Sleep -Seconds 10
        docker-compose exec -T backend alembic upgrade head
    }
    else {
        Write-Host "Cancelled" -ForegroundColor Yellow
        exit 0
    }
}
else {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "Service Status:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Docker update complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost" -ForegroundColor White
Write-Host "Flower:   http://localhost:5555" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White

# Docker Update Script for Windows PowerShell
# Rebuilds and restarts Docker containers with latest changes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MicroCFO Docker Update Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        $null = docker ps 2>&1
        return $true
    }
    catch {
        return $false
    }
}

# Function to check if docker-compose is installed
function Test-DockerComposeInstalled {
    try {
        $null = docker-compose --version 2>&1
        return $true
    }
    catch {
        return $false
    }
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-DockerComposeInstalled)) {
    Write-Host "ERROR: docker-compose is not installed" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-DockerRunning)) {
    Write-Host "ERROR: Docker is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Docker is installed and running" -ForegroundColor Green
Write-Host ""

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env file" -ForegroundColor Green
        Write-Host "Please edit .env with your configuration before continuing" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press Enter to continue after editing .env..." -NoNewline
        Read-Host
    }
    else {
        Write-Host "ERROR: .env.example not found" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ .env file exists" -ForegroundColor Green
Write-Host ""

# Show current containers
Write-Host "Current containers:" -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# Ask for update type
Write-Host "Select update type:" -ForegroundColor Cyan
Write-Host "  1. Quick restart (no rebuild)" -ForegroundColor White
Write-Host "  2. Rebuild and restart (recommended)" -ForegroundColor White
Write-Host "  3. Full clean and rebuild" -ForegroundColor White
Write-Host "  4. Cancel" -ForegroundColor White
Write-Host ""
Write-Host "Enter choice (1-4): " -NoNewline -ForegroundColor Cyan
$choice = Read-Host

Write-Host ""

switch ($choice) {
    "1" {
        # Quick restart
        Write-Host "Performing quick restart..." -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "Stopping containers..." -ForegroundColor Yellow
        docker-compose stop
        
        Write-Host "Starting containers..." -ForegroundColor Yellow
        docker-compose up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Containers restarted" -ForegroundColor Green
        }
        else {
            Write-Host "✗ Restart failed" -ForegroundColor Red
            exit 1
        }
    }
    
    "2" {
        # Rebuild and restart
        Write-Host "Rebuilding and restarting containers..." -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "Stopping containers..." -ForegroundColor Yellow
        docker-compose down
        
        Write-Host "Building images..." -ForegroundColor Yellow
        docker-compose build --no-cache
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Build failed" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Starting containers..." -ForegroundColor Yellow
        docker-compose up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Containers rebuilt and started" -ForegroundColor Green
        }
        else {
            Write-Host "✗ Start failed" -ForegroundColor Red
            exit 1
        }
    }
    
    "3" {
        # Full clean and rebuild
        Write-Host "WARNING: This will remove all containers, volumes, and data!" -ForegroundColor Red
        Write-Host "Are you sure? (yes/no): " -NoNewline -ForegroundColor Yellow
        $confirmClean = Read-Host
        
        if ($confirmClean -ne "yes") {
            Write-Host "Operation cancelled" -ForegroundColor Yellow
            exit 0
        }
        
        Write-Host ""
        Write-Host "Performing full clean and rebuild..." -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "Stopping and removing containers..." -ForegroundColor Yellow
        docker-compose down -v --remove-orphans
        
        Write-Host "Removing unused images..." -ForegroundColor Yellow
        docker image prune -f
        
        Write-Host "Building images..." -ForegroundColor Yellow
        docker-compose build --no-cache
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Build failed" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Starting containers..." -ForegroundColor Yellow
        docker-compose up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Full rebuild complete" -ForegroundColor Green
        }
        else {
            Write-Host "✗ Start failed" -ForegroundColor Red
            exit 1
        }
        
        Write-Host ""
        Write-Host "Running database migrations..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        docker-compose exec -T backend alembic upgrade head
    }
    
    "4" {
        Write-Host "Operation cancelled" -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check service health
Write-Host ""
Write-Host "Checking service health..." -ForegroundColor Yellow
Write-Host ""

# Check backend
Write-Host "Backend: " -NoNewline -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Healthy" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Unhealthy (Status: $($response.StatusCode))" -ForegroundColor Red
    }
}
catch {
    Write-Host "✗ Not responding" -ForegroundColor Red
}

# Check frontend
Write-Host "Frontend: " -NoNewline -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Healthy" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Unhealthy (Status: $($response.StatusCode))" -ForegroundColor Red
    }
}
catch {
    Write-Host "✗ Not responding" -ForegroundColor Red
}

# Check Flower
Write-Host "Flower: " -NoNewline -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5555/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Healthy" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Unhealthy (Status: $($response.StatusCode))" -ForegroundColor Red
    }
}
catch {
    Write-Host "✗ Not responding" -ForegroundColor Red
}

Write-Host ""

# Show running containers
Write-Host "Running containers:" -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# Show summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Update Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost" -ForegroundColor White
Write-Host "Flower:   http://localhost:5555" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "View logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "Stop all:  docker-compose down" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Docker update complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

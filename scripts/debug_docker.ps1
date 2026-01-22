# Docker Debug & Reset Script

Write-Host "🕵️ Starting Docker Debug & Reset..." -ForegroundColor Cyan

# 1. Check Docker Daemon
Write-Host "1️⃣ Checking Docker Daemon status..." -ForegroundColor Yellow

$daemonRunning = $false
try {
    $info = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        $daemonRunning = $true
        Write-Host "✅ Docker Daemon is responsive." -ForegroundColor Green
    }
}
catch {
    # Ignore initial error
}

if (-not $daemonRunning) {
    Write-Host "⚠️  Docker Daemon not running. Attempting to start Docker Desktop..." -ForegroundColor Yellow
    try {
        $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerPath) {
            Start-Process $dockerPath
            Write-Host "⏳ Waiting 60 seconds for Docker to initialize..." -ForegroundColor Cyan
            Start-Sleep -Seconds 60
            
            # Retry check
            $info = docker info 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Docker started successfully." -ForegroundColor Green
            }
            else {
                Write-Host "❌ Docker failed to start after waiting." -ForegroundColor Red
                # Exit but don't fail completely, maybe the user wants to try anyway? No, if docker info fails, docker-compose will fail.
                exit 1
            }
        }
        else {
            Write-Host "❌ Docker Desktop executable not found at default location: $dockerPath" -ForegroundColor Red
            Write-Host "Please start Docker Desktop manually." -ForegroundColor Yellow
            exit 1
        }
    }
    catch {
        Write-Host "❌ Failed to start Docker. Please start Docker Desktop manually." -ForegroundColor Red
        Write-Host "Error details: $_" -ForegroundColor Gray
        exit 1
    }
}

# 2. Stop and Remove Containers
Write-Host "2️⃣ Stopping and removing existing containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Containers removed." -ForegroundColor Green
}
else {
    Write-Host "⚠️  Warning during 'docker-compose down' (might be already down)." -ForegroundColor Gray
}

# 3. Prune Build Cache (Optional but recommended for 'red X' issues)
Write-Host "3️⃣ Pruning builder cache (to fix potential layer corruption)..." -ForegroundColor Yellow
# We use 'echo y' to confirm the pruning non-interactively
echo y | docker builder prune 2>&1 | Out-Null
Write-Host "✅ Builder cache pruned." -ForegroundColor Green

# 4. Rebuild Images
Write-Host "4️⃣ Rebuilding images (no cache)..." -ForegroundColor Yellow
docker-compose build --no-cache
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Images built successfully." -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to build images." -ForegroundColor Red
    exit 1
}

# 5. Start Services
Write-Host "5️⃣ Starting services..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Services started." -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to start services." -ForegroundColor Red
    exit 1
}

# 6. Check Health
Write-Host "6️⃣ Waiting for health checks (15s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
docker-compose ps

Write-Host "`n✅ Debug script completed. Check the status above." -ForegroundColor Cyan

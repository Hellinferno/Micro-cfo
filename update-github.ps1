# GitHub Update Script for Windows PowerShell
# Updates GitHub repository with latest changes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MicroCFO GitHub Update Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if git is installed
function Test-GitInstalled {
    try {
        $null = git --version
        return $true
    }
    catch {
        return $false
    }
}

# Function to check if we're in a git repository
function Test-GitRepository {
    try {
        $null = git rev-parse --git-dir 2>&1
        return $true
    }
    catch {
        return $false
    }
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-GitInstalled)) {
    Write-Host "ERROR: Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-GitRepository)) {
    Write-Host "ERROR: Not a git repository" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "Success: Git is installed" -ForegroundColor Green
Write-Host "Success: In git repository" -ForegroundColor Green
Write-Host ""

# Check current branch
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan
Write-Host ""

# Check for uncommitted changes
Write-Host "Checking for changes..." -ForegroundColor Yellow
$status = git status --porcelain

if (-not $status) {
    Write-Host "No changes to commit" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Would you like to push existing commits? (y/n): " -NoNewline -ForegroundColor Cyan
    $pushOnly = Read-Host
    
    if ($pushOnly -eq 'y' -or $pushOnly -eq 'Y') {
        Write-Host ""
        Write-Host "Pushing to remote..." -ForegroundColor Yellow
        git push origin $currentBranch
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Success: Pushed to GitHub" -ForegroundColor Green
        }
        else {
            Write-Host "Error: Push failed" -ForegroundColor Red
            Write-Host "Please check the error message above" -ForegroundColor Yellow
        }
    }
    exit 0
}

# Show status
Write-Host "Changes detected:" -ForegroundColor Green
git status --short
Write-Host ""

# Ask for confirmation
Write-Host "Do you want to commit and push these changes? (y/n): " -NoNewline -ForegroundColor Cyan
$confirm = Read-Host

if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Operation cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# Get commit message
Write-Host "Enter commit message (or press Enter for default): " -NoNewline -ForegroundColor Cyan
$commitMessage = Read-Host

if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = "Update: Latest changes to MicroCFO system"
    Write-Host "Using default message: $commitMessage" -ForegroundColor Yellow
}

Write-Host ""

# Stage all changes
Write-Host "Staging changes..." -ForegroundColor Yellow
git add .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to stage changes" -ForegroundColor Red
    exit 1
}

Write-Host "Success: Changes staged" -ForegroundColor Green
Write-Host ""

# Commit changes
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m $commitMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Commit failed" -ForegroundColor Red
    exit 1
}

Write-Host "Success: Changes committed" -ForegroundColor Green
Write-Host ""

# Push to remote
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push origin $currentBranch

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Push failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Remote repository not configured" -ForegroundColor White
    Write-Host "     Solution: git remote add origin YOUR-REPO-URL" -ForegroundColor Gray
    Write-Host "  2. Authentication failed" -ForegroundColor White
    Write-Host "     Solution: Configure GitHub credentials or use SSH" -ForegroundColor Gray
    Write-Host "  3. Branch not tracking remote" -ForegroundColor White
    Write-Host "     Solution: git push -u origin $currentBranch" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "Success: Pushed to GitHub" -ForegroundColor Green
Write-Host ""

# Show summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Update Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Branch: $currentBranch" -ForegroundColor White
Write-Host "Commit: $commitMessage" -ForegroundColor White
Write-Host "Status: Pushed to GitHub" -ForegroundColor Green
Write-Host ""

# Show last commit
Write-Host "Last commit details:" -ForegroundColor Yellow
git log -1 --stat
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub update complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

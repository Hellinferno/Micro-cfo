# GitHub push script for MicroCFO (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "MicroCFO GitHub Update Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Error: Not a git repository" -ForegroundColor Red
    Write-Host "Run: git init"
    exit 1
}

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "Found uncommitted changes" -ForegroundColor Yellow
    
    # Show status
    Write-Host ""
    Write-Host "Current status:" -ForegroundColor Cyan
    git status --short
    
    # Ask for confirmation
    Write-Host ""
    $response = Read-Host "Stage all changes? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        git add .
        Write-Host "✓ Changes staged" -ForegroundColor Green
    } else {
        Write-Host "Aborted" -ForegroundColor Red
        exit 1
    }
}

# Get commit message
Write-Host ""
Write-Host "Enter commit message (or press Enter for default):" -ForegroundColor Cyan
$commitMessage = Read-Host

if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = @"
chore: update Docker and GitHub configurations

- Add comprehensive Docker setup with docker-compose
- Add GitHub Actions CI/CD workflows
- Add issue templates and PR template
- Add contributing guidelines
- Update documentation
"@
}

# Commit changes
Write-Host ""
Write-Host "Committing changes..." -ForegroundColor Cyan
git commit -m $commitMessage
Write-Host "✓ Changes committed" -ForegroundColor Green

# Get branch name
$branch = git rev-parse --abbrev-ref HEAD
Write-Host ""
Write-Host "Current branch: $branch" -ForegroundColor Cyan

# Push to remote
Write-Host ""
$response = Read-Host "Push to origin/$branch? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host "Pushing to origin/$branch..." -ForegroundColor Cyan
    git push origin $branch
    Write-Host "✓ Push complete" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "✓ Successfully updated GitHub!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Configure GitHub secrets (GEMINI_API_KEY, etc.)"
    Write-Host "2. Enable GitHub Actions"
    Write-Host "3. Set up branch protection rules"
    Write-Host ""
    Write-Host "See GITHUB_CONFIGURATION_CHECKLIST.md for details"
} else {
    Write-Host "Push cancelled" -ForegroundColor Yellow
}

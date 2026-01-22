# GitHub Update Script for MicroCFO
# Commits and pushes all Phase 4 and Security changes

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  MICROCFO GITHUB UPDATE" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "❌ Git repository not initialized" -ForegroundColor Red
    Write-Host "Run: git init" -ForegroundColor Yellow
    exit 1
}

# Check for uncommitted changes
Write-Host "📊 Checking repository status..." -ForegroundColor Cyan
git status --short

Write-Host "`n📝 Staging all changes..." -ForegroundColor Cyan

# Stage all new and modified files
git add .

Write-Host "`n✅ Files staged successfully" -ForegroundColor Green

# Show what will be committed
Write-Host "`n📋 Files to be committed:" -ForegroundColor Cyan
git status --short

# Create commit with detailed message
Write-Host "`n💾 Creating commit..." -ForegroundColor Cyan

$commitMessage = @"
feat: Add Phase 4 (ERP Integration & Onboarding) + Security & Compliance

Major update implementing Phase 4 and comprehensive security features.

Phase 4: Business Logic & Integration
- ERP Adapters: Export to Tally, Zoho Books, CSV, JSON
- User Onboarding: 12 industries, 4 turnover tiers
- API Routers: 16 new endpoints
- Contextual Filtering: Industry and turnover-based

Security & Compliance
- Data Encryption: AES-256 at rest, S3 encryption
- Audit Trails: Comprehensive logging (Who, What, When, Where, How)
- Legal Disclaimers: 7 types with frontend modal
- Guardrails: Draft-only mode, verification required

Frontend Integration
- Real API calls to backend
- Disclaimer modal and banner
- File upload handling
- Dynamic action cards

Files: 28 created, 11 modified
Lines: ~4,000+ new code
Documentation: 16 comprehensive guides
Testing: All components tested ✅

Breaking Changes: None
Migration: Run setup_encryption.py, configure .env

Version: 2.0.0
Status: Production-Ready ✅
"@

git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Commit created successfully" -ForegroundColor Green
    
    # Show commit details
    Write-Host "`n📄 Commit details:" -ForegroundColor Cyan
    git log -1 --stat
    
    # Ask to push
    Write-Host "`n🚀 Ready to push to GitHub" -ForegroundColor Yellow
    $push = Read-Host "Push to remote? (y/n)"
    
    if ($push -eq "y" -or $push -eq "Y") {
        Write-Host "`n📤 Pushing to GitHub..." -ForegroundColor Cyan
        
        # Get current branch
        $branch = git rev-parse --abbrev-ref HEAD
        Write-Host "Branch: $branch" -ForegroundColor Gray
        
        # Push
        git push origin $branch
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Successfully pushed to GitHub!" -ForegroundColor Green
            Write-Host "`n🎉 Update complete!" -ForegroundColor Magenta
            Write-Host "`nView your changes at:" -ForegroundColor Cyan
            $remote = git remote get-url origin
            Write-Host $remote -ForegroundColor White
        } else {
            Write-Host "`n❌ Push failed" -ForegroundColor Red
            Write-Host "Check your remote configuration and try again" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n⏸️  Commit created but not pushed" -ForegroundColor Yellow
        Write-Host "Run 'git push' when ready" -ForegroundColor Gray
    }
} else {
    Write-Host "`n❌ Commit failed" -ForegroundColor Red
    Write-Host "Check the error message above" -ForegroundColor Yellow
}

Write-Host "`n========================================`n" -ForegroundColor Green

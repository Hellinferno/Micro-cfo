#!/bin/bash
# GitHub push script for MicroCFO

set -e

echo "=========================================="
echo "MicroCFO GitHub Update Script"
echo "=========================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
  echo "Error: Not a git repository"
  echo "Run: git init"
  exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
  echo "Found uncommitted changes"
  
  # Show status
  echo ""
  echo "Current status:"
  git status --short
  
  # Ask for confirmation
  echo ""
  read -p "Stage all changes? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
    echo "✓ Changes staged"
  else
    echo "Aborted"
    exit 1
  fi
fi

# Get commit message
echo ""
echo "Enter commit message (or press Enter for default):"
read -r commit_message

if [ -z "$commit_message" ]; then
  commit_message="chore: update Docker and GitHub configurations

- Add comprehensive Docker setup with docker-compose
- Add GitHub Actions CI/CD workflows
- Add issue templates and PR template
- Add contributing guidelines
- Update documentation"
fi

# Commit changes
echo ""
echo "Committing changes..."
git commit -m "$commit_message"
echo "✓ Changes committed"

# Get branch name
branch=$(git rev-parse --abbrev-ref HEAD)
echo ""
echo "Current branch: $branch"

# Push to remote
echo ""
read -p "Push to origin/$branch? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "Pushing to origin/$branch..."
  git push origin "$branch"
  echo "✓ Push complete"
  
  echo ""
  echo "=========================================="
  echo "✓ Successfully updated GitHub!"
  echo "=========================================="
  echo ""
  echo "Next steps:"
  echo "1. Configure GitHub secrets (GEMINI_API_KEY, etc.)"
  echo "2. Enable GitHub Actions"
  echo "3. Set up branch protection rules"
  echo ""
  echo "See GITHUB_CONFIGURATION_CHECKLIST.md for details"
else
  echo "Push cancelled"
fi

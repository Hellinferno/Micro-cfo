#!/bin/bash
# GitHub Update Script for Unix/Linux/Mac
# Updates GitHub repository with latest changes

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "  MicroCFO GitHub Update Script"
echo -e "========================================${NC}"
echo ""

# Function to check if git is installed
check_git() {
    if ! command -v git &> /dev/null; then
        echo -e "${RED}ERROR: Git is not installed${NC}"
        echo -e "${YELLOW}Please install Git first${NC}"
        exit 1
    fi
}

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Not a git repository${NC}"
        echo -e "${YELLOW}Please run this script from the project root directory${NC}"
        exit 1
    fi
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

check_git
check_git_repo

echo -e "${GREEN}✓ Git is installed${NC}"
echo -e "${GREEN}✓ In git repository${NC}"
echo ""

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${CYAN}Current branch: $CURRENT_BRANCH${NC}"
echo ""

# Check for uncommitted changes
echo -e "${YELLOW}Checking for changes...${NC}"
STATUS=$(git status --porcelain)

if [ -z "$STATUS" ]; then
    echo -e "${YELLOW}No changes to commit${NC}"
    echo ""
    echo -ne "${CYAN}Would you like to push existing commits? (y/n): ${NC}"
    read -r PUSH_ONLY
    
    if [ "$PUSH_ONLY" = "y" ] || [ "$PUSH_ONLY" = "Y" ]; then
        echo ""
        echo -e "${YELLOW}Pushing to remote...${NC}"
        git push origin "$CURRENT_BRANCH"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Successfully pushed to GitHub${NC}"
        else
            echo -e "${RED}✗ Push failed${NC}"
            echo -e "${YELLOW}Please check the error message above${NC}"
        fi
    fi
    exit 0
fi

# Show status
echo -e "${GREEN}Changes detected:${NC}"
git status --short
echo ""

# Ask for confirmation
echo -ne "${CYAN}Do you want to commit and push these changes? (y/n): ${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${YELLOW}Operation cancelled${NC}"
    exit 0
fi

echo ""

# Get commit message
echo -ne "${CYAN}Enter commit message (or press Enter for default): ${NC}"
read -r COMMIT_MESSAGE

if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="Update: Latest changes to MicroCFO system"
    echo -e "${YELLOW}Using default message: $COMMIT_MESSAGE${NC}"
fi

echo ""

# Stage all changes
echo -e "${YELLOW}Staging changes...${NC}"
git add .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to stage changes${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Changes staged${NC}"
echo ""

# Commit changes
echo -e "${YELLOW}Committing changes...${NC}"
git commit -m "$COMMIT_MESSAGE"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Commit failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Changes committed${NC}"
echo ""

# Push to remote
echo -e "${YELLOW}Pushing to GitHub...${NC}"
git push origin "$CURRENT_BRANCH"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Push failed${NC}"
    echo ""
    echo -e "${YELLOW}Common issues:${NC}"
    echo -e "  ${NC}1. Remote repository not configured${NC}"
    echo -e "     ${YELLOW}Solution: git remote add origin <your-repo-url>${NC}"
    echo -e "  ${NC}2. Authentication failed${NC}"
    echo -e "     ${YELLOW}Solution: Configure GitHub credentials or use SSH${NC}"
    echo -e "  ${NC}3. Branch not tracking remote${NC}"
    echo -e "     ${YELLOW}Solution: git push -u origin $CURRENT_BRANCH${NC}"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Successfully pushed to GitHub${NC}"
echo ""

# Show summary
echo -e "${CYAN}========================================"
echo -e "  Update Summary"
echo -e "========================================${NC}"
echo -e "${NC}Branch: $CURRENT_BRANCH${NC}"
echo -e "${NC}Commit: $COMMIT_MESSAGE${NC}"
echo -e "${GREEN}Status: Pushed to GitHub ✓${NC}"
echo ""

# Show last commit
echo -e "${YELLOW}Last commit details:${NC}"
git log -1 --stat
echo ""

echo -e "${CYAN}========================================"
echo -e "${GREEN}  GitHub update complete!"
echo -e "${CYAN}========================================${NC}"

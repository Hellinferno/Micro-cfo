#!/usr/bin/env bash
# Render Build Script

set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
alembic -c config/alembic.ini upgrade head

# Create necessary directories
mkdir -p data/initial_acts
mkdir -p legal_db
mkdir -p logs
mkdir -p temp_uploads
mkdir -p file_storage

echo "Build completed successfully!"

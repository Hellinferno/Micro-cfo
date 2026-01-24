#!/bin/bash
# Docker initialization script for MicroCFO

set -e

echo "=========================================="
echo "MicroCFO Docker Initialization"
echo "=========================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✓ PostgreSQL is ready"

# Wait for Redis to be ready
echo "Waiting for Redis..."
until redis-cli -h redis -a $REDIS_PASSWORD ping 2>/dev/null; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done
echo "✓ Redis is ready"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head
echo "✓ Migrations complete"

# Initialize legal database
echo "Initializing legal database..."
python scripts/setup_legal_db.py
echo "✓ Legal database initialized"

# Initialize scheme database
echo "Initializing scheme database..."
python scripts/setup_scheme_db.py
echo "✓ Scheme database initialized"

# Seed initial data (optional)
if [ "$SEED_DATA" = "true" ]; then
  echo "Seeding initial data..."
  python scripts/seed_data.py
  echo "✓ Data seeding complete"
fi

echo "=========================================="
echo "✓ Initialization complete!"
echo "=========================================="

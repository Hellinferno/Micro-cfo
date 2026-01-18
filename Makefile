# Makefile for MicroCFO Docker Operations

.PHONY: help build up down restart logs clean dev prod test db-init db-migrate

# Default target
help:
	@echo "MicroCFO Docker Commands:"
	@echo "  make build       - Build all Docker images"
	@echo "  make up          - Start all services (production)"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make clean       - Remove all containers, volumes, and images"
	@echo "  make dev         - Start development environment with hot reload"
	@echo "  make prod        - Start production environment"
	@echo "  make test        - Run tests in Docker"
	@echo "  make db-init     - Initialize database"
	@echo "  make db-migrate  - Run database migrations"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-frontend - Open shell in frontend container"

# Build all images
build:
	docker-compose build

# Start production environment
up:
	docker-compose up -d

# Start production environment (alias)
prod: up

# Start development environment
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Stop all services
down:
	docker-compose down

# Restart all services
restart: down up

# View logs
logs:
	docker-compose logs -f

# View backend logs only
logs-backend:
	docker-compose logs -f backend

# View frontend logs only
logs-frontend:
	docker-compose logs -f frontend

# Clean everything (WARNING: removes volumes)
clean:
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

# Initialize database
db-init:
	docker-compose exec backend python setup_legal_db.py
	docker-compose exec backend python setup_scheme_db.py

# Run database migrations (placeholder for future)
db-migrate:
	@echo "Database migrations not yet implemented"

# Open shell in backend container
shell-backend:
	docker-compose exec backend /bin/bash

# Open shell in frontend container
shell-frontend:
	docker-compose exec frontend /bin/sh

# Run tests in backend
test:
	docker-compose exec backend pytest -v

# Check service health
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend: UNHEALTHY"
	@curl -f http://localhost/health || echo "Frontend: UNHEALTHY"

# Show service status
status:
	docker-compose ps

# Pull latest images
pull:
	docker-compose pull

# Push images to registry (configure registry first)
push:
	docker-compose push

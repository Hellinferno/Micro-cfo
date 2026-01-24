.PHONY: help build up down logs restart clean test shell db-init health

help:
	@echo "MicroCFO Docker Commands:"
	@echo "  make build       - Build all Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make restart     - Restart all services"
	@echo "  make clean       - Remove all containers, volumes, and images"
	@echo "  make test        - Run tests in backend container"
	@echo "  make shell       - Open shell in backend container"
	@echo "  make db-init     - Initialize databases"
	@echo "  make health      - Check health of all services"

build:
	docker-compose build --no-cache

up:
	docker-compose up -d
	@echo "Services starting... Check status with 'make health'"

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-celery:
	docker-compose logs -f celery-worker

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker system prune -af

test:
	docker-compose exec backend pytest -v

shell:
	docker-compose exec backend /bin/bash

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

db-init:
	docker-compose exec backend python scripts/setup_legal_db.py
	docker-compose exec backend python scripts/setup_scheme_db.py
	docker-compose exec backend alembic upgrade head

health:
	@echo "Checking service health..."
	@docker-compose ps
	@echo "\nBackend health:"
	@curl -s http://localhost:8000/health || echo "Backend not responding"
	@echo "\nFrontend health:"
	@curl -s http://localhost/ > /dev/null && echo "Frontend OK" || echo "Frontend not responding"

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Docker Deployment Guide for MicroCFO

Complete guide for containerizing and deploying the MicroCFO application using Docker and Docker Compose.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This Docker setup provides:

- **Multi-stage builds** for optimized image sizes
- **PostgreSQL** for persistent data storage
- **Redis** for caching and session management
- **Nginx** for serving frontend and reverse proxy
- **Hot reload** in development mode
- **Health checks** for all services
- **Security best practices** (non-root users, minimal images)
- **Production-ready** configuration

## 📦 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

### Install Docker

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**macOS:**
```bash
brew install --cask docker
```

**Windows:**
Download Docker Desktop from https://www.docker.com/products/docker-desktop

## 🚀 Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/Hellinferno/Micro-cfo.git
cd Micro-cfo

# Copy environment template
cp .env.docker .env

# Edit .env with your configuration
nano .env
```

### 2. Set Required Environment Variables

Edit `.env` and set at minimum:

```bash
# Security (REQUIRED)
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
POSTGRES_PASSWORD=secure_database_password
REDIS_PASSWORD=secure_redis_password

# API Keys (REQUIRED for Visual Auditor)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Build and Start

```bash
# Using Make (recommended)
make build
make up

# Or using docker-compose directly
docker-compose build
docker-compose up -d
```

### 4. Initialize Databases

```bash
make db-init

# Or manually
docker-compose exec backend python setup_legal_db.py
docker-compose exec backend python setup_scheme_db.py
```

### 5. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🏗️ Architecture

### Services Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                       │
│                    (Nginx/Traefik)                      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌───────▼────────┐
│   Frontend     │       │    Backend     │
│   (Nginx)      │       │   (FastAPI)    │
│   Port: 80     │       │   Port: 8000   │
└────────────────┘       └───────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
            ┌───────▼──────┐ ┌──▼──────┐ ┌──▼──────┐
            │  PostgreSQL  │ │  Redis  │ │ ChromaDB│
            │  Port: 5432  │ │Port:6379│ │ (Volume)│
            └──────────────┘ └─────────┘ └─────────┘
```

### Container Details

| Service | Image | Purpose | Ports |
|---------|-------|---------|-------|
| frontend | nginx:alpine | React app + reverse proxy | 80 |
| backend | python:3.11-slim | FastAPI server | 8000 |
| postgres | postgres:16-alpine | Primary database | 5432 |
| redis | redis:7-alpine | Cache & sessions | 6379 |

### Volumes

- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence
- `legal_db`: ChromaDB legal documents
- `scheme_db`: ChromaDB subsidy schemes
- `temp_uploads`: Temporary file uploads
- `logs`: Application logs

## ⚙️ Configuration

### Environment Variables


#### Backend Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG` | Enable debug mode | `false` | No |
| `HOST` | Server host | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `JWT_SECRET_KEY` | JWT signing key | - | **Yes** |
| `GEMINI_API_KEY` | Google Gemini API | - | **Yes** |
| `DATABASE_URL` | PostgreSQL connection | Auto | No |
| `REDIS_URL` | Redis connection | Auto | No |

#### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_DB` | Database name | `microcfo` | No |
| `POSTGRES_USER` | Database user | `microcfo` | No |
| `POSTGRES_PASSWORD` | Database password | - | **Yes** |
| `REDIS_PASSWORD` | Redis password | - | **Yes** |

## 🔧 Development Setup

### Start Development Environment

```bash
# With hot reload enabled
make dev

# Or using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Development mode includes:
- **Hot reload** for backend (uvicorn --reload)
- **Hot reload** for frontend (Vite HMR)
- **Source code mounting** for instant changes
- **pgAdmin** at http://localhost:5050
- **Redis Commander** at http://localhost:8081

### Development Tools

**pgAdmin** (Database Management):
- URL: http://localhost:5050
- Email: admin@microcfo.com
- Password: admin

**Redis Commander** (Cache Management):
- URL: http://localhost:8081

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
docker-compose exec backend pytest test_integration_server.py -v

# Run with coverage
docker-compose exec backend pytest --cov=. --cov-report=html
```

### Accessing Logs

```bash
# All services
make logs

# Specific service
make logs-backend
make logs-frontend

# Follow logs
docker-compose logs -f backend
```

### Shell Access

```bash
# Backend shell
make shell-backend

# Frontend shell
make shell-frontend

# Database shell
docker-compose exec postgres psql -U microcfo -d microcfo
```

## 🚀 Production Deployment

### 1. Security Hardening

**Update .env with strong credentials:**

```bash
# Generate secure passwords
openssl rand -base64 32  # For JWT_SECRET_KEY
openssl rand -base64 24  # For POSTGRES_PASSWORD
openssl rand -base64 24  # For REDIS_PASSWORD
```

**Update .env:**
```bash
DEBUG=false
JWT_SECRET_KEY=<generated-secret>
POSTGRES_PASSWORD=<generated-password>
REDIS_PASSWORD=<generated-password>
```

### 2. Build Production Images

```bash
# Build optimized images
docker-compose build --no-cache

# Tag for registry
docker tag microcfo-backend:latest your-registry/microcfo-backend:v1.0.0
docker tag microcfo-frontend:latest your-registry/microcfo-frontend:v1.0.0
```

### 3. Deploy

```bash
# Start production services
make prod

# Or
docker-compose up -d

# Check health
make health
```

### 4. SSL/TLS Configuration

For production, use a reverse proxy with SSL:

**Using Traefik:**

```yaml
# docker-compose.prod.yml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@yourdomain.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
```

### 5. Monitoring

**Health Checks:**
```bash
# Check all services
docker-compose ps

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost/health
```

**Resource Usage:**
```bash
# Monitor resources
docker stats

# Check logs for errors
docker-compose logs --tail=100 backend | grep ERROR
```

## ☁️ Cloud Deployment

### AWS Deployment (ECS)

#### 1. Push Images to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create repositories
aws ecr create-repository --repository-name microcfo-backend
aws ecr create-repository --repository-name microcfo-frontend

# Tag and push
docker tag microcfo-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/microcfo-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/microcfo-backend:latest

docker tag microcfo-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/microcfo-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/microcfo-frontend:latest
```

#### 2. Create ECS Task Definition

```json
{
  "family": "microcfo",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/microcfo-backend:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "secrets": [
        {"name": "JWT_SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "GEMINI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ]
    }
  ]
}
```

#### 3. Required AWS Resources

- **RDS PostgreSQL** instance
- **ElastiCache Redis** cluster
- **EFS** for persistent volumes (legal_db, scheme_db)
- **ALB** for load balancing
- **Secrets Manager** for sensitive data

### Google Cloud Platform (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/microcfo-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/microcfo-frontend ./frontend

# Deploy backend
gcloud run deploy microcfo-backend \
  --image gcr.io/PROJECT_ID/microcfo-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://... \
  --set-secrets JWT_SECRET_KEY=jwt-secret:latest

# Deploy frontend
gcloud run deploy microcfo-frontend \
  --image gcr.io/PROJECT_ID/microcfo-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure (Container Instances)

```bash
# Login to Azure
az login

# Create resource group
az group create --name microcfo-rg --location eastus

# Create container registry
az acr create --resource-group microcfo-rg --name microcfoacr --sku Basic

# Push images
az acr login --name microcfoacr
docker tag microcfo-backend microcfoacr.azurecr.io/microcfo-backend:latest
docker push microcfoacr.azurecr.io/microcfo-backend:latest

# Deploy container group
az container create \
  --resource-group microcfo-rg \
  --name microcfo-backend \
  --image microcfoacr.azurecr.io/microcfo-backend:latest \
  --cpu 2 --memory 4 \
  --ports 8000 \
  --environment-variables DATABASE_URL=postgresql://... \
  --secure-environment-variables JWT_SECRET_KEY=...
```

## 🐛 Troubleshooting

### Common Issues

#### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common causes:
# 1. Missing API keys
docker-compose exec backend env | grep GEMINI_API_KEY

# 2. Database connection
docker-compose exec backend python -c "import psycopg2; print('OK')"

# 3. Port conflicts
lsof -i :8000
```

#### Frontend can't connect to backend

```bash
# Check network
docker network inspect microcfo_microcfo-network

# Test backend from frontend container
docker-compose exec frontend wget -O- http://backend:8000/health

# Check CORS configuration
curl -H "Origin: http://localhost" -I http://localhost:8000/health
```

#### Database initialization fails

```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec postgres psql -U microcfo -d microcfo -f /docker-entrypoint-initdb.d/init.sql
```

#### Out of disk space

```bash
# Clean up Docker
docker system prune -a --volumes

# Check volume sizes
docker system df -v
```

### Performance Optimization

#### Reduce Image Sizes

```bash
# Check image sizes
docker images | grep microcfo

# Backend should be ~500MB
# Frontend should be ~50MB
```

#### Database Performance

```sql
-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Add indexes if needed
CREATE INDEX idx_custom ON table_name(column_name);
```

#### Redis Cache Tuning

```bash
# Check cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace

# Monitor memory
docker-compose exec redis redis-cli INFO memory
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)

## 🔐 Security Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT secret (32+ characters)
- [ ] Enable SSL/TLS in production
- [ ] Restrict database access to backend only
- [ ] Use secrets management (AWS Secrets Manager, etc.)
- [ ] Enable Docker security scanning
- [ ] Regular security updates
- [ ] Implement rate limiting
- [ ] Enable audit logging
- [ ] Backup databases regularly

## 📝 Maintenance

### Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U microcfo microcfo > backup.sql

# Backup volumes
docker run --rm -v microcfo_legal_db:/data -v $(pwd):/backup alpine tar czf /backup/legal_db.tar.gz /data
```

### Restore

```bash
# Restore PostgreSQL
docker-compose exec -T postgres psql -U microcfo microcfo < backup.sql

# Restore volumes
docker run --rm -v microcfo_legal_db:/data -v $(pwd):/backup alpine tar xzf /backup/legal_db.tar.gz -C /
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Rebuild with latest code
git pull
docker-compose build --no-cache

# Rolling update (zero downtime)
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
```

---

**Need Help?** Open an issue at https://github.com/Hellinferno/Micro-cfo/issues

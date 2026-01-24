# Docker Quick Start Guide

Get MicroCFO running with Docker in 5 minutes!

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB free disk space

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/Hellinferno/Micro-cfo.git
cd Micro-cfo
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.docker .env

# Edit with your values (REQUIRED)
nano .env  # or use any text editor
```

**Minimum required configuration:**
```bash
# Security (REQUIRED)
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
POSTGRES_PASSWORD=secure_database_password
REDIS_PASSWORD=secure_redis_password

# AI API Key (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Start Services
```bash
# Build and start
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Initialize Databases
```bash
# Run database setup
docker-compose exec backend python scripts/setup_legal_db.py
docker-compose exec backend python scripts/setup_scheme_db.py
```

### 5. Access Application
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Task Monitor)**: http://localhost:5555

## Common Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Clean everything
docker-compose down -v
docker system prune -af
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs backend

# Verify environment
docker-compose config
```

### Database connection errors
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose up -d
```

### Port conflicts
```bash
# Change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=8080
```

## Next Steps

- Read [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed documentation
- Check [DOCKER_TROUBLESHOOTING.md](DOCKER_TROUBLESHOOTING.md) for common issues
- See [README.md](README.md) for API usage

## Need Help?

Open an issue at: https://github.com/Hellinferno/Micro-cfo/issues

# 🐳 Docker Quick Start Guide

Get MicroCFO running in 5 minutes with Docker!

## Prerequisites

- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- 4GB RAM available
- 10GB disk space

## Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Hellinferno/Micro-cfo.git
cd Micro-cfo
```

### 2️⃣ Configure Environment

```bash
# Copy the environment template
cp .env.docker .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Minimum required changes in `.env`:**

```bash
# Security - Generate strong passwords!
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-now
POSTGRES_PASSWORD=change-this-secure-password
REDIS_PASSWORD=change-this-redis-password

# API Keys - Get from Google AI Studio
GEMINI_API_KEY=your_gemini_api_key_here
```

💡 **Tip:** Generate secure passwords:
```bash
openssl rand -base64 32
```

### 3️⃣ Start Everything

```bash
# Build and start all services
docker-compose up -d

# Watch the logs (optional)
docker-compose logs -f
```

### 4️⃣ Initialize Databases

```bash
# Setup legal and scheme databases
docker-compose exec backend python setup_legal_db.py
docker-compose exec backend python setup_scheme_db.py
```

### 5️⃣ Access the Application

🎉 **You're done!** Access:

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Default Credentials

**Admin User:**
- Email: `admin@microcfo.com`
- Password: `admin123`

⚠️ **Change this immediately in production!**

## Common Commands

### Using Make (Recommended)

```bash
make help          # Show all available commands
make build         # Build Docker images
make up            # Start services
make down          # Stop services
make logs          # View logs
make restart       # Restart all services
make test          # Run tests
make clean         # Clean everything (⚠️ removes data)
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Run commands in containers
docker-compose exec backend python manage.py
docker-compose exec postgres psql -U microcfo
```

## Development Mode

For development with hot reload:

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use Make
make dev
```

Development mode includes:
- ✅ Hot reload for backend and frontend
- ✅ Source code mounted (changes reflect immediately)
- ✅ pgAdmin at http://localhost:5050
- ✅ Redis Commander at http://localhost:8081

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000  # or :80, :5432, etc.

# Change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=8080
```

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common fixes:
# 1. Verify API keys in .env
docker-compose exec backend env | grep GEMINI_API_KEY

# 2. Restart services
docker-compose restart backend

# 3. Rebuild if needed
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Reset database (⚠️ deletes data)
docker-compose down -v
docker-compose up -d
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Check disk usage
docker system df
```

## Stopping and Cleaning Up

```bash
# Stop services (keeps data)
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v

# Complete cleanup
make clean
```

## Next Steps

- 📖 Read the [Full Docker Deployment Guide](DOCKER_DEPLOYMENT.md)
- ☁️ Deploy to [AWS/GCP/Azure](DOCKER_DEPLOYMENT.md#cloud-deployment)
- 🔒 Review [Security Best Practices](SECURITY.md)
- 🧪 Run the [Test Suite](TEST_STATUS_SUMMARY.md)

## Need Help?

- 📝 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/Hellinferno/Micro-cfo/issues)
- 💬 [Discussions](https://github.com/Hellinferno/Micro-cfo/discussions)

---

**Happy Coding! 🚀**

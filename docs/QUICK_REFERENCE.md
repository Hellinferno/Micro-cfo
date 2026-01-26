# MicroCFO Quick Reference Guide

## Docker Commands

### Basic Operations
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart services
docker-compose restart
```

### Using Makefile (Recommended)
```bash
make build      # Build images
make up         # Start services
make down       # Stop services
make logs       # View logs
make restart    # Restart all
make test       # Run tests
make shell      # Backend shell
make db-init    # Initialize databases
make health     # Check health
make clean      # Remove everything
```

### Development Mode
```bash
# Start with hot reload
make dev

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Access tools
# pgAdmin: http://localhost:5050 (admin@microcfo.com / admin)
# Redis Commander: http://localhost:8081
```

### Production Mode
```bash
make prod

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## GitHub Commands

### Push Changes
```bash
# Unix/Linux/Mac
./scripts/github-push.sh

# Windows PowerShell
.\scripts\github-push.ps1

# Manual
git add .
git commit -m "your message"
git push origin main
```

### Check Status
```bash
git status
git log --oneline -5
git remote -v
```

## Application URLs

### Local Development
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Tasks)**: http://localhost:5555
- **pgAdmin**: http://localhost:5050 (dev mode)
- **Redis Commander**: http://localhost:8081 (dev mode)

## Environment Variables

### Required
```bash
JWT_SECRET_KEY=your-secret-key-min-32-chars
POSTGRES_PASSWORD=secure-password
REDIS_PASSWORD=secure-password
GEMINI_API_KEY=your-gemini-api-key
```

### Optional
```bash
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AZURE_FORM_RECOGNIZER_KEY=your-azure-key
ENCRYPTION_KEY=your-encryption-key
```

## Database Operations

### Initialize
```bash
docker-compose exec backend python scripts/setup_legal_db.py
docker-compose exec backend python scripts/setup_scheme_db.py
```

### Migrations
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Backup
```bash
# PostgreSQL
docker-compose exec postgres pg_dump -U microcfo microcfo > backup.sql

# Restore
docker-compose exec -T postgres psql -U microcfo microcfo < backup.sql
```

## Testing

### Run Tests
```bash
# All tests
docker-compose exec backend pytest -v

# Specific test
docker-compose exec backend pytest tests/test_integration_server.py -v

# With coverage
docker-compose exec backend pytest --cov=. --cov-report=html
```

### Local Testing (without Docker)
```bash
# Activate venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows

# Run tests
pytest tests/ -v
```

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs backend

# Verify config
docker-compose config

# Check ports
netstat -an | grep 8000  # Unix
netstat -an | findstr 8000  # Windows
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose up -d
```

### Clean Everything
```bash
# Stop and remove everything
docker-compose down -v

# Remove all Docker data
docker system prune -af --volumes
```

### Permission Issues (Unix)
```bash
# Fix script permissions
chmod +x scripts/*.sh

# Fix file ownership
sudo chown -R $USER:$USER .
```

## GitHub Actions

### View Workflow Status
1. Go to repository on GitHub
2. Click "Actions" tab
3. View workflow runs

### Re-run Failed Workflow
1. Click on failed workflow
2. Click "Re-run jobs"
3. Select "Re-run failed jobs"

### Check Secrets
1. Settings → Secrets and variables → Actions
2. Verify GEMINI_API_KEY exists
3. Add CODECOV_TOKEN (optional)

## Common Issues

### Port Already in Use
```bash
# Change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=8080
POSTGRES_PORT=5433
```

### Out of Disk Space
```bash
# Clean Docker
docker system prune -af --volumes

# Check space
df -h  # Unix
dir    # Windows
```

### API Key Not Working
```bash
# Verify in container
docker-compose exec backend env | grep GEMINI_API_KEY

# Update .env and restart
docker-compose restart backend
```

## File Locations

### Configuration
- `.env` - Environment variables
- `docker-compose.yml` - Main orchestration
- `Dockerfile` - Backend image
- `frontend/Dockerfile` - Frontend image

### Data
- `legal_db/` - Legal database
- `scheme_db/` - Scheme database
- `temp_uploads/` - Temporary files
- `logs/` - Application logs

### Scripts
- `scripts/setup_legal_db.py` - Initialize legal DB
- `scripts/setup_scheme_db.py` - Initialize scheme DB
- `scripts/docker-init.sh` - Docker initialization
- `scripts/github-push.sh` - GitHub push script

## Quick Links

- **Documentation**: [README.md](README.md)
- **Docker Guide**: [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)
- **GitHub Guide**: [GITHUB_UPDATE_GUIDE.md](GITHUB_UPDATE_GUIDE.md)
- **Contributing**: [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)
- **Issues**: https://github.com/Hellinferno/Micro-cfo/issues

## Support

- Open an issue for bugs
- Check documentation for guides
- Review closed issues for solutions
- Use GitHub Discussions for questions

---

**Keep this file handy for quick reference!** 📚

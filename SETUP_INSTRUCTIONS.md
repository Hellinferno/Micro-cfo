# 🚀 Quick Setup Instructions

## Before You Start

You need a **Google Gemini API Key** for the Visual Auditor to work.

### Get Your Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

### Add API Key to .env

Open `.env` file and replace this line:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

With your actual key:
```
GEMINI_API_KEY=AIzaSyC...your-actual-key-here
```

## Option 1: Automated Setup (Recommended)

Run the setup script:
```powershell
.\docker-setup.ps1
```

This will:
- ✅ Check Docker status
- ✅ Build images
- ✅ Start services
- ✅ Initialize databases
- ✅ Show access URLs

## Option 2: Manual Setup

### Step 1: Build Images
```bash
docker-compose build
```

### Step 2: Start Services
```bash
docker-compose up -d
```

### Step 3: Initialize Databases
```bash
docker-compose exec backend python setup_legal_db.py
docker-compose exec backend python setup_scheme_db.py
```

## Access Your Application

Once setup is complete:

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Default Credentials

```
Email: admin@microcfo.com
Password: admin123
```

⚠️ **Change these immediately in production!**

## Troubleshooting

### Docker not running
```powershell
# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### Port conflicts
If port 80 or 8000 is already in use, edit `.env`:
```
FRONTEND_PORT=8080
BACKEND_PORT=8001
```

### View logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
```

## Next Steps

1. ✅ Complete setup
2. 📖 Read [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for advanced configuration
3. 🧪 Run tests: `docker-compose exec backend pytest -v`
4. 🚀 Deploy to cloud: See [Cloud Deployment Guide](DOCKER_DEPLOYMENT.md#cloud-deployment)

## Need Help?

- 📝 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/Hellinferno/Micro-cfo/issues)
- 💬 [Quick Start Guide](DOCKER_QUICKSTART.md)

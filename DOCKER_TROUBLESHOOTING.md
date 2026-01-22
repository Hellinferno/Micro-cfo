# Docker Desktop Troubleshooting Guide

## Current Issue
**Error**: `request returned 500 Internal Server Error for API route`  
**Cause**: Docker Desktop Engine communication failure  
**Status**: Docker Desktop is running but WSL2 backend is not responding

## Quick Fixes (Try in Order)

### 1. Restart Docker Desktop (Recommended)
```powershell
# Stop Docker Desktop
Stop-Process -Name "Docker Desktop" -Force

# Wait 10 seconds
Start-Sleep -Seconds 10

# Start Docker Desktop (from Start Menu or)
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait for Docker to fully start (30-60 seconds)
Start-Sleep -Seconds 60

# Test Docker
docker ps
```

### 2. Restart WSL2 Backend
```powershell
# Shutdown WSL
wsl --shutdown

# Wait 5 seconds
Start-Sleep -Seconds 5

# Restart Docker Desktop
# (It will automatically restart WSL)
```

### 3. Reset Docker Desktop
1. Open Docker Desktop
2. Go to Settings (gear icon)
3. Click "Troubleshoot" tab
4. Click "Reset to factory defaults"
5. Confirm and wait for reset
6. Restart Docker Desktop

### 4. Check Docker Desktop Settings
1. Open Docker Desktop
2. Go to Settings → General
3. Ensure "Use WSL 2 based engine" is checked
4. Go to Settings → Resources → WSL Integration
5. Enable integration for your WSL distributions
6. Click "Apply & Restart"

### 5. Reinstall Docker Desktop (Last Resort)
```powershell
# Uninstall Docker Desktop
winget uninstall Docker.DockerDesktop

# Or use Control Panel → Programs → Uninstall

# Download latest version
# https://www.docker.com/products/docker-desktop/

# Install and restart computer
```

## Verification Steps

After trying any fix, verify Docker is working:

```powershell
# Check Docker version
docker version

# Check Docker info
docker info

# List containers
docker ps

# Test with hello-world
docker run hello-world
```

## Once Docker is Fixed

Run these commands to update MicroCFO:

```powershell
# Stop existing containers
docker compose down

# Remove old images (optional)
docker compose down --rmi all

# Build fresh images
docker compose build --no-cache

# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

## Common Docker Desktop Issues on Windows

### Issue 1: WSL2 Not Installed
**Solution**: Install WSL2
```powershell
wsl --install
# Restart computer
```

### Issue 2: Virtualization Disabled in BIOS
**Solution**: 
1. Restart computer
2. Enter BIOS (usually F2, F10, or Del key)
3. Enable Intel VT-x or AMD-V
4. Save and exit

### Issue 3: Hyper-V Conflicts
**Solution**: Ensure Hyper-V is enabled
```powershell
# Run as Administrator
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
# Restart computer
```

### Issue 4: Docker Desktop Service Not Running
**Solution**: Start Docker Desktop service
```powershell
# Run as Administrator
Start-Service com.docker.service
```

### Issue 5: Corrupted Docker Data
**Solution**: Clear Docker data
```powershell
# Stop Docker Desktop
Stop-Process -Name "Docker Desktop" -Force

# Delete Docker data (WARNING: Removes all containers/images)
Remove-Item -Recurse -Force "$env:APPDATA\Docker"
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker"

# Restart Docker Desktop
```

## Alternative: Use Docker without Docker Desktop

If Docker Desktop continues to have issues, you can use Docker in WSL2 directly:

```bash
# In WSL2 terminal
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo service docker start

# Test
docker ps
```

## Current System Status

**Docker Client**: ✅ Working (v29.1.3)  
**Docker Engine**: ❌ Not responding (500 error)  
**WSL2**: ⚠️ May need restart  
**Docker Desktop**: ⚠️ Running but not communicating

## Recommended Action

**Try this first**:
1. Close Docker Desktop completely
2. Run: `wsl --shutdown`
3. Wait 10 seconds
4. Open Docker Desktop
5. Wait 60 seconds for full startup
6. Test: `docker ps`

If that doesn't work, try the "Reset to factory defaults" option in Docker Desktop settings.

## Support Resources

- Docker Desktop Documentation: https://docs.docker.com/desktop/
- Docker Desktop Issues: https://github.com/docker/for-win/issues
- WSL2 Documentation: https://docs.microsoft.com/en-us/windows/wsl/

## Contact

If issues persist after trying all solutions:
1. Check Docker Desktop logs: Settings → Troubleshoot → View logs
2. Check Windows Event Viewer for Docker-related errors
3. Post issue on Docker Desktop GitHub with logs

---

**Last Updated**: January 22, 2026  
**Docker Version**: 29.1.3  
**OS**: Windows with WSL2

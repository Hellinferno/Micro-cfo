# MicroCFO Deployment Checklist

Use this checklist to ensure proper deployment of MicroCFO with Docker and GitHub integration.

## Pre-Deployment

### 1. Environment Setup
- [ ] Copy `.env.docker` to `.env`
- [ ] Generate secure JWT secret key (min 32 characters)
- [ ] Generate secure database password
- [ ] Generate secure Redis password
- [ ] Add Gemini API key
- [ ] (Optional) Add AWS credentials
- [ ] (Optional) Add Azure credentials
- [ ] (Optional) Generate encryption key

### 2. Verify Files
- [ ] `docker-compose.yml` exists
- [ ] `Dockerfile` exists
- [ ] `.dockerignore` exists
- [ ] `Makefile` exists
- [ ] `frontend/Dockerfile` exists
- [ ] `.env` file configured

### 3. System Requirements
- [ ] Docker Engine 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] 4GB RAM available
- [ ] 10GB disk space available
- [ ] Ports 80, 8000, 5432, 6379 available

## Docker Deployment

### 4. Build Images
```bash
make build
# or
docker-compose build --no-cache
```
- [ ] Backend image built successfully
- [ ] Frontend image built successfully
- [ ] No build errors

### 5. Start Services
```bash
make up
# or
docker-compose up -d
```
- [ ] PostgreSQL started
- [ ] Redis started
- [ ] Backend started
- [ ] Frontend started
- [ ] Celery worker started
- [ ] Flower started

### 6. Verify Services
```bash
make health
# or
docker-compose ps
```
- [ ] All services show "Up" status
- [ ] All health checks passing
- [ ] No restart loops

### 7. Initialize Databases
```bash
make db-init
# or
docker-compose exec backend python scripts/setup_legal_db.py
docker-compose exec backend python scripts/setup_scheme_db.py
```
- [ ] Legal database initialized
- [ ] Scheme database initialized
- [ ] No initialization errors

### 8. Test Application
- [ ] Frontend accessible at http://localhost
- [ ] Backend API accessible at http://localhost:8000
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Flower accessible at http://localhost:5555
- [ ] Can upload invoice image
- [ ] Can query legal database
- [ ] Can search subsidies

## GitHub Integration

### 9. Push to GitHub
```bash
./scripts/github-push.sh  # Unix
# or
.\scripts\github-push.ps1  # Windows
```
- [ ] All files committed
- [ ] Pushed to main branch
- [ ] No push errors

### 10. Configure GitHub Secrets
Navigate to: Settings → Secrets and variables → Actions
- [ ] Add `GEMINI_API_KEY`
- [ ] (Optional) Add `CODECOV_TOKEN`
- [ ] (Optional) Add `AWS_ACCESS_KEY_ID`
- [ ] (Optional) Add `AWS_SECRET_ACCESS_KEY`

### 11. Enable GitHub Actions
Navigate to: Settings → Actions → General
- [ ] Allow all actions and reusable workflows
- [ ] Read and write permissions for GITHUB_TOKEN
- [ ] Allow GitHub Actions to create and approve pull requests

### 12. Set Up Branch Protection
Navigate to: Settings → Branches → Add rule
- [ ] Require pull request reviews (1 approval)
- [ ] Require status checks to pass
  - [ ] lint-and-test
  - [ ] integration-tests
  - [ ] docker-build
- [ ] Require branches to be up to date
- [ ] Require conversation resolution

### 13. Verify CI/CD
- [ ] Create test branch
- [ ] Make small change
- [ ] Create pull request
- [ ] CI pipeline runs successfully
- [ ] All checks pass
- [ ] Docker images build

### 14. Enable Dependabot
Navigate to: Settings → Security → Code security and analysis
- [ ] Dependabot alerts enabled
- [ ] Dependabot security updates enabled
- [ ] Dependabot version updates enabled

## Production Deployment

### 15. Security Hardening
- [ ] Change all default passwords
- [ ] Use strong JWT secret (32+ characters)
- [ ] Enable SSL/TLS in production
- [ ] Restrict database access
- [ ] Use secrets management (AWS Secrets Manager, etc.)
- [ ] Enable Docker security scanning
- [ ] Implement rate limiting
- [ ] Enable audit logging

### 16. Production Configuration
```bash
make prod
# or
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
- [ ] Production overrides applied
- [ ] Resource limits configured
- [ ] Logging configured
- [ ] Auto-restart enabled
- [ ] Nginx reverse proxy (if using)

### 17. Monitoring Setup
- [ ] Health checks configured
- [ ] Log aggregation setup
- [ ] Error tracking (Sentry, etc.)
- [ ] Performance monitoring
- [ ] Uptime monitoring
- [ ] Alert notifications

### 18. Backup Configuration
- [ ] Database backup schedule
- [ ] Volume backup schedule
- [ ] Backup verification
- [ ] Restore procedure tested
- [ ] Backup retention policy

## Post-Deployment

### 19. Documentation
- [ ] Update README with deployment info
- [ ] Document custom configurations
- [ ] Create runbook for operations
- [ ] Document troubleshooting steps
- [ ] Update API documentation

### 20. Testing
- [ ] Run full test suite
- [ ] Test all API endpoints
- [ ] Test file uploads
- [ ] Test database queries
- [ ] Test async tasks
- [ ] Load testing (if applicable)

### 21. Team Onboarding
- [ ] Share access credentials
- [ ] Provide documentation links
- [ ] Conduct walkthrough
- [ ] Set up development environments
- [ ] Configure IDE/editor

### 22. Monitoring & Maintenance
- [ ] Set up monitoring dashboards
- [ ] Configure alerts
- [ ] Schedule regular updates
- [ ] Plan maintenance windows
- [ ] Document incident response

## Verification

### Final Checks
- [ ] All services running
- [ ] All tests passing
- [ ] CI/CD pipeline working
- [ ] Documentation complete
- [ ] Team trained
- [ ] Backups configured
- [ ] Monitoring active
- [ ] Security hardened

### Performance Checks
- [ ] Response times acceptable
- [ ] Database queries optimized
- [ ] Cache hit rate good
- [ ] Resource usage normal
- [ ] No memory leaks
- [ ] No error spikes

### Security Checks
- [ ] No exposed secrets
- [ ] SSL/TLS configured
- [ ] Authentication working
- [ ] Authorization working
- [ ] Audit logs enabled
- [ ] Rate limiting active

## Rollback Plan

### If Issues Occur
1. **Stop services**
   ```bash
   docker-compose down
   ```

2. **Check logs**
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

3. **Restore from backup**
   ```bash
   docker-compose exec -T postgres psql -U microcfo microcfo < backup.sql
   ```

4. **Restart services**
   ```bash
   docker-compose up -d
   ```

5. **Verify health**
   ```bash
   make health
   ```

## Support Contacts

- **Technical Issues**: Open GitHub issue
- **Security Issues**: Email security@yourdomain.com
- **Documentation**: Check README.md and docs/
- **Community**: GitHub Discussions

## Sign-Off

### Deployment Team
- [ ] Developer: _________________ Date: _______
- [ ] DevOps: ___________________ Date: _______
- [ ] QA: ______________________ Date: _______
- [ ] Manager: _________________ Date: _______

### Production Approval
- [ ] All checks passed
- [ ] Team trained
- [ ] Documentation complete
- [ ] Monitoring active
- [ ] Approved for production

**Deployment Date**: _______________
**Deployed By**: ___________________
**Version**: _______________________

---

**Congratulations on your deployment!** 🎉

For ongoing support, refer to:
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Detailed guide
- [GITHUB_CONFIGURATION_CHECKLIST.md](GITHUB_CONFIGURATION_CHECKLIST.md) - GitHub setup


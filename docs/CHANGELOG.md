# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive Docker setup with docker-compose
- Multi-stage Dockerfile for optimized builds
- Docker development and production configurations
- GitHub Actions CI/CD workflows
- Automated Docker image building and publishing
- Issue templates for bugs and feature requests
- Pull request template
- Contributing guidelines
- Code of conduct
- Automated testing in CI pipeline
- Docker health checks
- Makefile for common Docker operations
- Quick start guides for Docker deployment

### Changed
- Updated documentation with Docker instructions
- Improved project structure for containerization
- Enhanced security with non-root Docker users

### Fixed
- Docker networking configuration
- Environment variable handling in containers

## [2.0.0] - 2026-01-18

### Added
- Phase 4: Business Logic & Integration
  - ERP Adapters (Tally, Zoho Books, CSV, JSON)
  - User Onboarding system
  - Industry and turnover tier selection
  - Contextual filtering
- Security & Compliance features
  - AES-256 encryption at rest
  - Comprehensive audit trails
  - Legal disclaimers system
  - Guardrails and verification
- Frontend Integration
  - Real API calls to backend
  - Disclaimer modal and banner
  - File upload handling
  - Dynamic action cards

### Changed
- Enhanced database models with encryption
- Updated API routers with disclaimers
- Improved error handling
- Better logging and monitoring

## [1.0.0] - 2024-01-15

### Added
- Agent A: Visual Auditor with Gemini 2.5 Flash
- Agent B: Legislative Sentinel with RAG
- Agent C: Subsidy Hunter
- Agent D: Negotiator
- Legal database with structure-aware chunking
- Scheme database for subsidies
- Real-time legal monitoring
- Async task queue with Celery
- PostgreSQL database integration
- Redis caching
- FastAPI backend
- React frontend
- Comprehensive test suite

### Security
- JWT authentication
- Password hashing with bcrypt
- Rate limiting
- PII redaction
- Audit logging

[Unreleased]: https://github.com/Hellinferno/Micro-cfo/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/Hellinferno/Micro-cfo/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Hellinferno/Micro-cfo/releases/tag/v1.0.0

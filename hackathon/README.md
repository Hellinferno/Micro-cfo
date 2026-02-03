# MicroCFO - Hackathon Documentation

**AI-Powered Autonomous CFO Assistant for Indian SMBs**

---

## 📋 Quick Links

| Document | Description |
|----------|-------------|
| [requirements.md](requirements.md) | Functional & non-functional requirements |
| [design.md](design.md) | Technical architecture & design |

---

## 🎯 Project Overview

MicroCFO is an AI-powered autonomous CFO assistant that automates financial operations for small to medium businesses in India. It handles invoice processing, legal compliance, subsidy discovery, and vendor negotiations.

### Core Agents

| Agent | Name | Function |
|-------|------|----------|
| A | Visual Auditor | Invoice processing & fraud detection |
| B | Legislative Sentinel | Legal compliance & monitoring |
| C | Subsidy Hunter | Government scheme discovery |
| D | Negotiator | Payment negotiation drafts |

### Key Features

- ✅ **Gemini 2.5 Flash** for invoice image processing
- ✅ **Structure-aware RAG** for legal queries
- ✅ **A/B Testing** for negotiation strategies
- ✅ **ERP Integration** (Tally, Zoho Books)
- ✅ **AES-256 Encryption** for sensitive data
- ✅ **Comprehensive Audit Trails**

---

## 🏗️ Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite + Tailwind |
| Backend | FastAPI + FastMCP |
| Database | PostgreSQL + ChromaDB |
| AI | Gemini 2.5/3 Flash |
| Storage | AWS S3 / Local |

---

## 📊 Target Metrics

| Metric | Target |
|--------|--------|
| Invoice Processing | < 30 seconds |
| Legal Queries | < 5 seconds |
| Uptime | 99.5% |
| Accuracy | 95%+ |

---

## 🔒 Security Highlights

- AES-256 encryption at rest
- JWT authentication
- Rate limiting (100 req/min)
- Draft-only mode for negotiations
- Prominent AI disclaimers

---

**Last Updated**: February 3, 2026  
**Status**: ✅ Production Ready

# MicroCFO - Requirements Document

**Version**: 2.2.0  
**Last Updated**: February 7, 2026  
**Status**: ✅ Production Ready

---

## 1. Executive Summary

### 1.1 Product Vision
MicroCFO is an AI-powered autonomous CFO assistant designed for small to medium businesses in India. It automates financial operations including invoice processing, legal compliance monitoring, subsidy discovery, and vendor negotiations while maintaining conservative CA-style risk assessment.

### 1.2 Target Users
- Small to medium businesses in India (turnover: < ₹5 Cr to > ₹50 Cr)
- Chartered Accountants and financial consultants
- Companies requiring GST, Income Tax, and Companies Act compliance
- Businesses across 12 industry sectors

### 1.3 Core Value Proposition
- **Automation**: Reduce manual financial operations by 70%
- **Compliance**: Proactive legal monitoring and risk assessment
- **Integration**: Direct export to Tally, Zoho Books, and other ERP systems
- **Intelligence**: AI-powered decision making with human oversight

---

## 2. Functional Requirements

### 2.1 Agent A - Visual Auditor

| Req ID | Requirement | Status |
|--------|-------------|--------|
| FR-A1 | Process invoice images (PDF, PNG, JPG) using Gemini 2.5 Flash | ✅ |
| FR-A2 | Extract structured data (vendor, GSTIN, amounts, line items) | ✅ |
| FR-A3 | Categorize line items (Capital Goods, Raw Material, Personal, Service) | ✅ |
| FR-A4 | Detect invoice tampering and fraud indicators | ✅ |
| FR-A5 | Identify handwritten invoices with confidence scores | ✅ |
| FR-A6 | Validate GSTIN presence for ITC eligibility | ✅ |
| FR-A7 | Check invoice staleness (>30 days warning) | ✅ |
| FR-A8 | Auto-trigger Agent C for capital goods > ₹1 Lakh | ✅ |
| FR-A9 | Auto-trigger Agent B for personal/entertainment items | ✅ |
| FR-A10 | Conservative CA-style recommendations | ✅ |

**Specifications:**
- Max File Size: 50 MB
- Processing Time: < 30 seconds
- Confidence threshold: 0.7 triggers manual review

### 2.2 Agent B - Legislative Sentinel

| Req ID | Requirement | Status |
|--------|-------------|--------|
| FR-B1 | Ingest legal documents (14+ Acts/Rules including 2025 updates) | ✅ |
| FR-B2 | Extract metadata (turnover thresholds, sectors, dates) | ✅ |
| FR-B3 | CA-logic based text chunking | ✅ |
| FR-B4 | Semantic + keyword hybrid search | ✅ |
| FR-B5 | Turnover tier and sector filtering | ✅ |
| FR-B6 | Risk assessment (LOW/MEDIUM/HIGH) | ✅ |
| FR-B7 | Monitor CBIC, MCA, IT Department websites | ✅ |
| FR-B8 | User profile-based notification relevance | ✅ |
| FR-B9 | Multi-channel alerts (WhatsApp, Email, In-app) | ✅ |

### 2.3 Agent C - Subsidy Hunter

| Req ID | Requirement | Status |
|--------|-------------|--------|
| FR-C1 | Maintain government subsidy scheme database with Real-time Web Scraping | ✅ |
| FR-C2 | Match schemes to user profile (industry, turnover) | ✅ |
| FR-C3 | Calculate estimated benefits | ✅ |
| FR-C4 | Provide application guidance and deadlines | ✅ |

### 2.4 Agent D - Negotiator

| Req ID | Requirement | Status |
|--------|-------------|--------|
| FR-D1 | Router logic for strategy determination | ✅ |
| FR-D2 | Financial context analysis (cash flow, aging) | ✅ |
| FR-D3 | Gemini 3 Flash content generation | ✅ |
| FR-D4 | A/B testing (Relationship vs Transactional) | ✅ |
| FR-D5 | **CRITICAL**: Draft-only mode, never auto-send | ✅ |

**Negotiation Intents:**
- Credit Extension: When cash flow is tight
- Payment Chase: When invoices are overdue
- Early Payment Offer: When cash surplus exists

### 2.5 Business Logic & Integration

| Req ID | Requirement | Status |
|--------|-------------|--------|
| FR-E1 | Export to Tally ERP 9 / Tally Prime (XML/CSV) | ✅ |
| FR-E2 | Export to Zoho Books (JSON API) | ✅ |
| FR-E3 | Standard format export (CSV, JSON) | ✅ |
| FR-O1 | User onboarding with company capture | ✅ |
| FR-O2 | 12 industry type support | ✅ |
| FR-O3 | 4 turnover tiers (Micro/Small/Medium/Large) | ✅ |
| FR-O4 | 9-step onboarding flow | ✅ |
| FR-O5 | Input validation (GSTIN, PAN, Email, Phone) | ✅ |

### 2.6 Security & Compliance

| Req ID | Requirement | Status |
|--------|-------------|--------|
| FR-S1 | AES-256 encryption at rest | ✅ |
| FR-S2 | S3 server-side encryption | ✅ |
| FR-S3 | Local storage fallback | ✅ |
| FR-S4 | Comprehensive audit logging (30+ action types) | ✅ |
| FR-S5 | Audit log queries and export | ✅ |
| FR-S6 | 4 severity levels (INFO/WARNING/ERROR/CRITICAL) | ✅ |
| FR-S7 | Main disclaimer modal on first visit | ✅ |
| FR-S8 | 7 disclaimer types | ✅ |
| FR-S9 | Persistent disclaimer banner | ✅ |
| FR-S10 | Negotiator draft-only guardrail | ✅ |
| FR-S11 | Invoice verification requirement | ✅ |
| FR-S12 | Professional consultation recommendations | ✅ |

---

## 3. Non-Functional Requirements

### 3.1 Performance
| Metric | Requirement |
|--------|-------------|
| Invoice Processing | < 30 seconds |
| Legal Queries | < 5 seconds |
| API Response (P95) | < 2 seconds |
| Concurrent Users | 100 |
| Database Queries | < 1 second |

### 3.2 Scalability
| Metric | Capacity |
|--------|----------|
| Daily Invoices | 10,000 |
| Legal Chunks | 1 million |
| Monthly Audit Logs | 1 million |

### 3.3 Reliability
- Uptime: 99.5%
- Daily backups
- Recovery time: < 5 minutes
- Zero data loss for committed transactions

### 3.4 Security
- All endpoints require authentication
- Passwords hashed with bcrypt
- HTTPS/TLS enforced
- Rate limiting: 100 requests/minute

---

## 4. Integration Requirements

### 4.1 External APIs
- Gemini 2.5 Flash (invoice processing)
- Gemini 3 Flash (negotiation)
- OpenRouter (fallback)
- WhatsApp Business API
- AWS S3

### 4.2 ERP Systems
- Tally ERP 9 / Prime (XML/CSV)
- Zoho Books (JSON)
- Generic CSV/JSON export

---

## 5. Acceptance Criteria

### 5.1 Agent A - Visual Auditor
- [x] Process invoice in < 30 seconds
- [x] >90% field extraction accuracy
- [x] >85% tampering detection accuracy
- [x] Auto-trigger Agents B/C based on content

### 5.2 Agent B - Legal Sentinel
- [x] Query response < 5 seconds
- [x] Correct turnover filtering
- [x] Daily government website monitoring
- [x] Alerts within 1 hour of new notifications

### 5.3 Agent C - Subsidy Hunter
- [x] >90% scheme matching accuracy
- [x] Correct benefit calculations
- [x] Application guidance provided

### 5.4 Agent D - Negotiator
- [x] Correct strategy determination
- [x] Contextual content generation
- [x] A/B options provided
- [x] **CRITICAL**: Never auto-send

### 5.5 Security
- [x] All sensitive data encrypted
- [x] All user actions logged
- [x] Disclaimers prominently displayed
- [x] Guardrails enforced

---

## 6. Industry Support

| # | Industry | Status |
|---|----------|--------|
| 1 | Textile & Apparel | ✅ |
| 2 | Manufacturing | ✅ |
| 3 | Technology & IT | ✅ |
| 4 | Trading & Distribution | ✅ |
| 5 | Professional Services | ✅ |
| 6 | Retail | ✅ |
| 7 | Construction & Real Estate | ✅ |
| 8 | Healthcare & Pharma | ✅ |
| 9 | Education & Training | ✅ |
| 10 | Hospitality & Tourism | ✅ |
| 11 | Agriculture & Agri-business | ✅ |
| 12 | Other | ✅ |

---

## 7. Turnover Tiers

| Tier | Range | Features |
|------|-------|----------|
| Micro | < ₹5 Crore | Basic compliance, simplified schemes |
| Small | ₹5-20 Crore | Full compliance, MSME schemes |
| Medium | ₹20-50 Crore | Advanced compliance, industry schemes |
| Large | > ₹50 Crore | Enterprise features, audit requirements |

---

## 8. Success Metrics

### 8.1 Usage (6-month targets)
- 1,000 active users
- 10,000 invoices/month
- 5,000 legal queries/month
- 1,000 subsidy applications/month

### 8.2 Performance
- 95% invoice processing accuracy
- 99.5% uptime
- < 2 second API response

### 8.3 Business Impact
- 70% reduction in manual data entry
- 50% increase in subsidy applications
- 30% improvement in cash flow management
- 90% user satisfaction

---

## 9. Constraints & Assumptions

### Constraints
- Python 3.7+ required
- PostgreSQL database
- Gemini API key required
- Indian legal framework only

### Assumptions
- Users have basic computer literacy
- Internet connectivity available
- AI outputs verified with professionals

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Gemini API downtime | OpenRouter fallback |
| OCR accuracy issues | Confidence scores + manual review |
| Legal liability | Prominent disclaimers + guardrails |
| Data breach | AES-256 encryption + audit trails |

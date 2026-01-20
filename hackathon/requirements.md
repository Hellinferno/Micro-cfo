# MicroCFO - Requirements Document

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

#### 2.1.1 Invoice Processing
**FR-A1**: System shall process invoice images (PDF, PNG, JPG, JPEG) using Gemini 2.5 Flash
- **Input**: Invoice image (local file, URL, or base64)
- **Output**: Structured invoice data with confidence scores
- **Max File Size**: 50 MB
- **Processing Time**: < 30 seconds per invoice

**FR-A2**: System shall extract structured data from invoices
- Vendor name and GSTIN
- Invoice number and date
- Total amount, tax amount, taxable amount
- Line items with descriptions, amounts, and categories
- Payment terms and due date

**FR-A3**: System shall categorize line items into 4 categories
- Capital Goods (machinery, equipment, vehicles)
- Raw Material (production inputs)
- Personal/Entertainment (food, alcohol, personal expenses)
- Service (consulting, software, maintenance)

#### 2.1.2 Fraud Detection
**FR-A4**: System shall detect invoice tampering
- Mismatched fonts
- Blurred or altered numbers
- Digital manipulation indicators
- Confidence score < 0.7 triggers manual review

**FR-A5**: System shall identify handwritten invoices
- Flag handwritten bills for reliability assessment
- Provide confidence score for handwritten content

**FR-A6**: System shall validate GSTIN presence
- Flag invoices with tax charged but no GSTIN
- Warn about ITC eligibility issues

**FR-A7**: System shall check invoice staleness
- Flag invoices > 30 days old
- Warn about ITC time limits

#### 2.1.3 Orchestrator Integration
**FR-A8**: System shall auto-trigger Agent C for capital goods > ₹1 Lakh
- Automatic subsidy discovery
- Proactive benefit calculation

**FR-A9**: System shall auto-trigger Agent B for personal/entertainment items
- ITC compliance checking
- Section 17(5) validation

**FR-A10**: System shall provide conservative CA-style recommendations
- When in doubt, flag for manual review
- Err on the side of caution for compliance

### 2.2 Agent B - Legislative Sentinel

#### 2.2.1 Legal Document Processing
**FR-B1**: System shall ingest legal documents with structure awareness
- Recognize Section, Rule, Notification patterns
- Preserve provisos and sub-clauses
- Maintain parent-child relationships

**FR-B2**: System shall extract metadata from legal text
- Turnover thresholds (₹5 Cr, ₹50 Cr)
- Sector tags (Textile, Manufacturing, etc.)
- Effective dates
- Law types (GST, Income Tax, Companies Act)

**FR-B3**: System shall chunk legal text using CA-logic
- Preserve legal context
- Maintain section integrity
- Keep provisos with parent sections

#### 2.2.2 Legal Query Processing
**FR-B4**: System shall answer legal compliance queries
- Semantic search using vector database
- Keyword search for section numbers
- Hybrid search combining both approaches

**FR-B5**: System shall filter results by user context
- Turnover tier-based filtering
- Sector-specific relevance
- Conservative interpretations

**FR-B6**: System shall provide risk assessment
- Risk levels: LOW, MEDIUM, HIGH
- Relevant sections and citations
- Professional consultation recommendations

#### 2.2.3 Real-time Monitoring
**FR-B7**: System shall monitor government websites
- CBIC (GST notifications)
- MCA (Companies Act updates)
- Income Tax Department notifications

**FR-B8**: System shall check notification relevance
- User profile matching
- Turnover tier filtering
- Sector-specific filtering

**FR-B9**: System shall send alerts for relevant updates
- WhatsApp Business API integration
- Email notifications
- In-app alerts

### 2.3 Agent C - Subsidy Hunter

#### 2.3.1 Subsidy Discovery
**FR-C1**: System shall maintain subsidy scheme database
- Government schemes (PLI, TUFS, MSME, etc.)
- Eligibility criteria
- Application deadlines
- Benefit amounts

**FR-C2**: System shall match schemes to user profile
- Industry-based filtering
- Turnover tier-based filtering
- Sector-specific schemes

**FR-C3**: System shall calculate estimated benefits
- Percentage-based subsidies
- Fixed amount subsidies
- Conditional benefits

**FR-C4**: System shall provide application guidance
- Required documents
- Application process
- Deadlines and timelines

### 2.4 Agent D - Negotiator

#### 2.4.1 Strategy Determination
**FR-D1**: System shall determine negotiation strategy using router logic
- Credit Extension: When cash flow is tight
- Payment Chase: When invoices are overdue
- Early Payment Offer: When cash surplus exists

**FR-D2**: System shall analyze financial context
- Current cash position
- Upcoming outflows
- Due dates and aging
- Transaction type (payable/receivable)

#### 2.4.2 Content Generation
**FR-D3**: System shall generate negotiation content using Gemini 3 Flash
- WhatsApp messages (< 160 characters)
- Formal email content
- Indian business communication style
- Invoice-specific references

**FR-D4**: System shall provide A/B testing options
- Option A: Relationship-focused approach
- Option B: Transactional approach
- Strategy explanation for each

**FR-D5**: System shall enforce draft-only mode
- NEVER auto-send emails
- Always require user approval
- Display prominent disclaimer

### 2.5 Phase 4: Business Logic & Integration

#### 2.5.1 ERP Adapters
**FR-E1**: System shall export invoices to Tally ERP 9 / Tally Prime
- XML format for single voucher
- CSV format for batch import
- Automatic ledger entry creation (Dr/Cr)
- Purchase voucher generation

**FR-E2**: System shall export invoices to Zoho Books
- JSON API payload format
- Bill creation structure
- GST treatment handling
- Batch export support

**FR-E3**: System shall export to standard formats
- CSV for Excel and generic accounting
- JSON for custom integrations
- Line item detail support
- Configurable formatting

**FR-E4**: System shall validate export formats
- Format compatibility checking
- Batch support verification
- File size limits
- Data completeness validation

#### 2.5.2 User Onboarding
**FR-O1**: System shall capture company information
- Company name, email, phone
- GST registration type and GSTIN
- PAN number
- Registered address

**FR-O2**: System shall support 12 industry types
- Textile & Apparel
- Manufacturing
- Technology & IT
- Trading & Distribution
- Professional Services
- Retail
- Construction & Real Estate
- Healthcare & Pharma
- Education & Training
- Hospitality & Tourism
- Agriculture & Agri-business
- Other

**FR-O3**: System shall support 4 turnover tiers
- Micro: < ₹5 Crore
- Small: ₹5-20 Crore
- Medium: ₹20-50 Crore
- Large: > ₹50 Crore

**FR-O4**: System shall implement 9-step onboarding flow
1. Welcome
2. Company Basic Info
3. Industry Selection
4. Turnover Tier Selection
5. GST Details
6. Contact Information
7. Preferences
8. Review & Confirm
9. Complete

**FR-O5**: System shall validate user input
- GSTIN format validation (15 characters)
- PAN format validation (10 characters)
- Email format validation
- Phone number validation
- Pincode validation (6 digits)

**FR-O6**: System shall use context for filtering
- Agent B filters by turnover tier
- Agent C filters by industry
- Personalized recommendations

### 2.6 Security & Compliance

#### 2.6.1 Data Encryption
**FR-S1**: System shall encrypt sensitive data at rest
- AES-256 (Fernet) encryption
- Custom SQLAlchemy types
- Encrypted columns: GST, PAN, amounts, vendor names, addresses

**FR-S2**: System shall encrypt files in S3
- Server-side encryption (SSE-S3 or SSE-KMS)
- Automatic encryption on upload
- Secure key management

**FR-S3**: System shall support local storage fallback
- Automatic fallback when S3 unavailable
- Unified storage interface
- Transparent switching

#### 2.6.2 Audit Trails
**FR-S4**: System shall log all user actions
- Who: User ID
- What: Action type (30+ types)
- When: Timestamp
- Where: IP address
- How: User agent and request details

**FR-S5**: System shall support audit log queries
- Filter by user, action, date range
- Export to CSV/JSON
- Pagination support
- Search functionality

**FR-S6**: System shall implement 4 severity levels
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Failed operations
- CRITICAL: Security incidents

#### 2.6.3 Legal Disclaimers
**FR-S7**: System shall display main disclaimer
- Prominent on first visit
- Cannot be dismissed without acceptance
- Session-based tracking

**FR-S8**: System shall provide 7 disclaimer types
- General AI assistant
- Legal advice
- Financial advice
- Tax advice
- Negotiation
- Invoice processing
- Subsidy application

**FR-S9**: System shall show persistent disclaimer banner
- Always visible after acceptance
- "View Full Disclaimer" button
- Short disclaimer text

#### 2.6.4 Guardrails
**FR-S10**: System shall enforce draft-only mode for Negotiator
- NEVER auto-send emails
- Always require user approval
- Log all draft generations

**FR-S11**: System shall require verification for invoices
- No auto-approval
- Manual verification required
- Flag high amounts (> ₹50,000)

**FR-S12**: System shall recommend professional consultation
- For legal queries
- For financial decisions
- For tax planning
- For compliance matters

---

## 3. Non-Functional Requirements

### 3.1 Performance
**NFR-P1**: Invoice processing shall complete within 30 seconds
**NFR-P2**: Legal queries shall return results within 5 seconds
**NFR-P3**: API endpoints shall respond within 2 seconds (95th percentile)
**NFR-P4**: System shall support 100 concurrent users
**NFR-P5**: Database queries shall complete within 1 second

### 3.2 Scalability
**NFR-SC1**: System shall handle 10,000 invoices per day
**NFR-SC2**: Vector database shall support 1 million legal chunks
**NFR-SC3**: Audit logs shall support 1 million entries per month
**NFR-SC4**: System shall scale horizontally

### 3.3 Reliability
**NFR-R1**: System uptime shall be 99.5%
**NFR-R2**: Data backup shall occur daily
**NFR-R3**: System shall recover from failures within 5 minutes
**NFR-R4**: Zero data loss for committed transactions

### 3.4 Security
**NFR-SE1**: All API endpoints shall require authentication
**NFR-SE2**: Passwords shall be hashed using bcrypt
**NFR-SE3**: API keys shall never be logged
**NFR-SE4**: HTTPS/TLS shall be enforced for all connections
**NFR-SE5**: Rate limiting shall prevent abuse (100 requests/minute)

### 3.5 Usability
**NFR-U1**: Onboarding shall complete within 5 minutes
**NFR-U2**: UI shall be responsive (mobile, tablet, desktop)
**NFR-U3**: Error messages shall be user-friendly
**NFR-U4**: System shall support English and Hindi

### 3.6 Maintainability
**NFR-M1**: Code coverage shall be > 80%
**NFR-M2**: API documentation shall be auto-generated
**NFR-M3**: Logging shall be comprehensive
**NFR-M4**: Configuration shall be externalized

### 3.7 Compliance
**NFR-C1**: System shall comply with Indian data protection laws
**NFR-C2**: Audit trails shall be tamper-proof
**NFR-C3**: Data retention shall follow legal requirements
**NFR-C4**: System shall support GDPR-style data deletion

---

## 4. Integration Requirements

### 4.1 External APIs
**INT-1**: Gemini 2.5 Flash API for invoice processing
**INT-2**: Gemini 3 Flash API for negotiation content
**INT-3**: OpenRouter API (fallback for Gemini)
**INT-4**: WhatsApp Business API for alerts
**INT-5**: AWS S3 API for file storage

### 4.2 ERP Systems
**INT-6**: Tally ERP 9 / Tally Prime (XML/CSV export)
**INT-7**: Zoho Books (JSON API)
**INT-8**: Generic CSV export for other systems

### 4.3 Government Websites
**INT-9**: CBIC website scraping for GST notifications
**INT-10**: MCA website scraping for Companies Act updates
**INT-11**: Income Tax Department website scraping

---

## 5. Data Requirements

### 5.1 Database Schema
**Data-1**: Users table with encrypted PII
**Data-2**: Invoices table with encrypted amounts
**Data-3**: Legal queries table with history
**Data-4**: Subsidy applications table
**Data-5**: Negotiations table with drafts
**Data-6**: Audit logs table (append-only)
**Data-7**: Company profiles table with context

### 5.2 Vector Database
**Data-8**: Legal chunks with embeddings
**Data-9**: Metadata for filtering
**Data-10**: Seen notifications tracking

### 5.3 File Storage
**Data-11**: Invoice images in S3 or local
**Data-12**: Export files (temporary)
**Data-13**: Backup files

---

## 6. User Stories

### 6.1 Invoice Processing
**US-1**: As a business owner, I want to upload an invoice image and get structured data extracted automatically, so I can save time on manual data entry.

**US-2**: As a CA, I want the system to flag suspicious invoices, so I can review them before approving.

**US-3**: As a business owner, I want to export invoices to Tally with one click, so I don't have to manually enter data in my accounting system.

### 6.2 Legal Compliance
**US-4**: As a business owner, I want to ask legal compliance questions and get answers filtered by my turnover tier, so I only see relevant information.

**US-5**: As a CA, I want to receive alerts about new GST notifications relevant to my clients, so I can advise them proactively.

### 6.3 Subsidy Discovery
**US-6**: As a textile manufacturer, I want to see subsidies applicable to my industry, so I can apply for government benefits.

**US-7**: As a business owner, I want to know the estimated benefit amount, so I can decide if it's worth applying.

### 6.4 Negotiation
**US-8**: As a business owner with cash flow issues, I want to generate a professional email requesting payment extension, so I can maintain good vendor relationships.

**US-9**: As a business owner, I want to see two versions of the negotiation email (relationship vs transactional), so I can choose the best approach.

### 6.5 Onboarding
**US-10**: As a new user, I want to complete onboarding in 5 minutes, so I can start using the system quickly.

**US-11**: As a business owner, I want to select my industry and turnover tier, so the system shows me relevant information.

---

## 7. Acceptance Criteria

### 7.1 Agent A
- [ ] Process invoice image in < 30 seconds
- [ ] Extract all required fields with > 90% accuracy
- [ ] Detect tampering with > 85% accuracy
- [ ] Categorize line items with > 90% accuracy
- [ ] Auto-trigger Agent C for capital goods > ₹1L
- [ ] Auto-trigger Agent B for personal items

### 7.2 Agent B
- [ ] Answer legal queries in < 5 seconds
- [ ] Filter by turnover tier correctly
- [ ] Provide relevant sections and citations
- [ ] Monitor government websites daily
- [ ] Send alerts within 1 hour of new notification

### 7.3 Agent C
- [ ] Match schemes to user profile with > 90% accuracy
- [ ] Calculate benefits correctly
- [ ] Provide application guidance

### 7.4 Agent D
- [ ] Determine strategy correctly based on cash flow
- [ ] Generate contextual content
- [ ] Provide A/B options
- [ ] Enforce draft-only mode (never auto-send)

### 7.5 Phase 4
- [ ] Export to Tally XML/CSV successfully
- [ ] Export to Zoho Books JSON successfully
- [ ] Complete onboarding in < 5 minutes
- [ ] Validate all user inputs
- [ ] Filter by industry and turnover correctly

### 7.6 Security
- [ ] Encrypt all sensitive data
- [ ] Log all user actions
- [ ] Display disclaimers prominently
- [ ] Enforce guardrails (draft-only, verification)
- [ ] Prevent unauthorized access

---

## 8. Constraints

### 8.1 Technical Constraints
- Python 3.7+ required
- PostgreSQL database required
- Gemini API key required
- AWS S3 optional (local fallback available)

### 8.2 Business Constraints
- Focus on Indian legal framework only
- Support 12 industries initially
- 4 turnover tiers only
- English and Hindi languages only

### 8.3 Regulatory Constraints
- Must comply with Indian data protection laws
- Must not provide legal/financial advice
- Must recommend professional consultation
- Must maintain audit trails

---

## 9. Assumptions

1. Users have basic computer literacy
2. Users have internet connectivity
3. Users have valid GST registration (if applicable)
4. Users understand AI limitations
5. Users will verify AI outputs with professionals

---

## 10. Dependencies

1. Gemini API availability
2. Government website accessibility
3. AWS S3 availability (optional)
4. WhatsApp Business API (optional)
5. PostgreSQL database

---

## 11. Risks

### 11.1 Technical Risks
- **Risk**: Gemini API downtime
- **Mitigation**: Implement fallback to OpenRouter

- **Risk**: OCR accuracy issues
- **Mitigation**: Confidence scores and manual review

- **Risk**: Vector database performance
- **Mitigation**: Optimize queries and indexing

### 11.2 Business Risks
- **Risk**: Legal liability for incorrect advice
- **Mitigation**: Prominent disclaimers and guardrails

- **Risk**: User misuse of AI outputs
- **Mitigation**: Require professional verification

### 11.3 Compliance Risks
- **Risk**: Data breach
- **Mitigation**: Encryption and audit trails

- **Risk**: Regulatory changes
- **Mitigation**: Real-time monitoring and alerts

---

## 12. Success Metrics

### 12.1 Usage Metrics
- 1,000 active users within 6 months
- 10,000 invoices processed per month
- 5,000 legal queries per month
- 1,000 subsidy applications per month

### 12.2 Performance Metrics
- 95% invoice processing accuracy
- < 30 second processing time
- 99.5% uptime
- < 2 second API response time

### 12.3 Business Metrics
- 70% reduction in manual data entry time
- 50% increase in subsidy applications
- 30% improvement in cash flow management
- 90% user satisfaction score

---

**Document Version**: 2.0.0  
**Last Updated**: January 18, 2026  
**Status**: Approved ✅

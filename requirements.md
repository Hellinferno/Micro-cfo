# MicroCFO - Requirements Document

## 1. Executive Summary

MicroCFO is an AI-powered financial compliance platform designed specifically for Indian Micro, Small, and Medium Enterprises (MSMEs). The system provides automated invoice analysis, legal compliance monitoring, government subsidy discovery, and intelligent vendor negotiation capabilities.

### 1.1 Project Vision
To democratize access to professional financial and compliance services for Indian MSMEs through AI-powered automation, reducing costs and improving accuracy.

### 1.2 Target Users
- Indian MSMEs (Micro, Small, and Medium Enterprises)
- Business owners and financial managers
- Chartered Accountants and tax professionals
- Compliance officers

## 2. Business Requirements

### 2.1 Core Business Objectives
- **BR-001**: Reduce invoice processing time by 80% through automated analysis
- **BR-002**: Improve compliance accuracy by providing real-time legal guidance
- **BR-003**: Increase subsidy discovery rate by 60% through intelligent matching
- **BR-004**: Streamline vendor negotiations with AI-generated communication drafts
- **BR-005**: Ensure data security and privacy compliance for sensitive financial information

### 2.2 Success Metrics
- Invoice processing time < 30 seconds per document
- Compliance query response time < 5 seconds
- Subsidy match accuracy > 85%
- User satisfaction score > 4.0/5.0
- System uptime > 99.5%

## 3. Functional Requirements

### 3.1 Agent A: Visual Auditor (Invoice Analysis)

#### 3.1.1 Invoice Scanning and Data Extraction
- **FR-001**: System shall accept invoice uploads in PNG, JPG, and PDF formats
- **FR-002**: System shall extract structured data including vendor name, invoice date, amounts, GSTIN, and line items
- **FR-003**: System shall categorize line items into: Capital Goods, Raw Material, Personal/Entertainment, Service
- **FR-004**: System shall support both file upload and URL-based invoice analysis
- **FR-005**: System shall process base64-encoded image data

#### 3.1.2 Fraud Detection
- **FR-006**: System shall detect tampering indicators (mismatched fonts, blurred numbers, digital manipulation)
- **FR-007**: System shall identify handwritten invoices and flag them for manual review
- **FR-008**: System shall validate GSTIN presence when tax is charged
- **FR-009**: System shall flag invoices older than 30 days for ITC eligibility concerns
- **FR-010**: System shall provide confidence scores for all extracted data

#### 3.1.3 Compliance Checking
- **FR-011**: System shall flag items not eligible for Input Tax Credit (ITC)
- **FR-012**: System shall identify personal/entertainment expenses
- **FR-013**: System shall validate business expense eligibility
- **FR-014**: System shall generate compliance warnings with specific section references

#### 3.1.4 Orchestrator Integration
- **FR-015**: System shall auto-trigger Subsidy Hunter for capital goods purchases > ₹1 lakh
- **FR-016**: System shall auto-trigger Legal Sentinel for personal/entertainment items
- **FR-017**: System shall provide proactive alerts for compliance and subsidy opportunities

### 3.2 Agent B: Legal Sentinel (Compliance Monitoring)

#### 3.2.1 Compliance Query Processing
- **FR-018**: System shall accept natural language compliance questions
- **FR-019**: System shall provide risk-level assessment (LOW, MEDIUM, HIGH)
- **FR-020**: System shall identify relevant legal sections (GST Act, Income Tax Act, Companies Act)
- **FR-021**: System shall provide clear explanations in 2-3 sentences
- **FR-022**: System shall recommend specific compliant actions

#### 3.2.2 Structure-Aware RAG (Retrieval-Augmented Generation)
- **FR-023**: System shall implement CA-logic based legal text chunking
- **FR-024**: System shall preserve legal structure (sections, provisos, sub-clauses)
- **FR-025**: System shall extract metadata (turnover thresholds, sectors, effective dates)
- **FR-026**: System shall support semantic search using vector embeddings
- **FR-027**: System shall filter results based on user context (turnover, sector)

#### 3.2.3 Real-time Monitoring
- **FR-028**: System shall monitor government websites for new notifications
- **FR-029**: System shall check relevance against user profiles
- **FR-030**: System shall send alerts for applicable legal changes
- **FR-031**: System shall support Telegram Bot API integration for notifications

#### 3.2.4 Legal Database Management
- **FR-032**: System shall support automated legal document ingestion
- **FR-033**: System shall detect and prevent duplicate document processing
- **FR-034**: System shall maintain document processing history with file hashes
- **FR-035**: System shall support batch processing of multiple legal documents

### 3.3 Agent C: Subsidy Hunter (Government Scheme Discovery)

#### 3.3.1 Subsidy Search and Matching
- **FR-036**: System shall search subsidies by sector, CAPEX amount, and state
- **FR-037**: System shall support natural language query processing
- **FR-038**: System shall calculate match scores based on eligibility criteria
- **FR-039**: System shall provide top 5 most relevant schemes
- **FR-040**: System shall extract scheme details (name, benefit, eligibility, ministry, link)

#### 3.3.2 Scheme Database Management
- **FR-041**: System shall scrape government websites for scheme information
- **FR-042**: System shall support caching for performance optimization
- **FR-043**: System shall allow manual refresh of scheme database
- **FR-044**: System shall track scheme application status

#### 3.3.3 Eligibility Assessment
- **FR-045**: System shall filter schemes by sector keywords
- **FR-046**: System shall filter schemes by CAPEX thresholds
- **FR-047**: System shall provide estimated subsidy amounts
- **FR-048**: System shall list required documents for application

### 3.4 Agent D: Negotiator (Vendor Communication)

#### 3.4.1 Email Draft Generation
- **FR-049**: System shall generate negotiation emails based on invoice context
- **FR-050**: System shall support multiple tones (professional, firm, polite)
- **FR-051**: System shall consider vendor relationship status (neutral, good, strained)
- **FR-052**: System shall provide strategy explanations for generated content
- **FR-053**: System shall generate both subject lines and email bodies

#### 3.4.2 Negotiation Strategy
- **FR-054**: System shall determine negotiation intent (credit extension, payment chase, early payment offer)
- **FR-055**: System shall analyze cash flow position for strategy selection
- **FR-056**: System shall generate A/B variations (relationship-focused vs transactional)
- **FR-057**: System shall support multi-format output (Telegram messages + formal emails)

#### 3.4.3 Negotiation Tracking
- **FR-058**: System shall store negotiation drafts with status tracking
- **FR-059**: System shall track sent date and response status
- **FR-060**: System shall maintain vendor negotiation history

### 3.5 Orchestrator (Message Routing)

#### 3.5.1 Intelligent Agent Selection
- **FR-061**: System shall automatically route messages to appropriate agents
- **FR-062**: System shall support manual agent selection override
- **FR-063**: System shall score messages against agent keywords
- **FR-064**: System shall handle general queries with fallback responses

#### 3.5.2 Context Management
- **FR-065**: System shall maintain conversation context across messages
- **FR-066**: System shall support multi-turn conversations
- **FR-067**: System shall provide suggested follow-up actions
- **FR-068**: System shall track agent usage statistics

### 3.6 User Management

#### 3.6.1 Authentication and Authorization
- **FR-069**: System shall support email/password authentication
- **FR-070**: System shall implement JWT-based session management
- **FR-071**: System shall support email verification
- **FR-072**: System shall enforce role-based access control

#### 3.6.2 User Profiles
- **FR-073**: System shall collect business sector information
- **FR-074**: System shall collect turnover tier information
- **FR-075**: System shall store company details (name, GST number, PAN)
- **FR-076**: System shall support user preferences (JSONB format)

### 3.7 Data Management

#### 3.7.1 Invoice Storage
- **FR-077**: System shall store invoice metadata in database
- **FR-078**: System shall store extracted data in JSONB format
- **FR-079**: System shall track invoice status (pending, processed, flagged)
- **FR-080**: System shall support invoice file storage

#### 3.7.2 Query History
- **FR-081**: System shall maintain legal query history per user
- **FR-082**: System shall store compliance responses with risk levels
- **FR-083**: System shall support query history retrieval
- **FR-084**: System shall index queries by user and creation date

#### 3.7.3 Audit Logging
- **FR-085**: System shall log all user actions with timestamps
- **FR-086**: System shall capture IP address and user agent
- **FR-087**: System shall store action details in JSONB format
- **FR-088**: System shall support audit log querying and filtering

## 4. Non-Functional Requirements

### 4.1 Performance Requirements
- **NFR-001**: Invoice analysis shall complete within 30 seconds
- **NFR-002**: Compliance queries shall respond within 5 seconds
- **NFR-003**: Subsidy search shall return results within 10 seconds
- **NFR-004**: System shall support 100 concurrent users
- **NFR-005**: Database queries shall execute within 500ms (95th percentile)

### 4.2 Security Requirements
- **NFR-006**: System shall encrypt sensitive data at rest using AES-256
- **NFR-007**: System shall encrypt data in transit using TLS 1.3
- **NFR-008**: System shall implement rate limiting (100 requests/minute per user)
- **NFR-009**: System shall sanitize all user inputs to prevent injection attacks
- **NFR-010**: System shall implement CORS with whitelist-only origins
- **NFR-011**: System shall hash passwords using bcrypt with salt rounds ≥ 12
- **NFR-012**: System shall rotate encryption keys every 90 days

### 4.3 Reliability Requirements
- **NFR-013**: System shall maintain 99.5% uptime
- **NFR-014**: System shall implement automatic failover for critical services
- **NFR-015**: System shall perform daily automated backups
- **NFR-016**: System shall support point-in-time recovery within 24 hours
- **NFR-017**: System shall implement graceful degradation when AI services are unavailable

### 4.4 Scalability Requirements
- **NFR-018**: System shall scale horizontally to support 10,000+ users
- **NFR-019**: System shall support database read replicas for query distribution
- **NFR-020**: System shall implement caching for frequently accessed data
- **NFR-021**: System shall support CDN integration for static assets

### 4.5 Usability Requirements
- **NFR-022**: System shall provide mobile-responsive UI
- **NFR-023**: System shall support English and Hindi languages
- **NFR-024**: System shall provide contextual help and tooltips
- **NFR-025**: System shall display loading indicators for long operations
- **NFR-026**: System shall provide clear error messages with recovery suggestions

### 4.6 Compliance Requirements
- **NFR-027**: System shall comply with Indian IT Act 2000
- **NFR-028**: System shall comply with GDPR for data protection
- **NFR-029**: System shall display legal disclaimers for AI-generated advice
- **NFR-030**: System shall maintain audit trails for 7 years
- **NFR-031**: System shall support data export in standard formats (CSV, JSON)

### 4.7 Maintainability Requirements
- **NFR-032**: System shall use modular architecture with clear separation of concerns
- **NFR-033**: System shall maintain code coverage ≥ 80%
- **NFR-034**: System shall document all APIs using OpenAPI/Swagger
- **NFR-035**: System shall implement structured logging with log levels
- **NFR-036**: System shall support feature flags for gradual rollouts

## 5. Integration Requirements

### 5.1 AI/LLM Integration
- **IR-001**: System shall integrate with Google Gemini 1.5 Flash for general queries
- **IR-002**: System shall integrate with Google Gemini 2.5 Flash for vision tasks
- **IR-003**: System shall support fallback to mock data when API keys are unavailable
- **IR-004**: System shall implement retry logic with exponential backoff for API failures

### 5.2 External Services
- **IR-005**: System shall integrate with ChromaDB for vector storage
- **IR-006**: System shall integrate with sentence-transformers for embeddings
- **IR-007**: System shall support optional Redis integration for caching
- **IR-008**: System shall support optional S3 integration for file storage
- **IR-009**: System shall integrate with Telegram Bot API for notifications

### 5.3 ERP Integration
- **IR-010**: System shall support export to Tally format
- **IR-011**: System shall support export to Zoho Books format
- **IR-012**: System shall support export to CSV format
- **IR-013**: System shall support export to JSON format

## 6. Data Requirements

### 6.1 Data Models
- **DR-001**: System shall use PostgreSQL as primary database
- **DR-002**: System shall support SQLite for development environments
- **DR-003**: System shall use UUID for all primary keys
- **DR-004**: System shall use JSONB for flexible schema fields
- **DR-005**: System shall implement soft deletes for critical data

### 6.2 Data Retention
- **DR-006**: System shall retain invoice data for 7 years
- **DR-007**: System shall retain audit logs for 7 years
- **DR-008**: System shall retain user data until account deletion
- **DR-009**: System shall anonymize deleted user data

### 6.3 Data Migration
- **DR-010**: System shall support Alembic for database migrations
- **DR-011**: System shall implement rollback capability for all migrations
- **DR-012**: System shall validate data integrity after migrations
- **DR-013**: System shall support zero-downtime migrations

## 7. Deployment Requirements

### 7.1 Environment Configuration
- **DEP-001**: System shall support environment-based configuration (.env files)
- **DEP-002**: System shall support Docker containerization
- **DEP-003**: System shall support Docker Compose for local development
- **DEP-004**: System shall provide health check endpoints

### 7.2 Monitoring and Observability
- **DEP-005**: System shall expose Prometheus-compatible metrics
- **DEP-006**: System shall implement structured logging (JSON format)
- **DEP-007**: System shall support distributed tracing
- **DEP-008**: System shall provide performance monitoring dashboards

## 8. Constraints and Assumptions

### 8.1 Technical Constraints
- Python 3.11+ required for backend
- Node.js 18+ required for frontend
- Minimum 4GB RAM for production deployment
- Requires internet connectivity for AI services

### 8.2 Business Constraints
- Initial launch focused on Indian market only
- English and Hindi language support only
- Requires valid API keys for full functionality

### 8.3 Assumptions
- Users have basic understanding of GST and tax compliance
- Users have access to digital invoice documents
- Government websites remain accessible for scraping
- AI service providers maintain API compatibility

## 9. Future Enhancements

### 9.1 Planned Features
- Multi-language support (Tamil, Telugu, Marathi)
- Mobile native applications (iOS, Android)
- WhatsApp integration for notifications
- Advanced analytics and reporting dashboards
- Automated GST return filing
- Integration with banking APIs for cash flow analysis

### 9.2 Research Areas
- Blockchain integration for invoice verification
- Machine learning for fraud pattern detection
- Natural language processing for contract analysis
- Predictive analytics for cash flow forecasting

## 10. Acceptance Criteria

### 10.1 System Acceptance
- All functional requirements implemented and tested
- Non-functional requirements meet specified thresholds
- Security audit completed with no critical vulnerabilities
- Performance benchmarks achieved under load testing
- User acceptance testing completed with ≥ 90% satisfaction

### 10.2 Documentation Acceptance
- API documentation complete and accurate
- User manual available in English and Hindi
- Deployment guide tested on clean environment
- Troubleshooting guide covers common issues
- Code documentation meets coverage standards

---

**Document Version**: 1.0  
**Last Updated**: February 10, 2026  
**Status**: Approved  
**Owner**: MicroCFO Development Team

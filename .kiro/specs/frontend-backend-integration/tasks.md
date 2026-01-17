# Implementation Plan: Frontend-Backend Integration

## Overview

This implementation plan creates a FastAPI-based integration layer that bridges the React frontend with the existing MCP server. The approach builds incrementally, starting with core API endpoints, adding authentication, then real-time features, and finally optimization and testing.

## Tasks

- [x] 1. Set up FastAPI integration server foundation
  - Create new `integration_server.py` with FastAPI app initialization
  - Set up project structure with routers, middleware, and configuration
  - Configure CORS for frontend domain communication
  - Add basic health check endpoint
  - _Requirements: 7.3, 7.4_

- [x] 2. Implement MCP Bridge component
  - [x] 2.1 Create MCPBridge class for tool call translation
    - Write bridge class that imports and calls existing MCP server tools
    - Implement JSON serialization for Pydantic models
    - Add error handling for MCP tool failures
    - _Requirements: 1.1, 1.2, 1.5_

  - [x] 2.2 Write property test for MCP integration consistency
    - **Property 1: MCP Integration Consistency**
    - **Validates: Requirements 1.1, 1.2, 1.5**

- [x] 3. Create Agent A (Visual Auditor) REST endpoints
  - [x] 3.1 Implement POST /api/v1/agents/visual-auditor/scan-invoice
    - Create router with endpoint for invoice scanning
    - Handle both image_url and file upload scenarios
    - Integrate with existing scan_invoice_document MCP tool
    - _Requirements: 1.3, 4.1_

  - [x] 3.2 Implement file upload handling for Agent A
    - Add multipart form data support for document uploads
    - Implement secure temporary file storage with UUID filenames
    - Add file type and size validation (PDF, PNG, JPG, JPEG)
    - _Requirements: 1.4, 4.1, 4.5_

  - [x] 3.3 Write property test for secure file processing
    - **Property 4: Secure File Processing**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [x] 4. Create Agent B (Legal Sentinel) REST endpoints
  - [x] 4.1 Implement POST /api/v1/agents/legal-sentinel/check-compliance
    - Create endpoint for legal compliance queries
    - Integrate with existing check_compliance_law MCP tool
    - Add user context passing for personalized responses
    - _Requirements: 1.3, 2.4_

  - [x] 4.2 Write unit tests for legal compliance endpoint
    - Test various compliance queries and user contexts
    - Test error handling for invalid queries
    - _Requirements: 1.3_

- [x] 5. Create Agent C (Subsidy Hunter) REST endpoints
  - [x] 5.1 Implement POST /api/v1/agents/subsidy-hunter/find-subsidies
    - Create endpoint for subsidy discovery
    - Integrate with existing find_applicable_subsidies MCP tool
    - Add sector and capex amount validation
    - _Requirements: 1.3_

  - [x] 5.2 Write unit tests for subsidy hunter endpoint
    - Test various sector and capex combinations
    - Test input validation and error cases
    - _Requirements: 1.3_

- [x] 6. Create Agent D (Negotiator) REST endpoints
  - [x] 6.1 Implement POST /api/v1/agents/negotiator/generate-draft
    - Create endpoint for negotiation email generation
    - Integrate with existing generate_negotiation_draft MCP tool
    - Add request validation for required fields
    - _Requirements: 1.3_

  - [x] 6.2 Write unit tests for negotiator endpoint
    - Test email generation with various contexts and tones
    - Test input validation and error handling
    - _Requirements: 1.3_

- [x] 7. Checkpoint - Ensure all basic endpoints work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement authentication system
  - [x] 8.1 Create JWT token handler and user context management
    - Implement JWT token generation and validation
    - Create UserContext model with business profile data
    - Add authentication middleware for protected endpoints
    - _Requirements: 2.1, 2.2_

  - [x] 8.2 Add role-based access control
    - Implement role checking (business owner, accountant, viewer)
    - Add permission validation for different endpoints
    - Create authorization middleware
    - _Requirements: 2.5_

  - [x] 8.3 Create authentication endpoints
    - Implement POST /api/v1/auth/login for user authentication
    - Implement GET /api/v1/auth/profile for user profile retrieval
    - Add session management and token refresh
    - _Requirements: 2.1, 2.3_

  - [x] 8.4 Write property test for authentication and authorization
    - **Property 2: Authentication and Authorization**
    - **Validates: Requirements 2.1, 2.3, 2.5**

- [x] 9. Implement WebSocket manager for real-time features
  - [x] 9.1 Create WebSocket connection manager
    - Implement WebSocket endpoint for client connections
    - Add connection lifecycle management (connect, disconnect, heartbeat)
    - Create room-based broadcasting for user-specific updates
    - _Requirements: 3.3, 3.5_

  - [x] 9.2 Integrate with Legal Sentinel monitoring
    - Connect WebSocket manager to existing sentinel_monitor.py
    - Push legal updates to relevant connected clients
    - Add user profile-based filtering for update relevance
    - _Requirements: 3.1, 3.4_

  - [x] 9.3 Add progress updates for long-running operations
    - Implement operation tracking with unique IDs
    - Send progress updates via WebSocket during document processing
    - Add completion notifications for async operations
    - _Requirements: 3.2_

  - [x] 9.4 Write property test for real-time update delivery
    - **Property 3: Real-time Update Delivery**
    - **Validates: Requirements 3.1, 3.2, 3.4**

  - [x] 9.5 Write property test for WebSocket connection resilience
    - **Property 9: WebSocket Connection Resilience**
    - **Validates: Requirements 3.3, 3.5**

- [x] 10. Implement error handling and logging system
  - [x] 10.1 Create centralized error handler
    - Implement FastAPI exception handlers for different error types
    - Add user-friendly error message translation
    - Ensure internal details are not exposed to clients
    - _Requirements: 5.1, 5.3_

  - [x] 10.2 Add comprehensive logging system
    - Implement request logging with user context and timestamps
    - Add audit logging for compliance operations
    - Configure log levels and output formats
    - _Requirements: 5.2, 5.5_

  - [x] 10.3 Implement rate limiting
    - Add rate limiting middleware to prevent abuse
    - Configure different limits for different endpoint types
    - Add rate limit headers in responses
    - _Requirements: 5.4_

  - [x] 10.4 Write property test for error handling and logging
    - **Property 5: Error Handling and Logging**
    - **Validates: Requirements 5.1, 5.3, 8.4**

- [x] 11. Add performance optimization features
  - [x] 11.1 Implement caching system for legal queries
    - Add Redis or in-memory caching for frequently accessed legal data
    - Implement cache key generation based on query parameters
    - Add cache invalidation for updated legal content
    - _Requirements: 6.1, 6.2_

  - [x] 11.2 Add concurrent request handling
    - Ensure FastAPI async capabilities are properly utilized
    - Add connection pooling for database operations
    - Implement request queuing for resource-intensive operations
    - _Requirements: 6.3_

  - [x] 11.3 Optimize file transfer for large uploads
    - Implement streaming file uploads for large documents
    - Add progress tracking for file upload operations
    - Configure appropriate timeout settings
    - _Requirements: 6.4, 6.5_

  - [x] 11.4 Write property test for performance and caching
    - **Property 6: Performance and Caching**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 12. Implement data serialization and validation
  - [x] 12.1 Create request/response models for all endpoints
    - Define Pydantic models for all API request and response schemas
    - Add comprehensive input validation with detailed error messages
    - Ensure all models serialize correctly to JSON
    - _Requirements: 8.1, 8.2, 8.4_

  - [x] 12.2 Add API versioning support
    - Implement versioned API endpoints (v1, v2, etc.)
    - Add backward compatibility handling
    - Create version-specific response models
    - _Requirements: 8.5_

  - [x] 12.3 Write property test for data serialization consistency
    - **Property 7: Data Serialization Consistency**
    - **Validates: Requirements 8.1, 8.3**

- [x] 13. Add session context preservation
  - [x] 13.1 Implement session context middleware
    - Create middleware to extract and maintain user context throughout requests
    - Ensure business profile data is consistently available to MCP tools
    - Add session persistence across requests
    - _Requirements: 2.2, 2.4_

  - [x] 13.2 Write property test for session context preservation
    - **Property 8: Session Context Preservation**
    - **Validates: Requirements 2.2, 2.4**

- [x] 14. Add multi-format file support validation
  - [x] 14.1 Implement comprehensive file format detection
    - Add file type detection based on content, not just extension
    - Implement format-specific validation (PDF structure, image headers)
    - Add file corruption detection
    - _Requirements: 4.5_

  - [x] 14.2 Write property test for multi-format file support
    - **Property 10: Multi-format File Support**
    - **Validates: Requirements 4.5**

- [x] 15. Environment configuration and deployment setup
  - [x] 15.1 Create environment-specific configuration
    - Add configuration files for development, staging, production
    - Implement environment variable handling for sensitive data
    - Add database connection configuration per environment
    - _Requirements: 7.1, 7.2_

  - [x] 15.2 Add graceful startup and shutdown procedures
    - Implement application lifecycle management
    - Add cleanup procedures for temporary files and connections
    - Configure proper signal handling for container deployments
    - _Requirements: 7.5_

- [x] 16. Final integration and testing
  - [x] 16.1 Write comprehensive integration tests for complete workflows
    - Test end-to-end scenarios: login → upload → process → receive updates
    - Test error scenarios and recovery procedures
    - Test concurrent user scenarios
    - Test authentication flow with multiple users
    - Test WebSocket real-time updates during long operations
    - _Requirements: All requirements_

  - [x] 16.2 Add performance benchmarking tests
    - Test response times under load
    - Test caching effectiveness
    - Test concurrent request handling
    - Test file upload performance with large files
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 17. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive testing and validation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- The implementation builds incrementally: basic endpoints → authentication → real-time → optimization
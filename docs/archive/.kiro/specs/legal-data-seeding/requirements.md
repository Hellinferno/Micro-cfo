# Requirements Document

## Introduction

The Legal Data Seeding System provides automated downloading and ingestion of foundational Indian legal documents from official government sources into the MicroCFO vector database. This system establishes the "Base Layer" that powers the Legal Sentinel (Agent B) capabilities, enabling AI-powered legal compliance queries with structure-aware retrieval.

The system addresses the challenge of manually collecting and processing legal documents by automating the entire pipeline from download to vector database population, while handling common issues with government websites such as SSL certificate problems and complex PDF layouts.

## Glossary

- **Seed_Downloader**: The component responsible for downloading legal documents from official government sources
- **Legal_Ingestion_Pipeline**: The existing system that processes legal text with structure-aware chunking
- **Vector_Database**: ChromaDB-based storage system for semantic search of legal content
- **Base_Layer**: The foundational set of legal documents that power Legal Sentinel queries
- **CA_Logic**: Chartered Accountant-style legal interpretation and chunking methodology
- **Legal_Chunk**: A structured piece of legal text with metadata (law_type, section_number, etc.)
- **Turnover_Threshold**: Business revenue thresholds (5 crore, 50 crore) used for compliance filtering
- **Sector_Tag**: Industry classification (Textile, Manufacturing, Technology, Trading)
- **Seed_Data_Processor**: The component that orchestrates PDF processing and database population

## Requirements

### Requirement 1: Document Download Automation

**User Story:** As a system administrator, I want to automatically download foundational legal documents from official government sources, so that I can populate the vector database without manual intervention.

#### Acceptance Criteria

1. WHEN the Seed_Downloader is executed, THE System SHALL download the CGST Act 2017 from the CBIC official website
2. WHEN the Seed_Downloader is executed, THE System SHALL download the IGST Act 2017 from the CBIC official website
3. WHEN the Seed_Downloader is executed, THE System SHALL download the Income Tax Act 1961 from the IncomeTaxIndia official website
4. WHEN the Seed_Downloader is executed, THE System SHALL download the Companies Act 2013 from the India Code official website
5. WHEN the Seed_Downloader is executed, THE System SHALL download the PLI Scheme Textiles Guidelines from the Texprocil official website
6. WHEN a download is initiated, THE System SHALL store the downloaded file in the `./data/initial_acts/` directory
7. WHEN a file already exists in the target directory, THE System SHALL skip the download and log a message
8. WHEN a download completes successfully, THE System SHALL log the filename and file size

### Requirement 2: Network Error Handling

**User Story:** As a system administrator, I want the download system to handle network errors gracefully, so that temporary failures do not require manual intervention.

#### Acceptance Criteria

1. WHEN an SSL certificate verification fails for a gov.in domain, THE System SHALL retry the request with SSL verification disabled
2. WHEN a network timeout occurs during download, THE System SHALL retry the download up to 3 times with exponential backoff
3. WHEN a download fails after all retries, THE System SHALL log a detailed error message and continue with remaining downloads
4. WHEN an HTTP error status code is received, THE System SHALL log the status code and error details
5. WHEN all downloads complete, THE System SHALL provide a summary of successful and failed downloads

### Requirement 3: Enhanced Law Type Detection

**User Story:** As a developer, I want the legal ingestion system to automatically detect document types from filenames, so that legal chunks are correctly classified in the vector database.

#### Acceptance Criteria

1. WHEN a filename contains "CGST" or "IGST", THE Legal_Ingestion_Pipeline SHALL classify the document as law_type "GST"
2. WHEN a filename contains "Income Tax" or "IT Act", THE Legal_Ingestion_Pipeline SHALL classify the document as law_type "Income Tax"
3. WHEN a filename contains "Companies Act" or "MCA", THE Legal_Ingestion_Pipeline SHALL classify the document as law_type "Corporate Law"
4. WHEN a filename contains "PLI" or "Scheme", THE Legal_Ingestion_Pipeline SHALL classify the document as law_type "Subsidy Scheme"
5. WHEN a filename does not match any known pattern, THE Legal_Ingestion_Pipeline SHALL classify the document as law_type "General"

### Requirement 4: PDF Processing Enhancement

**User Story:** As a developer, I want the system to handle complex government PDF layouts, so that legal text is extracted accurately despite formatting variations.

#### Acceptance Criteria

1. WHEN a PDF contains multi-column layouts, THE Legal_Ingestion_Pipeline SHALL extract text in reading order
2. WHEN a PDF contains headers and footers, THE Legal_Ingestion_Pipeline SHALL exclude repetitive header/footer content from chunks
3. WHEN a PDF contains tables, THE Legal_Ingestion_Pipeline SHALL preserve table structure in extracted text
4. WHEN a PDF extraction fails, THE Legal_Ingestion_Pipeline SHALL log the error and continue processing remaining pages
5. WHEN text extraction produces empty content, THE Legal_Ingestion_Pipeline SHALL log a warning and skip the document

### Requirement 5: Structured Legal Chunking

**User Story:** As a Legal Sentinel user, I want legal documents to be chunked with structure awareness, so that search results preserve legal context and hierarchy.

#### Acceptance Criteria

1. WHEN processing a legal document, THE Legal_Ingestion_Pipeline SHALL identify section boundaries using patterns like "Section X"
2. WHEN processing a legal document, THE Legal_Ingestion_Pipeline SHALL identify proviso clauses using patterns like "Provided that"
3. WHEN processing a legal document, THE Legal_Ingestion_Pipeline SHALL identify sub-clauses using patterns like "(a)", "(b)", "(c)"
4. WHEN creating a Legal_Chunk, THE System SHALL extract the section_number from the text
5. WHEN creating a Legal_Chunk, THE System SHALL preserve the chunk_type (main, proviso, sub_clause)

### Requirement 6: Metadata Extraction

**User Story:** As a Legal Sentinel user, I want legal chunks to include relevant metadata, so that queries can be filtered by turnover thresholds and sector tags.

#### Acceptance Criteria

1. WHEN processing legal text containing "turnover exceeding 5 crore", THE Legal_Ingestion_Pipeline SHALL extract turnover_threshold as 50000000
2. WHEN processing legal text containing "turnover exceeding 50 crore", THE Legal_Ingestion_Pipeline SHALL extract turnover_threshold as 500000000
3. WHEN processing legal text mentioning "textile" or "garment", THE Legal_Ingestion_Pipeline SHALL add sector_tag "Textile"
4. WHEN processing legal text mentioning "manufacturing" or "production", THE Legal_Ingestion_Pipeline SHALL add sector_tag "Manufacturing"
5. WHEN processing legal text containing date patterns like "w.e.f. 01-04-2023", THE Legal_Ingestion_Pipeline SHALL extract effective_date in ISO format

### Requirement 7: Vector Database Population

**User Story:** As a system administrator, I want processed legal chunks to be automatically stored in the vector database, so that Legal Sentinel queries can retrieve relevant legal information.

#### Acceptance Criteria

1. WHEN the Seed_Data_Processor processes a PDF, THE System SHALL generate embeddings for each Legal_Chunk using sentence transformers
2. WHEN storing a Legal_Chunk, THE Vector_Database SHALL persist the text content, metadata, and embedding vector
3. WHEN storing a Legal_Chunk, THE Vector_Database SHALL create searchable indices for section_number and law_type
4. WHEN all chunks from a document are stored, THE System SHALL log the total number of chunks added
5. WHEN the database population completes, THE System SHALL provide statistics including total documents processed and total chunks created

### Requirement 8: Idempotent Operations

**User Story:** As a system administrator, I want to safely re-run the seeding process, so that I can update the database without creating duplicate entries.

#### Acceptance Criteria

1. WHEN a file already exists in the download directory, THE Seed_Downloader SHALL skip downloading that file
2. WHEN processing a document that has already been ingested, THE Seed_Data_Processor SHALL detect existing chunks and skip re-processing
3. WHEN the seeding process is interrupted, THE System SHALL resume from the last successful step on restart
4. WHEN re-running the complete seeding pipeline, THE System SHALL complete without errors or duplicate data
5. WHEN checking for existing data, THE System SHALL use document filename and modification timestamp as unique identifiers

### Requirement 9: Progress Feedback and Logging

**User Story:** As a system administrator, I want detailed progress feedback during the seeding process, so that I can monitor the system and troubleshoot issues.

#### Acceptance Criteria

1. WHEN downloading a file, THE System SHALL display a progress message with the filename and download status
2. WHEN processing a PDF, THE System SHALL display the current page number and total pages
3. WHEN creating Legal_Chunks, THE System SHALL display the number of chunks created per document
4. WHEN storing chunks in the Vector_Database, THE System SHALL display the storage progress percentage
5. WHEN the seeding process completes, THE System SHALL display a summary report with total files downloaded, documents processed, and chunks created

### Requirement 10: Directory Structure Management

**User Story:** As a system administrator, I want the system to automatically create required directories, so that the seeding process works on a fresh installation.

#### Acceptance Criteria

1. WHEN the Seed_Downloader is executed, THE System SHALL create the `./data/initial_acts/` directory if it does not exist
2. WHEN the Seed_Downloader is executed, THE System SHALL create the `./scripts/` directory if it does not exist
3. WHEN the Vector_Database is initialized, THE System SHALL create the `./legal_db/` directory if it does not exist
4. WHEN creating directories, THE System SHALL set appropriate permissions for read/write access
5. WHEN a directory creation fails, THE System SHALL log the error and terminate with a clear error message

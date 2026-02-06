# Legal Documents Directory

This directory contains downloaded legal documents from official government sources.

## Purpose

The Legal Data Seeding System downloads foundational Indian legal documents to this directory, which are then processed and ingested into the MicroCFO vector database.

## Expected Documents

The following documents will be downloaded by the `seed_downloader.py` script or added manually:

### Tax Laws (Latest 2025 Edition)
1. **Income-tax-Act-2025.pdf** - Income Tax Act 2025 (Updated)
2. **GST-Acts-and-Rules-Bare-Law-11-04-2025.pdf** - GST Acts and Rules Bare Law - April 2025 Edition

### Corporate & Other Laws
3. **Companies_Act_2013.pdf** - Companies Act 2013
4. **CGST_Act_2017.pdf** - Central Goods and Services Tax Act 2017
5. **IGST_Act_2017.pdf** - Integrated Goods and Services Tax Act 2017
6. **PLI_Textiles_Guidelines.pdf** - Production Linked Incentive Scheme for Textiles

## Usage

To download all documents:

```bash
python scripts/seed_downloader.py
```

To specify a custom output directory:

```bash
python scripts/seed_downloader.py --output-dir /path/to/directory
```

## Notes

- Downloaded files are automatically skipped on subsequent runs (idempotent)
- Files are downloaded from official government sources
- SSL certificate issues are handled automatically
- Network timeouts trigger automatic retries with exponential backoff

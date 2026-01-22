# Legal Documents Directory

This directory contains downloaded legal documents from official government sources.

## Purpose

The Legal Data Seeding System downloads foundational Indian legal documents to this directory, which are then processed and ingested into the MicroCFO vector database.

## Expected Documents

The following documents will be downloaded by the `seed_downloader.py` script:

1. **CGST_Act_2017.pdf** - Central Goods and Services Tax Act 2017
2. **IGST_Act_2017.pdf** - Integrated Goods and Services Tax Act 2017
3. **Income_Tax_Act_1961.pdf** - Income Tax Act 1961
4. **Companies_Act_2013.pdf** - Companies Act 2013
5. **PLI_Textiles_Guidelines.pdf** - Production Linked Incentive Scheme for Textiles

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

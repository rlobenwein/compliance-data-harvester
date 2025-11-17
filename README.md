# Compliance Data Harvester

A Python application that collects, processes, and version-controls regulatory data across multiple countries and regions, producing structured JSON files suitable for automated compliance analysis and integration with other tools.

## Features

- **Web Scraping**: Automatically fetches regulatory content from official websites
- **PDF Extraction**: Extracts text from PDF documents when HTML scraping is not available
- **Structured Processing**: Normalizes and extracts articles, summaries, and developer guidance
- **Version Control**: Maintains date-stamped versions of all regulations
- **Schema Validation**: Ensures all outputs conform to the required JSON schema using Pydantic
- **Multi-Region Support**: Handles regulations from EU, USA, Brazil, and more

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The application uses an environment variable to determine where to store regulation data. You can set it in two ways:

### Option 1: Using .env file (Recommended)

Create a `.env` file in the project root:

```bash
REGULATION_DATA_DIR=/path/to/regulation-data
```

The application will automatically load this file using `python-dotenv`.

### Option 2: Using environment variable

```bash
export REGULATION_DATA_DIR=/path/to/regulation-data
```

**Note:** If `REGULATION_DATA_DIR` is not set, the application will default to `./regulation-data` in the current directory and display a warning message.

## Usage

### Initialize

First, initialize the directory structure and `regions.json`:

```bash
python main.py init
```

Or using the module directly:

```bash
python -m regulation_ingestor.main init
```

Or if you have a custom data directory:

```bash
python main.py init --data-dir /path/to/data
```

### Update a Single Regulation

Update a specific regulation:

```bash
python main.py update eu gdpr
python main.py update usa hipaa
python main.py update brazil lgpd
```

### Update All Regulations

Update all regulations at once:

```bash
python main.py update all
```

### Options

- `--data-dir PATH`: Override the `REGULATION_DATA_DIR` environment variable
- `--dry-run`: Validate data without writing files
- `--verbose` or `-v`: Print detailed output during processing

Example with options:

```bash
python main.py update eu gdpr --verbose --dry-run
```

## Directory Structure

The application creates the following directory structure (matching MCP server requirements):

```
<regulation-data-dir>/
├── regions.json
├── eu/
│   ├── gdpr.json              # Active file (latest version)
│   ├── gdpr_2025-02-14.json  # Versioned file
│   ├── dora.json
│   └── dora_2025-02-14.json
├── usa/
│   ├── hipaa.json
│   ├── hipaa_2025-02-14.json
│   ├── ccpa.json
│   └── ...
└── brazil/
    ├── lgpd.json
    └── lgpd_2025-02-14.json
```

## Versioning Strategy

Each regulation update creates two files:

1. **Versioned file**: `{regulation_id}_{YYYY-MM-DD}.json` - A date-stamped snapshot
2. **Active file**: `{regulation_id}.json` - Always points to the latest version (copied, not symlinked for Windows compatibility)

This allows you to:
- Track changes over time
- Roll back to previous versions if needed
- Always have the latest version available at a predictable path

## Data Schema

Each regulation JSON file follows this structure:

```json
{
  "id": "gdpr",
  "name": "General Data Protection Regulation",
  "region": "EU",
  "risk_category": "high",
  "summary": "High-level description...",
  "articles": [
    {
      "article": "32",
      "title": "Security of Processing",
      "summary": "Explanation...",
      "notes": null
    }
  ],
  "developer_guidance": [
    "Encrypt sensitive data",
    "Enforce access control",
    "Minimize personal data storage"
  ]
}
```

## Architecture

The application is organized into modular layers:

### Sources Layer (`sources/`)
- `fetcher.py`: HTTP client for downloading HTML/PDF
- `html_parser.py`: BeautifulSoup-based HTML text extraction
- `pdf_parser.py`: PDF text extraction using pypdf
- `fallback.py`: Orchestrates HTML → PDF → manual fallback strategy

### Processors Layer (`processors/`)
- `normalizer.py`: Text cleaning and normalization
- `extractor.py`: Article extraction, summary generation, guidance extraction
- `validator.py`: Pydantic models for schema validation

### Writers Layer (`writers/`)
- `versioning.py`: Versioned file management
- `output.py`: Directory structure creation and JSON writing

### Configuration (`config.py`)
- Loads environment variables and `regions.json`
- Provides typed configuration classes

## Extension Points

### LLM Integration

The extractor module is designed to support LLM-assisted extraction. You can extend `processors/extractor.py` to:

- Generate more accurate summaries
- Extract better article titles
- Generate comprehensive developer guidance
- Improve article content extraction

### Custom Parsers

You can add regulation-specific parsers by extending the `Extractor` class or creating custom extractors for specific regulations.

### Manual Overrides

If automated extraction fails, the system will:
1. Print instructions for manual PDF placement
2. Allow you to place PDFs in `./manual/{region_id}/{regulation_id}.pdf`
3. Re-run the scraper to process the manual file

## Troubleshooting

### "regions.json not found"

Run the init command:
```bash
python main.py init
```

### "Failed to extract content from all sources"

This means both HTML and PDF extraction failed. Options:
1. Check if the source URLs are still valid
2. Manually download the PDF and place it in `./manual/{region_id}/{regulation_id}.pdf`
3. Update the source URLs in `regions.json`

### "PDF is encrypted"

Some PDFs are password-protected. You may need to:
1. Find an unencrypted version
2. Manually extract the text
3. Create a custom parser for that specific regulation

### Encoding Issues

If you encounter encoding errors, the HTML parser will attempt to auto-detect encoding. For PDFs, ensure the PDF is not corrupted.

## Contributing

To add support for new regions or regulations:

1. Add the region and regulation to `regions.json` (or use the init command)
2. Ensure source URLs are valid
3. Test extraction with: `python main.py update <region> <regulation> --verbose`

## License

[Specify your license here]


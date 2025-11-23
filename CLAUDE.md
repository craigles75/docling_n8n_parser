# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a standalone Python script that extracts tables and text from PDF files using the Docling library. It's specifically designed for integration with n8n workflows and outputs structured JSON to stdout.

**Core Functionality:**
- Single-file Python script (`docling_parser.py`)
- Extracts tables from PDFs with headers and data in structured format
- Extracts full text content (exported as Markdown when available)
- Returns JSON output for easy consumption by automation tools
- Exit codes: 0 for success, 1 for failure

## Running and Testing

### Dependencies

The project uses `uv` for Python package management. Dependencies are handled in two ways:

1. **Run without pre-installation** (recommended):
   ```bash
   uv run --with docling docling_parser.py document.pdf
   ```

2. **Install dependencies first**:
   ```bash
   uv pip install docling
   python docling_parser.py document.pdf
   ```

### Command Line Usage

**File path mode:**
```bash
# Basic usage (extracts both tables and text)
python docling_parser.py document.pdf

# Extract only tables
python docling_parser.py document.pdf --no-text

# Extract only text
python docling_parser.py document.pdf --no-tables

# Pretty print for debugging
python docling_parser.py document.pdf --pretty
```

**Stdin mode (for n8n integration):**
```bash
# Pipe PDF binary data to stdin
cat document.pdf | python docling_parser.py --stdin

# With uv
cat document.pdf | uv run --with docling docling_parser.py --stdin

# Decode base64 and pipe (common in n8n)
echo "$BASE64_DATA" | base64 -d | python docling_parser.py --stdin
```

### Testing

Test the script with sample PDFs in the `tmp/` directory:

```bash
# Test with pretty output
uv run --with docling docling_parser.py tmp/64ccac8e-0644-41d8-b688-9f93b10190d4.pdf --pretty

# Check exit code
echo $?  # Should be 0 for success, 1 for failure
```

## Architecture

### Script Structure

The script has two main functions:

1. **`parse_pdf(pdf_path, extract_tables=True, extract_text=True)`**
   - Core parsing function
   - Returns dictionary with success/failure status
   - Handles file validation before processing
   - Catches all exceptions and returns error structure

2. **`main()`**
   - CLI entry point with argparse
   - Outputs JSON to stdout
   - Sets exit codes based on success/failure

### Output Format

**Success response:**
```json
{
  "success": true,
  "file": "/absolute/path/to/file.pdf",
  "filename": "file.pdf",
  "tables": [
    {
      "headers": ["Column1", "Column2"],
      "data": [["val1", "val2"], ["val3", "val4"]],
      "num_rows": 2,
      "num_cols": 2
    }
  ],
  "text": "Full document text...",
  "metadata": {
    "page_count": 5,
    "table_count": 1
  }
}
```

**Error response:**
```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Error description",
  "file": "/path/to/file.pdf"
}
```

### Table Extraction Logic

The script attempts multiple methods to extract table data (lines 88-109):

1. First tries `table.to_dataframe()` if available (returns pandas DataFrame)
2. Falls back to `table.data` for raw table data
3. Auto-detects headers from first row if DataFrame method not available
4. Individual table extraction failures are caught and stored in table's error field

### Text Extraction Logic

The script attempts multiple methods to extract text (lines 117-127):

1. First tries `export_to_markdown()` (preferred for formatting)
2. Falls back to `document.text` property
3. Final fallback: string conversion of document object
4. Text extraction errors are stored in `text_extraction_error` field

## n8n Integration

The script supports two integration methods:

### Method 1: Stdin Mode (Recommended - No Temp Files)

Use Execute Command node to pipe binary data directly:

```bash
# In n8n Execute Command node:
# Command: bash
# Arguments: -c "uv run --with docling /path/to/docling_parser.py --stdin"
# Then pipe the binary data from previous node
```

Workflow:
1. Receive/read PDF file in n8n (HTTP Request, Webhook, Read Binary File)
2. Pipe binary data to Execute Command node with `--stdin` flag
3. Parse JSON stdout in subsequent node
4. Process extracted tables/text

### Method 2: File Path Mode (Traditional)

Workflow:
1. Receive/read PDF file in n8n
2. Save binary data to temporary file using Code node
3. Execute this script via Execute Command node with file path
4. Parse JSON stdout in subsequent Code node
5. Process extracted tables/text

### Method 3: Flask API

Alternative: Wrap in Flask API for HTTP-based integration (see README.md lines 182-214).

## Important Notes

- The script is completely self-contained (no imports from other local modules)
- All output goes to stdout as JSON
- Errors are returned as JSON (not raised), ensuring n8n can always parse response
- File paths should be absolute for reliability (when using file path mode)
- **Stdin mode** eliminates need for temporary file management in n8n workflows
- When using stdin mode, the output JSON shows `"file": "<stdin>"` and `"filename": "<stdin>"`
- The `tmp/` directory contains sample PDFs for testing

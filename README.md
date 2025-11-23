# Docling PDF Parser for n8n

Extract tables and text from PDF files in your n8n workflows. No temporary file management required.

## Quick Start

### 1. Install uv on your n8n server

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Copy the script to your server

```bash
# Download or clone this repository
git clone <repo-url>
cd docling_n8n_parser
```

That's it! No need to install Python packages - `uv` handles dependencies automatically.

## Using in n8n

### Recommended: Stdin Mode (No Temp Files)

This is the simplest approach - pipe PDF binary data directly to the parser.

**n8n Workflow:**

1. **Get PDF** - Use HTTP Request, Webhook, or Read Binary File node

2. **Execute Command Node**
   - **Command**: `bash`
   - **Arguments**: `-c "uv run --with docling /path/to/docling_parser.py --stdin"`
   - **Binary Data**: Enable and select your PDF binary data

3. **Code Node** - Parse the JSON output:
   ```javascript
   const result = JSON.parse($input.item.json.stdout);
   return result;
   ```

4. **Process your data** - Access tables and text:
   ```javascript
   // Get all tables
   const tables = $json.tables;

   // Get first table
   const firstTable = $json.tables[0];
   const headers = firstTable.headers;  // ["Column1", "Column2"]
   const rows = firstTable.data;         // [["val1", "val2"], ...]

   // Get extracted text
   const fullText = $json.text;

   // Convert table to array of objects
   const tableObjects = rows.map(row => {
     const obj = {};
     headers.forEach((header, i) => {
       obj[header] = row[i];
     });
     return obj;
   });
   ```

### Output Format

**Success:**
```json
{
  "success": true,
  "file": "<stdin>",
  "filename": "<stdin>",
  "tables": [
    {
      "headers": ["Column1", "Column2", "Column3"],
      "data": [
        ["row1col1", "row1col2", "row1col3"],
        ["row2col1", "row2col2", "row2col3"]
      ],
      "num_rows": 2,
      "num_cols": 3
    }
  ],
  "text": "Full document text content...",
  "metadata": {
    "page_count": 5,
    "table_count": 1
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Error description",
  "file": "<stdin>"
}
```

## Command Line Options

```bash
# Extract both tables and text (default)
cat document.pdf | uv run --with docling docling_parser.py --stdin

# Extract only tables (skip text)
cat document.pdf | uv run --with docling docling_parser.py --stdin --no-text

# Extract only text (skip tables)
cat document.pdf | uv run --with docling docling_parser.py --stdin --no-tables

# Pretty print for debugging
cat document.pdf | uv run --with docling docling_parser.py --stdin --pretty
```

## Testing

Test with a sample PDF:

```bash
# Using stdin mode
cat tmp/sample.pdf | uv run --with docling docling_parser.py --stdin --pretty

# Using file path mode
uv run --with docling docling_parser.py tmp/sample.pdf --pretty

# Check exit code (0 = success, 1 = failure)
echo $?
```

## Troubleshooting

**"uv command not found"**
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`

**"No data received from stdin"**
- Ensure binary data is being piped correctly in n8n
- Check that Binary Data is enabled in Execute Command node

**"Empty tables array"**
- PDF might not contain structured tables
- Use `--pretty` flag to inspect full output
- Try extracting text only with `--no-tables`

**Memory issues with large PDFs**
- Increase available memory for the process
- Consider splitting large PDFs into smaller files

## System Requirements

- Python 3.8 or higher (usually pre-installed)
- uv (handles all Python dependencies)
- Sufficient memory for PDF processing (varies by PDF size)

---

## Alternative Methods

### File Path Mode

If you need to use file paths instead of stdin:

```bash
# In n8n Execute Command node:
# Command: uv
# Arguments: run --with docling /path/to/docling_parser.py /path/to/document.pdf
```

You'll need to save the binary data to a temp file first using a Code node:

```javascript
const fs = require('fs');
const path = '/tmp/temp_pdf.pdf';
const binaryData = items[0].binary.data;
fs.writeFileSync(path, Buffer.from(binaryData.data, 'base64'));
return [{ json: { pdf_path: path } }];
```

### Flask API Wrapper

For HTTP-based integration, see the Flask example in the codebase.

### Pre-installing Docling

If you prefer to install docling once instead of using `uv run --with`:

```bash
uv pip install docling
python3 docling_parser.py document.pdf
```

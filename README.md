# Docling PDF Parser for n8n

A Python script that extracts tables and text from PDF files using the Docling library, designed for easy integration with n8n workflows.

## Installation

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on Windows:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Docling using uv

```bash
uv pip install docling
```

Or use uv to run the script directly without manual installation:
```bash
uv run --with docling docling_parser.py document.pdf
```

### 3. Make the script executable (optional)

```bash
chmod +x docling_parser.py
```

## Usage

### Basic Usage

Extract both tables and text from a PDF:

**Using standard Python:**
```bash
python docling_parser.py document.pdf
```

**Using uv (automatically handles dependencies):**
```bash
uv run --with docling docling_parser.py document.pdf
```

### Options

- `--no-tables` - Skip table extraction, only extract text
- `--no-text` - Skip text extraction, only extract tables
- `--pretty` - Pretty print JSON output (useful for debugging)

### Examples

#### Extract only tables:
```bash
python docling_parser.py invoice.pdf --no-text
# Or with uv:
uv run --with docling docling_parser.py invoice.pdf --no-text
```

#### Extract only text:
```bash
python docling_parser.py report.pdf --no-tables
# Or with uv:
uv run --with docling docling_parser.py report.pdf --no-tables
```

#### Pretty print for debugging:
```bash
python docling_parser.py document.pdf --pretty
# Or with uv:
uv run --with docling docling_parser.py document.pdf --pretty
```

## Output Format

The script outputs JSON to stdout with the following structure:

```json
{
  "success": true,
  "file": "/absolute/path/to/file.pdf",
  "filename": "file.pdf",
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

### Error Format

If an error occurs, the output will be:

```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Error description",
  "file": "/path/to/file.pdf"
}
```

## Integration with n8n

### Method 1: Using Execute Command Node

1. **Read/Receive PDF file** - Use HTTP Request, Webhook, or Read Binary File node

2. **Save to temporary file** - Use Code node to save the binary data:
   ```javascript
   const fs = require('fs');
   const path = '/tmp/temp_pdf.pdf';
   
   // Get binary data
   const binaryData = items[0].binary.data;
   
   // Write to file
   fs.writeFileSync(path, Buffer.from(binaryData.data, 'base64'));
   
   return [{ json: { pdf_path: path } }];
   ```

3. **Execute Parser** - Use Execute Command node:
   
   **Option A: Using uv (recommended - handles dependencies automatically)**
   - **Command**: `uv`
   - **Arguments**: `run --with docling /path/to/docling_parser.py {{$json.pdf_path}}`
   
   **Option B: Using Python directly (requires pre-installed docling)**
   - **Command**: `python3`
   - **Arguments**: `/path/to/docling_parser.py {{$json.pdf_path}}`
   
4. **Parse JSON Output** - The Execute Command node will return the JSON as text. Use a Code node to parse it:
   ```javascript
   const result = JSON.parse(items[0].json.stdout);
   return [{ json: result }];
   ```

5. **Process Tables** - Now you can access the structured table data:
   ```javascript
   // Access first table
   const firstTable = $json.tables[0];
   
   // Get headers
   const headers = firstTable.headers;
   
   // Get all rows
   const rows = firstTable.data;
   
   // Convert to array of objects (like CSV parsing)
   const tableObjects = rows.map(row => {
     const obj = {};
     headers.forEach((header, i) => {
       obj[header] = row[i];
     });
     return obj;
   });
   
   return tableObjects.map(obj => ({ json: obj }));
   ```

### Method 2: Using HTTP Request to a Flask API (Advanced)

If you prefer an API approach, you can wrap this script in a simple Flask server:

```python
from flask import Flask, request, jsonify
import tempfile
import os

app = Flask(__name__)

@app.route('/parse-pdf', methods=['POST'])
def parse_pdf_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        # Parse the PDF
        from docling_parser import parse_pdf
        result = parse_pdf(tmp_path)
        return jsonify(result)
    finally:
        # Clean up
        os.unlink(tmp_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Then use n8n's HTTP Request node to POST the PDF to `http://localhost:5000/parse-pdf`.

## Troubleshooting

### Common Issues

1. **"Docling not installed" error**
   - Solution: Run `uv pip install docling` or use `uv run --with docling` to run the script

2. **File not found error**
   - Solution: Ensure you're using absolute paths
   - Check file permissions

3. **Empty tables array**
   - Solution: The PDF might not contain properly formatted tables
   - Try with `--pretty` flag to see full output

4. **Memory issues with large PDFs**
   - Solution: Process PDFs in smaller chunks or increase available memory

5. **uv command not found**
   - Solution: Install uv first: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Make sure uv is in your PATH

## System Requirements

- Python 3.8 or higher
- Sufficient memory for PDF processing (depends on PDF size)
- Write permissions for temporary file storage (if saving PDFs)

## Testing

Test the script with a sample PDF:

```bash
# Test with uv (recommended - no pre-installation needed)
uv run --with docling docling_parser.py test.pdf --pretty

# Or if you've installed docling with uv pip install
python docling_parser.py test.pdf --pretty

# Check exit code
echo $?  # Should be 0 for success, 1 for failure
```

## License

This script is provided as-is for integration with n8n workflows.

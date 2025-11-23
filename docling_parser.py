#!/usr/bin/env python3
"""
Docling PDF Parser for n8n Integration
Extracts tables and text from PDF files using Docling library
Outputs structured JSON to stdout for easy n8n consumption
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

try:
    from docling.document_converter import DocumentConverter
except ImportError:
    print(json.dumps({
        "error": "Docling not installed",
        "message": "Please install docling: pip install docling",
        "success": False
    }))
    sys.exit(1)


def parse_pdf(pdf_path: str, extract_tables: bool = True, extract_text: bool = True) -> Dict[str, Any]:
    """
    Parse PDF file and extract tables and/or text content
    
    Args:
        pdf_path: Path to the PDF file
        extract_tables: Whether to extract tables (default: True)
        extract_text: Whether to extract text content (default: True)
    
    Returns:
        Dictionary containing extracted data and metadata
    """
    try:
        # Verify file exists
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return {
                "success": False,
                "error": "File not found",
                "message": f"PDF file does not exist: {pdf_path}"
            }
        
        if not pdf_file.is_file():
            return {
                "success": False,
                "error": "Invalid file",
                "message": f"Path is not a file: {pdf_path}"
            }
        
        # Initialize Docling converter
        converter = DocumentConverter()
        
        # Convert the PDF
        result = converter.convert(pdf_path)
        
        # Prepare output structure
        output = {
            "success": True,
            "file": str(pdf_file.absolute()),
            "filename": pdf_file.name,
            "tables": [],
            "text": "",
            "metadata": {
                "page_count": 0,
                "table_count": 0
            }
        }
        
        # Extract tables if requested
        if extract_tables:
            tables_data = []
            
            # Iterate through document tables
            for table in result.document.tables:
                table_dict = {
                    "data": [],
                    "headers": [],
                    "num_rows": 0,
                    "num_cols": 0
                }
                
                # Convert table to list of lists (rows)
                # Docling provides table data in various formats
                # We'll try to get it as a DataFrame first, then fall back
                try:
                    # Try to get as pandas DataFrame if available
                    if hasattr(table, 'to_dataframe'):
                        df = table.to_dataframe()
                        table_dict["headers"] = df.columns.tolist()
                        table_dict["data"] = df.values.tolist()
                        table_dict["num_rows"] = len(df)
                        table_dict["num_cols"] = len(df.columns)
                    # Alternative: get raw table data
                    elif hasattr(table, 'data'):
                        table_dict["data"] = table.data
                        if table_dict["data"]:
                            table_dict["num_rows"] = len(table_dict["data"])
                            table_dict["num_cols"] = len(table_dict["data"][0]) if table_dict["data"] else 0
                            # Try to detect headers (first row)
                            if len(table_dict["data"]) > 0:
                                table_dict["headers"] = table_dict["data"][0]
                except Exception as e:
                    # If table extraction fails, store error info
                    table_dict["error"] = str(e)
                
                tables_data.append(table_dict)
            
            output["tables"] = tables_data
            output["metadata"]["table_count"] = len(tables_data)
        
        # Extract text if requested
        if extract_text:
            try:
                # Get full document text
                if hasattr(result.document, 'export_to_markdown'):
                    output["text"] = result.document.export_to_markdown()
                elif hasattr(result.document, 'text'):
                    output["text"] = result.document.text
                else:
                    output["text"] = str(result.document)
            except Exception as e:
                output["text"] = ""
                output["text_extraction_error"] = str(e)
        
        # Try to get page count
        try:
            if hasattr(result.document, 'pages'):
                output["metadata"]["page_count"] = len(result.document.pages)
        except:
            pass
        
        return output
        
    except Exception as e:
        return {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
            "file": pdf_path
        }


def main():
    """Main entry point for command line usage"""
    parser = argparse.ArgumentParser(
        description="Extract tables and text from PDF files using Docling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract tables and text from a PDF
  python docling_parser.py document.pdf
  
  # Extract only tables
  python docling_parser.py document.pdf --no-text
  
  # Extract only text
  python docling_parser.py document.pdf --no-tables
  
  # Pretty print JSON output
  python docling_parser.py document.pdf --pretty
        """
    )
    
    parser.add_argument(
        'pdf_file',
        help='Path to the PDF file to parse'
    )
    
    parser.add_argument(
        '--no-tables',
        action='store_true',
        help='Skip table extraction'
    )
    
    parser.add_argument(
        '--no-text',
        action='store_true',
        help='Skip text extraction'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty print JSON output'
    )
    
    args = parser.parse_args()
    
    # Parse the PDF
    result = parse_pdf(
        args.pdf_file,
        extract_tables=not args.no_tables,
        extract_text=not args.no_text
    )
    
    # Output JSON to stdout
    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()

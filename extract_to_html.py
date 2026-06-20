#!/usr/bin/env python3
"""
CSV to HTML Extraction and JSON Transformation Script

This script processes large CSV files and either:
1. Extracts thread content into separate HTML files (default)
2. Transforms all columns except content column into JSON format

It's designed to handle CSV files with 3M+ rows efficiently using built-in Python modules.

Usage:
    # Extract thread content to HTML
    python extract_to_html.py [--input FILE] [--output-dir DIR] [--id-column NAME] [--content-column NAME]

    # Transform to JSON (excluding content column)
    python extract_to_html.py --mode json [--input FILE] [--output-dir DIR] [--content-column NAME]
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from time import time

# HTML template for sidecar files (using simple string formatting)
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{thread_title}</title>
</head>
<body>
{thread_content}
</body>
</html>
"""

# Default column names
DEFAULT_ID_COLUMN = "ID"
DEFAULT_CONTENT_COLUMN = "Thread Content"

# Output directories
DEFAULT_OUTPUT_DIR = Path("output")
HTML_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "html"
MANIFEST_FILE = DEFAULT_OUTPUT_DIR / "manifest.json"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract thread content from CSV files to HTML or transform to JSON format"
    )
    parser.add_argument(
        "--input", "-i",
        default="data/Threads__10.csv",
        help="Input CSV file path (default: data/Threads__10.csv)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--id-column",
        default=DEFAULT_ID_COLUMN,
        help=f"Name of the ID column (default: {DEFAULT_ID_COLUMN})"
    )
    parser.add_argument(
        "--content-column",
        default=DEFAULT_CONTENT_COLUMN,
        help=f"Name of the Thread Content column (default: {DEFAULT_CONTENT_COLUMN})"
    )
    parser.add_argument(
        "--mode",
        choices=["html", "json"],
        default="html",
        help="Output mode: 'html' for HTML extraction, 'json' for JSON transformation (default: html)"
    )
    parser.add_argument(
        "--skip-empty",
        action="store_true",
        help="Skip rows with empty thread content (HTML mode only)"
    )
    
    return parser.parse_args()


def create_directories(output_dir, mode):
    """Create output directories if they don't exist."""
    output_path = Path(output_dir)
    
    if mode == "html":
        html_path = output_path / "html"
        output_path.mkdir(parents=True, exist_ok=True)
        html_path.mkdir(parents=True, exist_ok=True)
        return output_path, html_path
    else:
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path, None


def process_csv_html(args):
    """Process CSV file and extract thread content to HTML files."""
    input_file = Path(args.input)
    output_path, html_path = create_directories(args.output_dir, "html")
    
    # Verify input file exists
    if not input_file.exists():
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Increase CSV field size limit for large fields (set to very high value)
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = int(max_int / 2)
    
    # Initialize manifest dictionary
    manifest = {}
    
    # Process CSV row by row (memory efficient)
    total_rows = 0
    processed_rows = 0
    start_time = time()
    
    print(f"Processing CSV file: {input_file}")
    print(f"Output directory: {output_path}")
    print(f"Mode: HTML extraction")
    
    try:
        # Open and read CSV file
        with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as csvfile:
            reader = csv.DictReader(csvfile, quotechar='"', delimiter=',')
            
            # Check if required columns exist
            if args.id_column not in reader.fieldnames:
                print(f"Error: ID column '{args.id_column}' not found in CSV")
                print(f"Available columns: {reader.fieldnames}")
                sys.exit(1)
            if args.content_column not in reader.fieldnames:
                print(f"Error: Content column '{args.content_column}' not found in CSV")
                print(f"Available columns: {reader.fieldnames}")
                sys.exit(1)
            
            # Process each row
            for row in reader:
                total_rows += 1
                
                # Get thread ID and content
                thread_id = row.get(args.id_column)
                thread_content = row.get(args.content_column)
                ticket_id = row.get("Ticket id")
                
                # Skip if ID is missing
                if thread_id is None or str(thread_id).strip() == "":
                    continue
                
                # Convert ID to string
                thread_id_str = str(thread_id).strip()
                ticket_id_str = str(ticket_id).strip() if ticket_id is not None else ""
                thread_title = (
                    f"ThreadID {thread_id_str} - TicketID {ticket_id_str}"
                    if ticket_id_str
                    else f"Thread {thread_id_str}"
                )
                
                # Handle empty content
                if thread_content is None or str(thread_content).strip() == "":
                    if args.skip_empty:
                        continue
                    thread_content = ""
                
                # Create HTML content (preserve original without escaping)
                html_content = HTML_TEMPLATE.format(
                    thread_title=thread_title,
                    thread_content=str(thread_content) if thread_content is not None else ""
                )
                
                # Save HTML file
                html_filename = f"{thread_id_str}.html"
                html_filepath = html_path / html_filename
                
                with open(html_filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Add to manifest
                manifest[thread_id_str] = {
                    "html_path": f"html/{html_filename}",
                    "Ticket id": ticket_id_str,
                }
                
                processed_rows += 1
                
                # Report progress every 100,000 rows
                if total_rows % 100000 == 0:
                    elapsed = time() - start_time
                    rate = processed_rows / elapsed if elapsed > 0 else 0
                    print(f"Processed {total_rows:,} rows, generated {processed_rows:,} HTML files ({rate:.0f} rows/sec)")
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
        sys.exit(1)
    
    # Save manifest
    manifest_path = output_path / f"{input_file.stem}_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # Final statistics
    elapsed = time() - start_time
    print(f"\nProcessing complete!")
    print(f"Total rows processed: {total_rows:,}")
    print(f"HTML files generated: {processed_rows:,}")
    print(f"Manifest saved to: {manifest_path}")
    print(f"Total time: {elapsed:.1f} seconds")
    print(f"Average rate: {processed_rows/elapsed:.0f} rows/second")
    
    return processed_rows


def process_csv_json(args):
    """Process CSV file and transform to JSON format (excluding content column)."""
    input_file = Path(args.input)
    output_path, _ = create_directories(args.output_dir, "json")
    
    # Verify input file exists
    if not input_file.exists():
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Increase CSV field size limit for large fields
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = int(max_int / 2)
    
    # Collect all records (excluding content column)
    total_rows = 0
    records = []
    start_time = time()
    
    print(f"Processing CSV file: {input_file}")
    print(f"Output directory: {output_path}")
    print(f"Mode: JSON transformation (excluding column: {args.content_column})")
    
    try:
        # Open and read CSV file
        with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as csvfile:
            reader = csv.DictReader(csvfile, quotechar='"', delimiter=',')
            
            # Check if content column exists
            # if args.content_column not in reader.fieldnames:
            #     print(f"Error: Content column '{args.content_column}' not found in CSV")
            #     print(f"Available columns: {reader.fieldnames}")
            #     sys.exit(1)
            
            # Process each row
            for row in reader:
                total_rows += 1
                
                # Create a copy of the row excluding the content column
                record = {key: value for key, value in row.items() if key != args.content_column}
                records.append(record)
                
                # Report progress every 100,000 rows
                if total_rows % 100000 == 0:
                    elapsed = time() - start_time
                    rate = total_rows / elapsed if elapsed > 0 else 0
                    print(f"Processed {total_rows:,} rows ({rate:.0f} rows/sec)")
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
        sys.exit(1)
    
    # Save JSON file
    #json_filename = "transformed_data.json"
    json_filename = input_file.stem + ".json"
    json_filepath = output_path / json_filename
    
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    # Final statistics
    elapsed = time() - start_time
    print(f"\nProcessing complete!")
    print(f"Total rows processed: {total_rows:,}")
    print(f"JSON file saved to: {json_filepath}")
    print(f"Total time: {elapsed:.1f} seconds")
    print(f"Average rate: {total_rows/elapsed:.0f} rows/second")
    
    return total_rows


def main():
    """Main entry point."""
    args = parse_arguments()
    
    if args.mode == "html":
        process_csv_html(args)
    else:
        process_csv_json(args)


if __name__ == "__main__":
    main()

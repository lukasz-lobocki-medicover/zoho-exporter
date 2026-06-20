# CSV to HTML Extraction and JSON Transformation Script

This script processes large CSV files (designed for 3M+ rows, 400MB+) and can either:
1. Extract thread content into separate HTML files
2. Transform all columns except the content column into JSON format

## Features

- Processes large CSV files efficiently using Python's built-in `csv` module
- Preserves UTF-8 encoding in thread content
- Creates individual HTML files for each thread (HTML mode)
- Generates JSON manifest mapping IDs to HTML file paths (HTML mode)
- Transforms CSV to JSON format excluding specified column (JSON mode)
- No external dependencies required

## Requirements

- Python 3.6+
- No external packages required (uses only Python standard library)

## Usage

```bash
python extract_to_html.py [options]
```

### Options

- `--input`, `-i`: Input CSV file path (default: `data/Threads__10.csv`)
- `--output-dir`, `-o`: Output directory (default: `output`)
- `--id-column`: Name of the ID column (default: `ID`)
- `--content-column`: Name of the Thread Content column (default: `Thread Content`)
- `--mode`: Output mode: `html` (default) or `json`
- `--skip-empty`: Skip rows with empty thread content (HTML mode only)

### Examples

```bash
# HTML mode: Extract thread content to HTML files
python extract_to_html.py

# JSON mode: Transform CSV to JSON (excluding content column)
python extract_to_html.py --mode json --output-dir json_output

# Process custom file in HTML mode
python extract_to_html.py --input data/my_data.csv --output-dir results

# Use different column names
python extract_to_html.py --id-column id --content-column content
```

## Output Structure

### HTML Mode
```
output/
├── manifest.json          # JSON mapping of ID to HTML file path
└── html/                  # Directory containing individual HTML files
    ├── 12345.html
    ├── 12346.html
    └── ...
```

### JSON Mode
```
json_output/
└── transformed_data.json  # JSON file with all columns except content column
```

### HTML File Format

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Thread {id} - Ticket {ticket_id}</title>
</head>
<body>
{thread_content}
</body>
</html>
```

### Manifest Format

```json
{
  "12345": {
    "html_path": "html/12345.html",
    "Ticket id": "12345"
  },
  "12346": {
    "html_path": "html/12346.html",
    "Ticket id": "12346"
  },
  ...
}
```

### JSON Format

```json
[
  {
    "ID": "12345",
    "Ticket id": "12345",
    "Sent Date And Time": "2023-01-17 11:32:16",
    ...
  },
  ...
]
```

## Performance

- Estimated processing time: ~10-15 seconds per 10,000 records
- Memory usage: Minimal (streams CSV row-by-row)
- File size handling: Designed for 400MB+ files

## Notes

- The script handles CSV files with embedded newlines within quoted fields
- Large fields (1GB+) are supported
- HTML content is preserved as-is (no escaping) to maintain original formatting
- Empty thread content rows are skipped by default (can be included by removing `--skip-empty`)

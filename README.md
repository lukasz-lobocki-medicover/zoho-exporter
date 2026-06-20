# Zoho Exporter

Utilities for exporting and transforming Zoho-related data.

This repository currently contains:
- a CSV processing script for extracting HTML sidecar files or generating JSON
- a Zoho OAuth token helper
- a Zoho Desk ticket download helper
- a small shell loop for batch processing CSV files

## Requirements

- Python 3.10+
- No third-party Python packages are required for the current scripts

## Repository contents

### `extract_from_csv.py`

Processes large CSV files and supports two modes:

1. **HTML mode** (`--mode html`, default)
   - reads a CSV file row by row
   - extracts the `Thread Content` column into separate HTML files
   - writes one HTML file per row using the row `ID` as the filename
   - creates a manifest JSON file named `<input_stem>_manifest.json`

2. **JSON mode** (`--mode json`)
   - reads a CSV file row by row
   - removes the configured content column from each record
   - writes the remaining columns to a JSON array in `<input_stem>.json`

Default column names:
- ID column: `ID`
- content column: `Thread Content`

Default input file:
- `data/Threads__10.csv`

Default output directory:
- `output`

#### Usage

```bash
python extract_from_csv.py [options]
```

#### Options

- `--input`, `-i`: Input CSV file path (default: `data/Threads__10.csv`)
- `--output-dir`, `-o`: Output directory (default: `output`)
- `--id-column`: Name of the ID column (default: `ID`)
- `--content-column`: Name of the content column (default: `Thread Content`)
- `--mode`: Output mode: `html` (default) or `json`
- `--skip-empty`: Skip rows with empty thread content in HTML mode

#### Examples

```bash
# HTML mode: extract thread content to HTML files
python extract_from_csv.py

# JSON mode: transform CSV to JSON without the content column
python extract_from_csv.py --mode json --output-dir json_output

# Process a custom file in HTML mode
python extract_from_csv.py --input data/my_data.csv --output-dir results

# Use different column names
python extract_from_csv.py --id-column id --content-column content

# Skip rows with empty thread content
python extract_from_csv.py --skip-empty
```

#### HTML mode output

Directory structure:

```text
output/
├── html/
│   ├── 12345.html
│   ├── 12346.html
│   └── ...
└── Threads__10_manifest.json
```

Example generated HTML structure:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ThreadID 12345 - TicketID 67890</title>
</head>
<body>
...thread content...
</body>
</html>
```

Example manifest entry:

```json
{
  "12345": {
    "html_path": "html/12345.html",
    "Ticket id": "67890"
  }
}
```

#### JSON mode output

Example output file name:
- `Threads__10.json`

Example JSON structure:

```json
[
  {
    "ID": "12345",
    "Ticket id": "67890",
    "Sent Date And Time": "2023-01-17 11:32:16"
  }
]
```

#### Notes

- The script is designed to process large CSV files efficiently.
- CSV rows are streamed row by row.
- Large CSV fields are supported by increasing the field size limit.
- HTML content is preserved as-is and is not escaped.
- In HTML mode, rows without an ID are skipped.
- In JSON mode, the configured content column is excluded from the output records.

### `get_tokens.py`

Interactive helper for exchanging a Zoho OAuth authorization code for tokens.

What it does:
- prompts for `client_id`
- prompts for `client_secret`
- prompts for `code`
- sends a `POST` request to `https://accounts.zoho.eu/oauth/v2/token`
- prints the returned JSON response
- prints `access_token` and `refresh_token`
- writes both values to `tokens.txt`

#### Usage

```bash
python get_tokens.py
```

### `download_imgs.py`

Despite the filename, this script currently performs token exchange and then downloads Zoho Desk tickets as JSON.
It does not document or implement image downloading in the current version.

What it does:
- prompts for `client_id`
- prompts for `client_secret`
- prompts for `code`
- sends a `POST` request to `https://accounts.zoho.eu/oauth/v2/token`
- prints the returned JSON response
- saves `access_token` and `refresh_token` to `tokens.txt`
- uses the access token to call `https://desk.zoho.eu/api/v1/tickets`
- saves the returned response to `tickets.json`

#### Usage

```bash
python download_imgs.py
```

### Shared Zoho configuration

Both `get_tokens.py` and `download_imgs.py` look for a config file named `zoho_exporter.ini` in one of these locations:
- `./zoho_exporter.ini`
- `~/.zoho_exporter.ini`

Expected format:

```ini
[zoho]
client_id = your_client_id_here
client_secret = your_client_secret_here
```

If a valid `[zoho]` section is present, the stored credentials are shown as prompt defaults.
You can press `Enter` to reuse them or type replacements.

### Output files created by the Zoho scripts

#### `tokens.txt`

Written by both `get_tokens.py` and `download_imgs.py`.

Format:

```text
access_token=...
refresh_token=...
```

#### `tickets.json`

Written by `download_imgs.py` after a successful tickets request.

The file contains the pretty-printed JSON response returned by the Zoho Desk tickets API.

### `loop.sh`

Simple shell helper for batch-processing CSV files from a local directory.

Current behavior:
- loops through `/home/la_lukasz/Code/zoho-exporter/data/*.csv`
- runs `python extract_from_csv.py --input "${file}"` for each matching file
- includes a commented example line for JSON mode

#### Usage

```bash
bash loop.sh
```

## Notes

- `ORG_ID` is hard-coded in the Zoho scripts.
- `requirements.txt` currently documents that no external dependencies are required.
- This README is aligned to the repository's current code and avoids changing functionality.

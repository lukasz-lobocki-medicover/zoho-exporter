# Zoho Exporter

Small utilities for exporting and transforming Zoho-related data.

This repository currently contains:
- `extract_from_csv.py` for converting CSV exports into HTML sidecar files or JSON
- `get_tokens.py` for exchanging a Zoho OAuth authorization code for tokens
- `loop.sh` for batch-running the CSV conversion script over a local directory

## Requirements

- Python 3.10+
- No third-party Python packages are required for the current scripts

> `requirements.txt` is informational only. The current code uses the Python standard library.

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

### Shared Zoho configuration

`get_tokens.py` looks for a config file named `zoho_exporter.ini` in one of these locations:
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

### Output files created by the Zoho helper

#### `tokens.txt`

Written by `get_tokens.py`.

Format:

```text
access_token=...
refresh_token=...
```

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

#### Note

`loop.sh` uses a hard-coded local filesystem path, so it may need adjustment before use on another machine.

### `download_imgs.py`

Downloads all remote images referenced in `<img src="...">` tags inside
HTML files and rewrites each `src` attribute to point to the locally saved
sidecar file.

What it does:
- reads `access_token` from `tokens.txt` and prompts the user (default shown in brackets)
- scans every `.html` file under the given input directory (recursive)
- for each remote image URL found in an `<img>` tag, calls `curl` with the
  Zoho Desk API auth headers to download the image
- saves each image under an `images/` subdirectory next to the HTML file,
  naming the file by the MD5 hash of the URL
- rewrites the `src` attribute in the HTML file to the relative local path
- skips images that have already been downloaded (cached by filename)

#### Usage

```bash
python download_imgs.py [--input-dir DIR]
```

#### Options

- `--input-dir`, `-i`: Directory containing HTML files (default: `output/html`)

#### Example

```bash
# Process all HTML files under output/html
python download_imgs.py

# Process a custom directory
python download_imgs.py --input-dir /path/to/html/files
```

#### Output structure

```text
output/html/
└── Threads__10/
    ├── 12345.html          ← img src attributes updated to local paths
    └── images/
        ├── a1b2c3d4....jpg
        └── e5f6a7b8....png
```

#### Notes

- `tokens.txt` is read for the default `access_token`; create it with `get_tokens.py`.
- The `orgId` header is hard-coded to `20067925477`.
- Images already present in the `images/` directory are not re-downloaded.

## Notes

- This README is aligned to the repository's current code and avoids changing functionality.

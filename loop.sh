#!/bin/bash

for file in /home/la_lukasz/Code/zoho-exporter/data/*.csv; do
    # Check if it's actually a file (and not a subdirectory)
    echo "Processing: ${file}"
    if [ -f "${file}" ]; then
       python extract_from_csv.py --input "${file}"
       # python extract_from_csv.py --mode json  --input "${file}"
    fi
done
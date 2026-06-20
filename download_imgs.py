#!/usr/bin/env python3
"""
Download Remote Images from HTML Files

Scans all HTML files in a given directory, downloads every remote image
referenced in <img src="..."> tags using the Zoho Desk API, saves each
image as a sidecar file, and rewrites the src attribute to point to the
locally saved file.

Usage:
    python download_imgs.py [--input-dir DIR]
"""

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ORG_ID = "20067925477"
TOKENS_FILENAME = "tokens.txt"


def load_access_token() -> str:
    """Try to read access_token from tokens.txt."""
    token_file = Path(TOKENS_FILENAME)
    if token_file.is_file():
        for line in token_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("access_token="):
                return line[len("access_token="):].strip()
    return ""


def prompt_with_default(prompt: str, default: str) -> str:
    """Prompt the user, showing a truncated default in brackets; return default on empty input."""
    if default:
        display = default[:8] + "..." if len(default) > 8 else default
        value = input(f"{prompt} [{display}]: ").strip()
        return value if value else default
    return input(f"{prompt}: ").strip()


def sidecar_path(url: str, images_dir: Path) -> Path:
    """Return a unique local Path for the given URL inside images_dir."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix
    # Keep only safe, short extensions; fall back to .bin
    if not suffix or len(suffix) > 8 or not suffix[1:].isalnum():
        suffix = ".bin"
    return images_dir / f"{url_hash}{suffix}"


def download_image(url: str, dest: Path, access_token: str) -> bool:
    """Download a single image via curl with Zoho auth headers.

    Returns True on success, False on failure.
    """
    cmd = [
        "curl", "-s", "-f",
        "-X", "GET", url,
        "-H", f"orgId:{ORG_ID}",
        "-H", f"Authorization:Zoho-oauthtoken {access_token}",
        "-o", str(dest),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        print(f"  Warning: failed to download {url} (exit {result.returncode})"
              + (f": {stderr}" if stderr else ""))
        return False
    return True


def process_html_file(html_file: Path, access_token: str) -> int:
    """Download remote images in html_file and rewrite their src attributes.

    Returns the number of images that were successfully downloaded or
    already cached.
    """
    content = html_file.read_text(encoding="utf-8", errors="replace")

    images_dir = html_file.parent / "images"
    images_dir.mkdir(exist_ok=True)

    updated = 0

    def replace_img(img_match: re.Match) -> str:
        nonlocal updated
        tag = img_match.group(0)

        src_match = re.search(r'src=(["\'])([^"\']+)\1', tag, re.IGNORECASE)
        if not src_match:
            return tag

        src_url = src_match.group(2)
        if not src_url.startswith(("http://", "https://")):
            return tag

        dest = sidecar_path(src_url, images_dir)

        if dest.exists():
            print(f"  Cached: {dest.name}")
        else:
            print(f"  Downloading: {src_url}")
            if not download_image(src_url, dest, access_token):
                return tag

        # Build relative POSIX path from the HTML file's directory
        rel = dest.relative_to(html_file.parent).as_posix()

        # Replace only the URL value inside the src attribute, preserving quotes
        new_tag = tag[: src_match.start(2)] + rel + tag[src_match.end(2):]
        updated += 1
        return new_tag

    new_content = re.sub(r"<img\b[^>]*>", replace_img, content, flags=re.IGNORECASE)

    if new_content != content:
        html_file.write_text(new_content, encoding="utf-8")

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download remote images referenced in HTML files and rewrite "
            "their src attributes to local sidecar paths."
        )
    )
    parser.add_argument(
        "--input-dir", "-i",
        default="output/html",
        help="Directory containing HTML files to process (default: output/html)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"Error: input directory '{input_dir}' not found or is not a directory")
        sys.exit(1)

    default_token = load_access_token()
    access_token = prompt_with_default("Enter access_token", default_token)

    if not access_token:
        print("Error: access_token is required")
        sys.exit(1)

    html_files = sorted(input_dir.rglob("*.html"))
    if not html_files:
        print(f"No HTML files found in '{input_dir}'")
        sys.exit(0)

    print(f"Found {len(html_files)} HTML file(s) in '{input_dir}'")

    total = 0
    for html_file in html_files:
        print(f"\nProcessing: {html_file}")
        total += process_html_file(html_file, access_token)

    print(f"\nDone. Total images downloaded/updated: {total}")


if __name__ == "__main__":
    main()

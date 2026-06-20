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
import logging
import re
import sys
import urllib.error
import urllib.request
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
    """Download a single image via urllib with Zoho auth headers.

    Returns True on success, False on failure.
    """
    req = urllib.request.Request(
        url,
        headers={
            "orgId": ORG_ID,
            "Authorization": f"Zoho-oauthtoken {access_token}",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req) as response:
            dest.write_bytes(response.read())
        return True
    except urllib.error.HTTPError as exc:
        logging.warning("Failed to download %s (HTTP %s %s)", url, exc.code, exc.reason)
    except urllib.error.URLError as exc:
        logging.warning("Failed to download %s: %s", url, exc.reason)
    except OSError as exc:
        logging.warning("Failed to save %s to %s: %s", url, dest, exc)
    return False


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
            logging.debug("Cached: %s", dest.name)
        else:
            logging.info("Downloading: %s", src_url)
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
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: INFO)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        logging.error("Input directory '%s' not found or is not a directory", input_dir)
        sys.exit(1)

    default_token = load_access_token()
    access_token = prompt_with_default("Enter access_token", default_token)

    if not access_token:
        logging.error("access_token is required")
        sys.exit(1)

    html_files = sorted(input_dir.rglob("*.html"))
    if not html_files:
        logging.info("No HTML files found in '%s'", input_dir)
        sys.exit(0)

    logging.info("Found %d HTML file(s) in '%s'", len(html_files), input_dir)

    total = 0
    for html_file in html_files:
        logging.info("Processing: %s", html_file)
        total += process_html_file(html_file, access_token)

    logging.info("Done. Total images downloaded/updated: %d", total)


if __name__ == "__main__":
    main()

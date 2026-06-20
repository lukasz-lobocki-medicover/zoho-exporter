"""Tests for download_imgs.py regex patterns and process_html_file."""
import html as html_mod
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import download_imgs
from download_imgs import (
    IMG_TAG_PATTERN,
    SRC_ATTR_PATTERN,
    ZOHO_BASE_URL,
    process_html_file,
    sidecar_path,
)

TST_HTML = Path(__file__).parent / "tst" / "test.html"

# A representative real-world Zoho inline-image tag (from problem statement)
REAL_ZOHO_TAG = (
    '<img border="0" width="83" height="49" style="width: 0.8611in; height: 0.5069in" '
    'src="/api/v1/threads/21172000056521412/inlineImages/'
    'edbsn47d33341b51ecadf99f4b7d7017384e3fe8d63c6cce37dc7506e5b1e02304773dfe'
    'eb4b8ff89edf6d3101ad713fc4fff309ae348f7fad637e8e6d3d64542e7bfc1a4d2244ee'
    '493a67d1f01a11ccb92ac?et=19f14b9511e&amp;ha=5b4dcf16f30e257c575be8061053'
    'ca2c3f30cf60b1ac27154f3b42c017b5e587&amp;f=1.png"/>'
)


# ---------------------------------------------------------------------------
# Pattern unit tests
# ---------------------------------------------------------------------------

class TestImgTagPattern:
    """IMG_TAG_PATTERN should find every <img> tag that has a src attribute."""

    def test_zoho_inline_image(self):
        assert IMG_TAG_PATTERN.search(REAL_ZOHO_TAG)

    def test_double_quoted_src_first(self):
        tag = '<img src="https://example.com/a.png" alt="x">'
        assert IMG_TAG_PATTERN.search(tag)

    def test_double_quoted_src_not_first(self):
        tag = '<img alt="x" src="https://example.com/b.jpg">'
        assert IMG_TAG_PATTERN.search(tag)

    def test_single_quoted_src(self):
        tag = "<img src='https://example.com/c.gif'>"
        assert IMG_TAG_PATTERN.search(tag)

    def test_unquoted_src(self):
        tag = '<img src=https://example.com/d.svg alt="x">'
        assert IMG_TAG_PATTERN.search(tag)

    def test_img_without_src_not_matched(self):
        tag = '<img alt="no src here">'
        assert not IMG_TAG_PATTERN.search(tag)


class TestSrcAttrPattern:
    """SRC_ATTR_PATTERN must extract the raw (still HTML-encoded) URL without quotes."""

    def test_zoho_relative_path_with_amp_entities(self):
        m = SRC_ATTR_PATTERN.search(REAL_ZOHO_TAG)
        assert m is not None
        raw = m.group("quoted") or m.group("unquoted") or ""
        # Raw value should still contain &amp; — decoding happens later
        assert raw.startswith("/api/v1/")
        assert "&amp;" in raw

    def test_double_quoted(self):
        tag = '<img src="https://example.com/a.png" alt="x">'
        m = SRC_ATTR_PATTERN.search(tag)
        assert m is not None
        url = m.group("quoted") or m.group("unquoted") or ""
        assert url == "https://example.com/a.png"

    def test_double_quoted_src_not_first(self):
        tag = '<img alt="x" src="https://example.com/b.jpg">'
        m = SRC_ATTR_PATTERN.search(tag)
        assert m is not None
        url = m.group("quoted") or m.group("unquoted") or ""
        assert url == "https://example.com/b.jpg"

    def test_single_quoted(self):
        tag = "<img src='https://example.com/c.gif'>"
        m = SRC_ATTR_PATTERN.search(tag)
        assert m is not None
        url = m.group("quoted") or m.group("unquoted") or ""
        assert url == "https://example.com/c.gif"

    def test_unquoted(self):
        tag = '<img src=https://example.com/d.svg alt="x">'
        m = SRC_ATTR_PATTERN.search(tag)
        assert m is not None
        url = m.group("quoted") or m.group("unquoted") or ""
        assert url == "https://example.com/d.svg"


class TestHtmlEntityDecoding:
    """&amp; entities in src must be decoded before the URL is used."""

    def test_amp_decoded_to_ampersand(self):
        src_raw = "/api/v1/threads/123/inlineImages/abc?et=x&amp;ha=y&amp;f=1.png"
        decoded = html_mod.unescape(src_raw)
        assert "&amp;" not in decoded
        assert "&" in decoded
        assert decoded == "/api/v1/threads/123/inlineImages/abc?et=x&ha=y&f=1.png"


class TestSidecarPath:
    """sidecar_path must derive extension from f= query param when path has none."""

    def test_extension_from_f_query_param(self, tmp_path):
        url = "https://desk.zoho.com/api/v1/threads/123/inlineImages/abc?et=x&ha=y&f=1.png"
        p = sidecar_path(url, tmp_path)
        assert p.suffix == ".png"

    def test_extension_from_f_query_param_gif(self, tmp_path):
        url = "https://desk.zoho.com/api/v1/threads/123/inlineImages/abc?et=x&f=image.gif"
        p = sidecar_path(url, tmp_path)
        assert p.suffix == ".gif"

    def test_extension_from_path_when_present(self, tmp_path):
        url = "https://example.com/photo.jpg"
        p = sidecar_path(url, tmp_path)
        assert p.suffix == ".jpg"

    def test_fallback_to_bin(self, tmp_path):
        url = "https://example.com/no-extension"
        p = sidecar_path(url, tmp_path)
        assert p.suffix == ".bin"


# ---------------------------------------------------------------------------
# Integration test using tst/test.html
# ---------------------------------------------------------------------------

def _fake_download(url: str, dest: Path, access_token: str) -> bool:
    """Simulate a successful download by writing an empty placeholder file."""
    dest.write_bytes(b"")
    return True


class TestProcessHtmlFile:
    """process_html_file must find and replace all 4 src attributes in tst/test.html."""

    def setup_method(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.html_file = self.tmpdir / "test.html"
        shutil.copy(TST_HTML, self.html_file)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_finds_and_replaces_four_images(self):
        with patch.object(download_imgs, "download_image", side_effect=_fake_download):
            replaced = process_html_file(self.html_file, access_token="dummy")

        assert replaced == 4, f"Expected 4 replacements, got {replaced}"

    def test_sidecar_files_created(self):
        with patch.object(download_imgs, "download_image", side_effect=_fake_download):
            process_html_file(self.html_file, access_token="dummy")

        images_dir = self.html_file.parent / "images"
        sidecar_files = list(images_dir.iterdir())
        assert len(sidecar_files) == 4, f"Expected 4 sidecar files, found {len(sidecar_files)}"

    def test_sidecar_extensions_derived_from_f_param(self):
        with patch.object(download_imgs, "download_image", side_effect=_fake_download):
            process_html_file(self.html_file, access_token="dummy")

        images_dir = self.html_file.parent / "images"
        suffixes = {f.suffix for f in images_dir.iterdir()}
        # tst/test.html has .png, .png, .gif, .jpg
        assert ".png" in suffixes
        assert ".gif" in suffixes
        assert ".jpg" in suffixes

    def test_src_attributes_rewritten(self):
        with patch.object(download_imgs, "download_image", side_effect=_fake_download):
            process_html_file(self.html_file, access_token="dummy")

        updated = self.html_file.read_text(encoding="utf-8")
        # No original /api/ paths should remain
        assert "/api/v1/" not in updated, "Zoho API paths should have been replaced"
        # All 4 replacements should point into images/
        assert updated.count('src="images/') == 4, \
            "Expected 4 src attributes pointing to images/ directory"

    def test_download_called_with_full_url(self):
        """download_image must receive the fully-qualified URL, not the relative path."""
        called_urls = []

        def recording_download(url: str, dest: Path, access_token: str) -> bool:
            called_urls.append(url)
            dest.write_bytes(b"")
            return True

        with patch.object(download_imgs, "download_image", side_effect=recording_download):
            process_html_file(self.html_file, access_token="dummy")

        assert len(called_urls) == 4
        for url in called_urls:
            assert url.startswith("https://"), f"Expected full URL, got: {url!r}"
            assert "&amp;" not in url, f"HTML entity not decoded in download URL: {url!r}"

    def test_custom_base_url(self):
        """--base-url override must be used when constructing the download URL."""
        called_urls = []

        def recording_download(url: str, dest: Path, access_token: str) -> bool:
            called_urls.append(url)
            dest.write_bytes(b"")
            return True

        with patch.object(download_imgs, "download_image", side_effect=recording_download):
            process_html_file(
                self.html_file, access_token="dummy", base_url="https://desk.zoho.eu"
            )

        for url in called_urls:
            assert url.startswith("https://desk.zoho.eu/"), \
                f"Expected EU base URL, got: {url!r}"

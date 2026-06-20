"""Playwright PDF/PNG export: valid output, browser reuse, crash recovery.

Opt-in: these launch real Chromium and keep a persistent sync-Playwright loop,
which doesn't mix with the rest of the (DB) suite. Run them on demand with
`RUN_BROWSER_TESTS=1 pytest tests/exporting/test_render_browser.py`."""
import os

import pytest

from apps.exporting import render_browser

# No django_db marker: these don't touch the DB, and the persistent Playwright
# sync loop conflicts with Django's DB teardown.

_HTML = "<!DOCTYPE html><html><body><h1>Hello Resume</h1><p>Body text.</p></body></html>"

needs_chromium = pytest.mark.skipif(
    os.environ.get("RUN_BROWSER_TESTS") != "1",
    reason="set RUN_BROWSER_TESTS=1 to run Playwright export tests")


@needs_chromium
def test_pdf_is_valid_and_browser_is_reused():
    pdf1 = render_browser.html_to_pdf(_HTML)
    b1 = render_browser._get_browser()
    pdf2 = render_browser.html_to_pdf(_HTML)
    b2 = render_browser._get_browser()
    assert pdf1[:5] == b"%PDF-"
    assert pdf2[:5] == b"%PDF-"
    assert b1 is b2  # same browser object reused (warm path)


@needs_chromium
def test_png_is_valid():
    png = render_browser.html_to_png(_HTML)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


@needs_chromium
def test_recovers_after_browser_death():
    render_browser.html_to_pdf(_HTML)          # warm up
    render_browser._get_browser().close()      # simulate a crash
    pdf = render_browser.html_to_pdf(_HTML)    # must recover, not poison the thread
    assert pdf[:5] == b"%PDF-"

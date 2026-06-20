"""PDF + PNG rendering via Playwright (headless Chromium).

Chromium produces a selectable text layer (critical for ATS) at full CSS
fidelity. Launching a browser per request is the slow part (~2-4s), so we keep
one Chromium alive PER THREAD and reuse it: the first export on a worker thread
warms it up, every later export just opens a page (~0.3-0.8s).

Playwright's sync objects are bound to the thread that created them, so
thread-local storage keeps each worker's browser on its own thread safely.
"""
from __future__ import annotations

import atexit
import logging
import threading
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from apps.templates_engine.render import render_resume_document

logger = logging.getLogger(__name__)

_local = threading.local()
_LAUNCH_ARGS = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
_all_playwrights: list = []  # for shutdown cleanup


@lru_cache(maxsize=1)
def _resume_css() -> str:
    path = Path(settings.BASE_DIR) / "static" / "css" / "resume.css"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _document_html(resume) -> str:
    return render_resume_document(resume, inline_css=_resume_css())


def _reset_local() -> None:
    """Tear down this thread's Playwright fully before relaunching. Starting a
    second sync_playwright on a thread whose loop is still alive is illegal and
    permanently poisons the thread — so always stop the old one first."""
    browser = getattr(_local, "browser", None)
    if browser is not None:
        try:
            browser.close()
        except Exception:  # noqa: BLE001
            pass
    pw = getattr(_local, "pw", None)
    if pw is not None:
        try:
            pw.stop()
        except Exception:  # noqa: BLE001
            pass
        if pw in _all_playwrights:
            _all_playwrights.remove(pw)
    _local.pw = None
    _local.browser = None


def _get_browser():
    """Return this thread's live Chromium, launching it once on first use. If the
    browser died but the Playwright loop is alive, relaunch just the browser."""
    pw = getattr(_local, "pw", None)
    browser = getattr(_local, "browser", None)
    if browser is not None and browser.is_connected():
        return browser
    if pw is not None:
        # Loop alive, browser dead -> relaunch only the browser (legal).
        try:
            _local.browser = pw.chromium.launch(args=_LAUNCH_ARGS)
            return _local.browser
        except Exception:  # noqa: BLE001 - loop is wedged; full reset below
            _reset_local()

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    _all_playwrights.append(pw)
    _local.pw = pw
    _local.browser = pw.chromium.launch(args=_LAUNCH_ARGS)
    return _local.browser


def _render(html: str, fn):
    """Open a fresh page on the reused browser, run fn(page), always close page.
    Recovers once if the persisted browser/loop died."""
    try:
        browser = _get_browser()
        page = browser.new_page()
    except Exception:  # noqa: BLE001 - rebuild from scratch once
        _reset_local()
        browser = _get_browser()
        page = browser.new_page()
    try:
        page.set_content(html, wait_until="load")
        # Give web fonts a brief chance to load for fidelity (best-effort).
        try:
            page.evaluate("document.fonts && document.fonts.ready")
        except Exception:  # noqa: BLE001
            pass
        return fn(page)
    finally:
        try:
            page.close()
        except Exception:  # noqa: BLE001
            pass


def html_to_pdf(html: str) -> bytes:
    return _render(html, lambda page: page.pdf(
        format="Letter", print_background=True,
        margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}))


def html_to_png(html: str) -> bytes:
    def shot(page):
        page.set_viewport_size({"width": 816, "height": 1056})
        return page.screenshot(full_page=True)
    return _render(html, shot)


def resume_to_pdf(resume) -> bytes:
    return html_to_pdf(_document_html(resume))


def resume_to_png(resume) -> bytes:
    return html_to_png(_document_html(resume))


@atexit.register
def _shutdown() -> None:
    for pw in _all_playwrights:
        try:
            pw.stop()
        except Exception:  # noqa: BLE001
            pass

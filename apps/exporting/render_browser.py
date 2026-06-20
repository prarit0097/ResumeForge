"""PDF + PNG rendering via Playwright (headless Chromium).

Chromium produces a selectable text layer (critical for ATS) at full CSS
fidelity. We launch a browser per request in dev; a long-lived browser/Celery
worker is the production optimization noted in the spec.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from django.conf import settings

from apps.templates_engine.render import render_resume_document


@lru_cache(maxsize=1)
def _resume_css() -> str:
    path = Path(settings.BASE_DIR) / "static" / "css" / "resume.css"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _document_html(resume) -> str:
    return render_resume_document(resume, inline_css=_resume_css())


def html_to_pdf(html: str) -> bytes:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        pdf = page.pdf(format="Letter", print_background=True,
                       margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()
        return pdf


def html_to_png(html: str) -> bytes:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=2)
        page.set_content(html, wait_until="networkidle")
        png = page.screenshot(full_page=True)
        browser.close()
        return png


def resume_to_pdf(resume) -> bytes:
    return html_to_pdf(_document_html(resume))


def resume_to_png(resume) -> bytes:
    return html_to_png(_document_html(resume))

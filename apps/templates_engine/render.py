"""Render a resume to HTML using its chosen template partial.

The same function powers the live preview (embedded in the editor) and the
export pipeline (wrapped in a full HTML document for Playwright). One render
path = no drift between what you see and what you download.
"""
from __future__ import annotations

from django.templatetags.static import static
from django.template.loader import render_to_string

from . import registry


def render_resume_partial(resume, template_id: str | None = None) -> str:
    """Return just the <article> resume HTML (for htmx preview swaps)."""
    meta = registry.get(template_id or resume.template_id)
    return render_to_string(meta.partial, {"resume": resume, "meta": meta})


def render_resume_document(resume, template_id: str | None = None, *,
                           inline_css: str | None = None) -> str:
    """Return a full standalone HTML document for PDF/PNG export.

    ``inline_css`` is the raw resume.css text embedded in a <style> block so
    the export browser needs no network/static resolution. When omitted we link
    the static path (only works if a server is serving it)."""
    meta = registry.get(template_id or resume.template_id)
    body = render_to_string(meta.partial, {"resume": resume, "meta": meta})
    if inline_css is not None:
        css_block = f"<style>{inline_css}\nbody{{margin:0;background:#fff;}}</style>"
    else:
        css_block = (
            f"<link rel='stylesheet' href='{static('css/resume.css')}'>"
            "<style>body{margin:0;background:#fff;}</style>"
        )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<link rel='preconnect' href='https://fonts.googleapis.com'>"
        "<link href='https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..900&family=Inter:wght@300..700&display=swap' rel='stylesheet'>"
        f"{css_block}"
        f"</head><body>{body}</body></html>"
    )

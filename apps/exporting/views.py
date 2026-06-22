"""Download endpoints: PDF, DOCX, PNG, TXT, and the download menu page."""
from __future__ import annotations

import logging
import re

from django.http import HttpResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit

from apps.templates_engine import registry
from core.access import get_resume_or_404

from . import docx_builder, plain_text

logger = logging.getLogger(__name__)


def _filename(resume, ext: str) -> str:
    base = resume.data.get("basics", {}).get("name") or resume.title or "resume"
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", base).strip("_") or "resume"
    return f"{slug}_resume.{ext}"


@ratelimit(key="ip", rate="60/m", block=True)
def download_menu(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    return render(request, "exporting/download_menu.html", {
        "resume": resume,
        "token": resume.edit_token,
        "plain_text": plain_text.as_plain_text(resume.data),
    })


@ratelimit(key="ip", rate="20/m", block=True)
def download_pdf(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    try:
        from .render_browser import resume_to_pdf
        pdf = resume_to_pdf(resume)
    except Exception:  # noqa: BLE001
        logger.exception("PDF export failed")
        return HttpResponse("PDF export is unavailable. Try DOCX, or contact support.",
                            status=503, content_type="text/plain")
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{_filename(resume, "pdf")}"'
    return resp


@ratelimit(key="ip", rate="20/m", block=True)
def download_png(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    try:
        from .render_browser import resume_to_png
        png = resume_to_png(resume)
    except Exception:  # noqa: BLE001
        logger.exception("PNG export failed")
        return HttpResponse("PNG export is unavailable.", status=503, content_type="text/plain")
    resp = HttpResponse(png, content_type="image/png")
    resp["Content-Disposition"] = f'attachment; filename="{_filename(resume, "png")}"'
    return resp


@ratelimit(key="ip", rate="30/m", block=True)
def download_docx(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    meta = registry.get(resume.template_id)
    accent = (meta.accent or "#4f46e5").lstrip("#")
    data = docx_builder.build_docx(resume.data, accent_hex=accent)
    resp = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    resp["Content-Disposition"] = f'attachment; filename="{_filename(resume, "docx")}"'
    return resp


@ratelimit(key="ip", rate="30/m", block=True)
def download_txt(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    resp = HttpResponse(plain_text.as_plain_text(resume.data), content_type="text/plain; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{_filename(resume, "txt")}"'
    return resp

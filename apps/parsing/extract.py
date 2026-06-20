"""Extract raw text from an uploaded resume (PDF or DOCX).

Validates type and size at the boundary. PDF via pdfplumber (MIT), DOCX via
python-docx (walking paragraphs AND tables, since resumes hide contact info in
tables). Returns plain text in reading order.
"""
from __future__ import annotations

import io

from django.conf import settings


class UploadError(ValueError):
    """Raised for invalid uploads (bad type, too big, unreadable)."""


def _validate(uploaded) -> None:
    size = getattr(uploaded, "size", None)
    if size is not None and size > settings.MAX_UPLOAD_SIZE:
        raise UploadError("File is too large (max 5 MB).")
    content_type = getattr(uploaded, "content_type", "")
    name = (getattr(uploaded, "name", "") or "").lower()
    if content_type not in settings.ALLOWED_UPLOAD_TYPES and not name.endswith((".pdf", ".docx")):
        raise UploadError("Please upload a PDF or Word (.docx) file.")


def _extract_pdf(raw: bytes) -> str:
    import pdfplumber

    out: list[str] = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            out.append(page.extract_text() or "")
    return "\n".join(out).strip()


def _extract_docx(raw: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(raw))
    parts: list[str] = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts).strip()


def extract_text(uploaded) -> str:
    """Validate and extract text from an uploaded file object."""
    _validate(uploaded)
    raw = uploaded.read()
    name = (getattr(uploaded, "name", "") or "").lower()
    is_pdf = name.endswith(".pdf") or getattr(uploaded, "content_type", "") == "application/pdf"
    try:
        text = _extract_pdf(raw) if is_pdf else _extract_docx(raw)
    except UploadError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise UploadError("Could not read that file. It may be scanned or corrupted.") from exc
    if not text.strip():
        raise UploadError("No text found. If this is a scanned image, please paste your details manually.")
    return text

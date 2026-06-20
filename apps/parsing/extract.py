"""Extract raw text from an uploaded resume (PDF or DOCX).

Validates type and size at the boundary. PDF via pdfplumber (MIT), DOCX via
python-docx (walking paragraphs AND tables, since resumes hide contact info in
tables). Returns plain text in reading order.
"""
from __future__ import annotations

import io
import re

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


# A page that yields fewer than this many characters is treated as "sparse"
# (often a multi-column or heavily designed layout that extract_text mangles),
# and we re-assemble its text from positioned words instead.
_SPARSE_PAGE_CHARS = 40


def _page_text_from_words(page) -> str:
    """Re-assemble page text from positioned words, grouped into rows.

    pdfplumber's default ``extract_text`` can return jumbled or sparse output on
    multi-column / designed resumes. Reading words sorted by vertical then
    horizontal position and grouping ones on the same line recovers a sane
    reading order without leaving PyMuPDF (AGPL)."""
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False) or []
    if not words:
        return ""
    words.sort(key=lambda w: (round(float(w["top"]) / 3.0), float(w["x0"])))
    lines: list[str] = []
    current: list[str] = []
    current_top: float | None = None
    for w in words:
        top = float(w["top"])
        if current_top is None or abs(top - current_top) <= 3.0:
            current.append(w["text"])
            current_top = top if current_top is None else current_top
        else:
            lines.append(" ".join(current))
            current = [w["text"]]
            current_top = top
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def _extract_pdf(raw: bytes) -> str:
    import pdfplumber

    out: list[str] = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            # Prefer layout-aware extraction (keeps columns/indentation closer to
            # the visual order); fall back to plain extraction if unsupported.
            try:
                text = page.extract_text(layout=True) or ""
            except Exception:  # noqa: BLE001 - older pdfplumber w/o layout kw
                text = page.extract_text() or ""
            # Sparse page: re-assemble from positioned words for a better result.
            if len(text.strip()) < _SPARSE_PAGE_CHARS:
                word_text = _page_text_from_words(page)
                if len(word_text.strip()) > len(text.strip()):
                    text = word_text
            out.append(text)
    # Collapse runs of intra-line spaces that layout=True introduces, but keep
    # line structure (headings/bullets) intact for the structurer.
    joined = "\n".join(out)
    joined = "\n".join(re.sub(r"[ \t]{2,}", " ", ln).rstrip() for ln in joined.splitlines())
    return joined.strip()


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

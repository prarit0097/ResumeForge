"""Tests for DOCX + plain-text export (PDF/PNG covered by a smoke test)."""
import io
import zipfile

from apps.exporting import docx_builder, plain_text


def test_docx_is_valid_zip_with_content(strong_resume_data):
    data = docx_builder.build_docx(strong_resume_data)
    assert data[:2] == b"PK"  # zip signature
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        assert "word/document.xml" in names
        document = zf.read("word/document.xml").decode("utf-8")
    assert "Jane Doe" in document
    assert "Python" in document
    # ATS-safe: no tables used for layout.
    assert "<w:tbl>" not in document


def test_plain_text_has_sections(strong_resume_data):
    text = plain_text.as_plain_text(strong_resume_data)
    assert "Jane Doe" in text
    assert "WORK EXPERIENCE" in text
    assert "SKILLS" in text

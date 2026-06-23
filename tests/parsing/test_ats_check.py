"""Instant landing ATS check: upload -> score + compare link."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from docx import Document

pytestmark = pytest.mark.django_db

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _docx():
    doc = Document()
    for line in ["Asha Verma", "Engineer", "asha@example.com | +91 99999 11111",
                 "Summary", "Builds reliable systems.", "Experience",
                 "Engineer - Acme  2021 - Present", "Built APIs", "Education", "MIT - BS 2016-2020"]:
        doc.add_paragraph(line)
    buf = io.BytesIO(); doc.save(buf)
    return buf.getvalue()


def test_ats_check_returns_score_and_compare_url(client):
    upload = SimpleUploadedFile("r.docx", _docx(), content_type=DOCX_MIME)
    resp = client.post("/ats-check/", {"resume": upload})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert 0 <= data["score"] <= 100
    assert "/compare/" in data["compareUrl"]
    assert isinstance(data["fixes"], list)


def test_ats_check_requires_a_file(client):
    resp = client.post("/ats-check/")
    assert resp.status_code == 400
    assert resp.json()["ok"] is False


def test_ats_check_rejects_get(client):
    assert client.get("/ats-check/").status_code == 405

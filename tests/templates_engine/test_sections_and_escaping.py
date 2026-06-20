"""Two-column completeness, DOCX completeness, and XSS escaping."""
import io
import zipfile

import pytest

from apps.exporting import docx_builder
from apps.resumes import schema
from apps.resumes.models import Resume
from apps.templates_engine.render import render_resume_partial

pytestmark = pytest.mark.django_db


def _full():
    d = schema.empty_resume()
    d["basics"]["name"] = "Test User"
    d["certifications"] = [{"name": "AWS Cert", "issuer": "Amazon"}]
    d["awards"] = [{"title": "Top Performer"}]
    d["languages"] = [{"language": "English", "fluency": "Native"}]
    d["custom"] = [{"heading": "Volunteering", "items": ["Food bank lead"]}]
    return d


def test_two_column_includes_all_sections():
    r = Resume.objects.create(session_key="s", data=_full())
    html = render_resume_partial(r, "sidebar-indigo")  # two-column template
    assert "AWS Cert" in html
    assert "Top Performer" in html
    assert "Food bank lead" in html


def test_docx_includes_all_sections():
    docx = docx_builder.build_docx(_full())
    xml = zipfile.ZipFile(io.BytesIO(docx)).read("word/document.xml").decode()
    assert "Top Performer" in xml      # award
    assert "English" in xml            # language
    assert "Food bank lead" in xml     # custom item
    assert "<w:tbl>" not in xml        # still ATS-safe (no tables)


def test_resume_data_is_html_escaped_in_output():
    d = schema.empty_resume()
    d["basics"]["name"] = "<script>alert(1)</script>"
    d["basics"]["summary"] = "<img src=x onerror=alert(2)>"
    r = Resume.objects.create(session_key="s", data=d)
    html = render_resume_partial(r, "classic")
    # Raw tags must be escaped to inert text (so no executable script/img tag).
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<img src=x" not in html  # the < is escaped -> harmless text only

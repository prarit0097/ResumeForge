"""Template registry + render tests."""
import pytest

from apps.resumes.models import Resume
from apps.templates_engine import registry
from apps.templates_engine.render import render_resume_document, render_resume_partial

pytestmark = pytest.mark.django_db


def test_registry_has_templates_and_categories():
    assert len(registry.all_templates()) >= 5
    assert "Simple" in registry.categories()


def test_get_unknown_falls_back_to_default():
    meta = registry.get("does-not-exist")
    assert meta.id == registry.DEFAULT_TEMPLATE_ID


def test_every_template_renders(strong_resume_data):
    resume = Resume.objects.create(session_key="s", data=strong_resume_data)
    for meta in registry.all_templates():
        html = render_resume_partial(resume, meta.id)
        assert "Jane Doe" in html, f"template {meta.id} failed to render name"


def test_document_inlines_css(strong_resume_data):
    resume = Resume.objects.create(session_key="s", data=strong_resume_data)
    html = render_resume_document(resume, inline_css=".rf-doc{color:red}")
    assert "<style>" in html
    assert "Jane Doe" in html

"""Catalog-wide guarantees: size and that every template renders cleanly."""
import pytest

from apps.resumes.models import Resume
from apps.templates_engine import registry
from apps.templates_engine.render import render_resume_partial

pytestmark = pytest.mark.django_db


def test_catalog_has_100_plus_templates():
    assert len(registry.all_templates()) >= 100


def test_every_template_renders_without_error(strong_resume_data):
    resume = Resume.objects.create(session_key="s", data=strong_resume_data)
    failures = []
    for meta in registry.all_templates():
        try:
            html = render_resume_partial(resume, meta.id)
            if "Jane Doe" not in html:
                failures.append((meta.id, "name missing"))
        except Exception as exc:  # noqa: BLE001
            failures.append((meta.id, str(exc)))
    assert not failures, f"templates failed: {failures[:5]}"


def test_ids_are_unique():
    ids = [t.id for t in registry.all_templates()]
    assert len(ids) == len(set(ids))


def test_has_both_ats_safe_and_creative():
    safe = [t for t in registry.all_templates() if t.ats_safe]
    creative = [t for t in registry.all_templates() if not t.ats_safe]
    assert safe and creative

"""Tests for resume access services (token security, sessions, variants)."""
import pytest

from apps.resumes import services

pytestmark = pytest.mark.django_db


def test_get_requires_correct_token():
    r = services.create_resume("sess-a")
    assert services.get_resume(r.id, r.edit_token) == r
    assert services.get_resume(r.id, "wrong-token") is None
    assert services.get_resume(r.id, "") is None


def test_get_unknown_id_returns_none():
    assert services.get_resume("00000000-0000-0000-0000-000000000000", "x") is None


def test_list_filters_by_session():
    a = services.create_resume("sess-a")
    services.create_resume("sess-b")
    ids = {r.id for r in services.list_session_resumes("sess-a")}
    assert a.id in ids
    assert len(ids) == 1


def test_update_validates_and_saves():
    r = services.create_resume("s")
    errors = services.update_resume_data(r, {"basics": {"name": "Jane"}})
    assert errors == []
    r.refresh_from_db()
    assert r.data["basics"]["name"] == "Jane"


def test_update_rejects_bad_data():
    r = services.create_resume("s")
    errors = services.update_resume_data(r, {"work": "oops"})
    assert errors


def test_create_variant_links_parent():
    r = services.create_resume("s", title="Base")
    services.update_resume_data(r, {"basics": {"name": "Jane"}})
    r.refresh_from_db()
    v = services.create_variant(r)
    assert v.parent_id == r.id
    assert v.data["basics"]["name"] == "Jane"

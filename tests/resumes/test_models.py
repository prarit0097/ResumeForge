"""Tests for resume model + schema."""
import pytest

from apps.resumes import schema
from apps.resumes.models import Resume

pytestmark = pytest.mark.django_db


def test_empty_resume_is_valid():
    assert schema.validate_resume_data(schema.empty_resume()) == []


def test_malformed_data_rejected():
    errors = schema.validate_resume_data({"work": "not a list"})
    assert errors


def test_non_dict_rejected():
    assert schema.validate_resume_data(["nope"])


def test_resume_gets_uuid_and_token():
    r = Resume.objects.create(session_key="s1")
    assert r.id is not None
    assert len(r.edit_token) > 20
    # tokens are unique per resume
    r2 = Resume.objects.create(session_key="s1")
    assert r.edit_token != r2.edit_token


def test_merge_is_immutable():
    base = schema.empty_resume()
    merged = schema.merge_into_resume(base, {"basics": {"name": "X"}})
    assert merged["basics"]["name"] == "X"
    assert base["basics"]["name"] == ""  # original untouched

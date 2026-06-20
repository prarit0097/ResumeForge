"""Tests for resume structuring (offline/mock path)."""
import pytest

from apps.ai import provider
from apps.parsing import structure
from apps.resumes import schema

RAW = """Jane Doe
Senior Software Engineer
jane@example.com | +1 555 123 4567

Experienced engineer who builds scalable systems."""


@pytest.fixture(autouse=True)
def _mock_ai(settings):
    settings.OPENROUTER_API_KEY = ""
    provider.reset_provider_cache()
    yield
    provider.reset_provider_cache()


def test_structure_returns_valid_schema():
    data = structure.to_resume_json(RAW)
    assert schema.validate_resume_data(data) == []


def test_structure_extracts_basic_contact():
    data = structure.to_resume_json(RAW)
    assert data["basics"]["name"] == "Jane Doe"
    assert data["basics"]["email"] == "jane@example.com"

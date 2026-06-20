"""Tests for the real-provider structuring path that we cannot hit live.

We verify (1) the structure prompt fully describes the target shape, and (2)
``structure.to_resume_json`` drives the provider with ``strict=False`` (plain
JSON-object mode) and fully merges a rich result. A stub provider stands in for
OpenRouter so no network call is made.
"""
import pytest

from apps.ai import prompts, provider
from apps.parsing import structure
from apps.resumes import schema


def test_structure_prompt_describes_full_shape():
    msgs = prompts.structure_messages("Some resume text")
    system = msgs[0]["content"]
    user = msgs[1]["content"]

    # The model must be told about every section we support.
    for key in ("basics", "work", "education", "skills", "projects",
                "certifications", "awards", "languages"):
        assert key in system
    # Key per-entry fields and rules are present.
    for token in ("highlights", "startDate", "endDate", "current",
                  "YYYY-MM", "name", "first non-empty line", "Never invent"):
        assert token in system
    # The raw text is forwarded to the user turn.
    assert "Some resume text" in user


class _StubProvider:
    """Captures how ``structured`` was called and returns a canned rich result."""

    def __init__(self, result):
        self.result = result
        self.calls = []

    def complete(self, *a, **k):  # pragma: no cover - unused here
        return ""

    def structured(self, messages, schema_arg, *, temperature=0.2, task=None,
                   context=None, strict=True):
        self.calls.append({"strict": strict, "task": task, "schema": schema_arg})
        return self.result


@pytest.fixture
def _no_real_key(settings):
    settings.OPENROUTER_API_KEY = ""
    provider.reset_provider_cache()
    yield
    provider.reset_provider_cache()


def test_to_resume_json_uses_json_object_mode_and_merges_all(monkeypatch, _no_real_key):
    rich = {
        "basics": {"name": "Lee Park", "email": "lee@x.com", "summary": "Hi."},
        "work": [{"company": "Acme", "position": "Eng",
                   "highlights": ["Did a thing"], "startDate": "2020-01"}],
        "education": [{"institution": "MIT", "area": "CS"}],
        "skills": [{"name": "Skills", "keywords": ["Go", "Rust"]}],
        "projects": [{"name": "Side", "description": "x", "highlights": []}],
    }
    stub = _StubProvider(rich)
    monkeypatch.setattr(structure, "get_provider", lambda: stub)

    data = structure.to_resume_json("raw text here")

    # Provider was invoked in non-strict (json_object) mode for structuring.
    assert stub.calls and stub.calls[0]["strict"] is False
    assert stub.calls[0]["task"] == "structure_resume"

    # Every returned section is fully merged and the doc is schema-valid.
    assert schema.validate_resume_data(data) == []
    assert data["basics"]["name"] == "Lee Park"
    assert data["work"][0]["company"] == "Acme"
    assert data["education"][0]["institution"] == "MIT"
    assert data["skills"][0]["keywords"] == ["Go", "Rust"]
    assert data["projects"][0]["name"] == "Side"


def test_to_resume_json_salvages_valid_sections_on_partial_invalid(monkeypatch, _no_real_key):
    # work[0].current has the wrong type -> the work section is invalid, but the
    # other sections must survive instead of the whole resume going empty.
    partial = {
        "basics": {"name": "Sam", "email": "s@x.com"},
        "work": [{"company": "Acme", "current": "yes"}],  # invalid boolean
        "skills": [{"name": "Skills", "keywords": ["Python"]}],
    }
    stub = _StubProvider(partial)
    monkeypatch.setattr(structure, "get_provider", lambda: stub)

    data = structure.to_resume_json("raw")

    assert schema.validate_resume_data(data) == []
    assert data["basics"]["name"] == "Sam"
    assert data["skills"][0]["keywords"] == ["Python"]
    # The malformed work section was dropped, not the rest of the resume.
    assert data["work"] == []

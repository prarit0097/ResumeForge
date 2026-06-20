"""Combined extract_and_enhance: one-call success path + fallback."""
import pytest

from apps.parsing import structure
from apps.resumes import schema

pytestmark = pytest.mark.django_db


class _StubProvider:
    """Returns a combined {original, enhanced} envelope in one call."""
    def __init__(self):
        self.calls = []

    def structured(self, messages, schema_, *, task=None, context=None, strict=True):
        self.calls.append({"task": task, "strict": strict})
        return {
            "original": {"basics": {"name": "Jane"}, "work": [{"company": "Acme", "highlights": ["x"]}]},
            "enhanced": {"basics": {"name": "Jane"}, "work": [{"company": "Acme", "highlights": ["Led X, +20%"]}]},
        }

    def complete(self, *a, **k):
        return ""


def test_combined_call_used_once_and_splits(monkeypatch):
    stub = _StubProvider()
    monkeypatch.setattr(structure, "get_provider", lambda: stub)
    original, enhanced = structure.extract_and_enhance("raw resume text")
    # Exactly one combined call, in json_object mode.
    assert len(stub.calls) == 1
    assert stub.calls[0]["task"] == "extract_and_enhance"
    assert stub.calls[0]["strict"] is False
    assert schema.validate_resume_data(original) == []
    assert schema.validate_resume_data(enhanced) == []
    assert original["work"][0]["company"] == "Acme"
    assert "Led X" in enhanced["work"][0]["highlights"][0]


def test_falls_back_when_no_envelope(monkeypatch):
    class Bad:
        def structured(self, *a, **k):
            return {"not": "useful"}
        def complete(self, *a, **k):
            return ""
    monkeypatch.setattr(structure, "get_provider", lambda: Bad())
    # Should fall back to to_resume_json + enhance and still return two valid resumes.
    original, enhanced = structure.extract_and_enhance("Jane Doe\njane@x.com\n")
    assert schema.validate_resume_data(original) == []
    assert schema.validate_resume_data(enhanced) == []

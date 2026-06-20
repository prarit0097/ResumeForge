"""Enhancement: no prompt-echo, never drops jobs, before/after summary."""
import pytest

from apps.ai import enhance, services
from apps.resumes import schema

pytestmark = pytest.mark.django_db


def _resume():
    d = schema.empty_resume()
    d["basics"].update({"name": "A", "summary": "led the team to ship features"})
    d["work"] = [
        {"position": "Eng", "company": "Acme", "highlights": ["led migration", "did backend"]},
        {"position": "Dev", "company": "Beta", "highlights": ["shipped api"]},
        {"position": "Intern", "company": "Gamma", "highlights": ["helped out"]},
    ]
    return d


def test_mock_improve_does_not_echo_prompt():
    out = services.improve_text("led the team to ship features", "bullet")
    # The prompt text must never leak into the output.
    assert "resume bullet" not in out.lower()
    assert "return only" not in out.lower()
    assert "led the team to ship features" in out.lower()


def test_enhance_preserves_all_jobs():
    original = _resume()
    enhanced = enhance.enhance_resume_data(original)
    assert len(enhanced["work"]) == 3  # never drops jobs
    companies = {w["company"] for w in enhanced["work"]}
    assert companies == {"Acme", "Beta", "Gamma"}


def test_dropped_entries_detector():
    a = {"work": [1, 2, 3], "education": [1]}
    fewer = {"work": [1], "education": [1]}
    same = {"work": [1, 2, 3], "education": [1]}
    assert enhance._dropped_entries(a, fewer) is True
    assert enhance._dropped_entries(a, same) is False


def test_summary_non_positive_delta_phrasing():
    original = _resume()
    result = enhance.summarize_improvements(original, original, 80, 80)
    # No "X-point jump" wording when the score didn't improve.
    assert not any("jump" in b for b in result["benefits"])

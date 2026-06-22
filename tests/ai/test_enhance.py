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


def test_ensure_ats_polish_adds_skills_and_lifts_score():
    from apps.ai.enhance import ensure_ats_polish
    from apps.ats import compatibility
    from apps.templates_engine import registry

    d = schema.empty_resume()
    d["basics"].update({
        "name": "Prarit", "email": "p@x.com", "phone": "123", "location": "R",
        "label": "Sales Manager | Revenue Growth Expert | Business Development Specialist",
        "summary": "Seasoned sales leader with over five years of experience in sales leadership and operational management, consistently driving revenue growth and strategic planning across teams.",
    })
    d["work"] = [{"position": "Sales Manager", "company": "J", "current": True,
                  "startDate": "2021-10", "highlights": ["Directed a team of 350.", "Increased revenue by 30%."]}]
    d["education"] = [{"institution": "RTU", "studyType": "B.Tech"}]

    before = compatibility.score_resume(d, registry.get("classic"))["score"]
    polished = ensure_ats_polish(d)
    after = compatibility.score_resume(polished, registry.get("classic"))["score"]

    assert polished["skills"] and len(polished["skills"][0]["keywords"]) >= 6
    # No junk leading filler words in derived skills.
    for kw in polished["skills"][0]["keywords"]:
        assert kw.split()[0].lower() not in {"in", "and", "the", "of", "driving"}
    assert after > before and after >= 95


def test_sanitizer_strips_llm_artifacts():
    from apps.ai.enhance import _clean_text
    assert _clean_text('"Directed 350+ team members."') == "Directed 350+ team members."
    assert _clean_text("Optimized ops. *(Note: add metrics like \"by 20%\".)*") == "Optimized ops."
    assert _clean_text('"Did X." (Note: you could also say Y.)') == "Did X."
    assert _clean_text("Plain bullet with no artifacts.") == "Plain bullet with no artifacts."


def test_ensure_ats_polish_sanitizes_bullets():
    from apps.ai.enhance import ensure_ats_polish
    d = schema.empty_resume()
    d["basics"]["summary"] = '"A summary in quotes."'
    d["work"] = [{"position": "Eng", "company": "C", "highlights": [
        'Built systems. *(Note: add a metric here.)*', '"Led the team."']}]
    out = ensure_ats_polish(d)
    assert out["basics"]["summary"] == "A summary in quotes."
    assert out["work"][0]["highlights"][0] == "Built systems."
    assert out["work"][0]["highlights"][1] == "Led the team."


def test_ensure_ats_polish_leaves_rich_skills_untouched():
    from apps.ai.enhance import ensure_ats_polish
    d = schema.empty_resume()
    d["skills"] = [{"name": "X", "keywords": ["a", "b", "c", "d", "e", "f", "g"]}]
    assert ensure_ats_polish(d)["skills"] == d["skills"]


def test_summary_non_positive_delta_phrasing():
    original = _resume()
    result = enhance.summarize_improvements(original, original, 80, 80)
    # No "X-point jump" wording when the score didn't improve.
    assert not any("jump" in b for b in result["benefits"])

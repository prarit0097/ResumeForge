"""Unit tests for the ATS compatibility scorer."""
from apps.ats import compatibility
from apps.resumes import schema


class _Meta:
    def __init__(self, ats_safe=True):
        self.ats_safe = ats_safe


def test_empty_resume_scores_low_with_fixes():
    result = compatibility.score_resume(schema.empty_resume(), _Meta())
    assert result["score"] < 40
    # Every failing dimension carries an actionable fix string.
    assert all(d["fix"] for d in result["dimensions"])
    assert any(d["key"] == "contact" and d["status"] == "fail" for d in result["dimensions"])


def test_strong_resume_scores_high(strong_resume_data):
    result = compatibility.score_resume(strong_resume_data, _Meta())
    assert result["score"] >= 80
    assert result["grade"] in {"Good", "Excellent"}


def test_missing_contact_is_flagged(strong_resume_data):
    strong_resume_data["basics"]["email"] = ""
    result = compatibility.score_resume(strong_resume_data, _Meta())
    contact = next(d for d in result["dimensions"] if d["key"] == "contact")
    assert contact["status"] == "fail"
    assert "email" in contact["fix"].lower()


def test_unquantified_bullets_flagged(strong_resume_data):
    strong_resume_data["work"][0]["highlights"] = ["Worked on stuff", "Did things"]
    result = compatibility.score_resume(strong_resume_data, _Meta())
    quant = next(d for d in result["dimensions"] if d["key"] == "quantified")
    assert quant["status"] == "warn"


def test_two_column_template_lowers_parse_safety(strong_resume_data):
    safe = compatibility.score_resume(strong_resume_data, _Meta(ats_safe=True))
    risky = compatibility.score_resume(strong_resume_data, _Meta(ats_safe=False))
    assert risky["score"] < safe["score"]
    parse = next(d for d in risky["dimensions"] if d["key"] == "parse")
    assert parse["status"] == "warn"

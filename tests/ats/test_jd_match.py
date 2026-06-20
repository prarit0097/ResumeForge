"""Unit tests for the JD-match scorer and keyword extraction."""
from apps.ats import jd_match, keywords

JD = (
    "We are hiring a Software Engineer. You will build services in Python and "
    "JavaScript, deploy with Docker and Kubernetes on AWS, and work with SQL "
    "databases. Strong communication and teamwork required. Bachelor degree."
)


def test_extract_finds_hard_skills_and_title():
    req = keywords.extract(JD)
    assert "python" in req["hard"]
    assert "kubernetes" in req["hard"]
    assert req["title"]  # a title was detected
    assert req["education"] == "degree"


def test_no_jd_returns_zero_with_prompt():
    result = jd_match.score({"basics": {}}, "")
    assert result["score"] == 0
    assert result["warnings"]


def test_missing_skills_listed(strong_resume_data):
    # strong_resume_data has Python/JS/Go/SQL/AWS/Docker/Kubernetes already
    result = jd_match.score(strong_resume_data, JD)
    assert result["score"] >= 70
    assert "python" in [m.lower() for m in result["matched"]]


def test_weak_resume_misses_skills():
    data = {"basics": {"summary": "I like computers"}, "work": [], "skills": []}
    result = jd_match.score(data, JD)
    assert result["score"] < 50
    assert "python" in result["missing"]


def test_high_match_warns_about_over_optimization(strong_resume_data):
    # Force a deterministic near-perfect match so the assertion is never vacuous.
    strong_resume_data["skills"].append(
        {"name": "All", "keywords": ["communication", "teamwork"]})
    strong_resume_data["basics"]["summary"] += (
        " Bachelor degree. Software Engineer with Python, JavaScript, Docker, "
        "Kubernetes, AWS, SQL, communication and teamwork.")
    result = jd_match.score(strong_resume_data, JD)
    assert result["score"] >= 88, f"expected near-perfect match, got {result['score']}"
    assert any("over-optim" in w.lower() for w in result["warnings"])

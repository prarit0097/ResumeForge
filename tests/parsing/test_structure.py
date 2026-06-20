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


# A realistic multi-section, single-column resume. The mock structurer should
# recover contact, summary, two jobs with bullets, education and skills.
FULL_RAW = """Asha Verma
Senior Backend Engineer
asha.verma@example.com | +91 98765 43210 | Bangalore

Summary
Backend engineer with 7 years building high-throughput payment systems and
leading small teams.

Experience
Senior Backend Engineer - PayFlow  Jan 2021 - Present
- Cut p99 API latency by 45% by redesigning the ledger service.
- Led a team of 5 engineers to ship a new payouts platform.
Backend Engineer - Shopline  Jun 2018 - Dec 2020
- Built an event pipeline processing 2M events per day.
- Reduced infra costs by 30% through autoscaling.

Education
TU Munich - M.Sc. Computer Science  2016 - 2018
University of Pune - B.E. Information Technology  2012 - 2016

Skills
Python, Django, PostgreSQL, AWS, Kafka, Docker
"""


def test_structure_extracts_all_sections_from_full_resume():
    data = structure.to_resume_json(FULL_RAW)

    # Always schema-valid.
    assert schema.validate_resume_data(data) == []

    # Contact / basics
    b = data["basics"]
    assert b["name"] == "Asha Verma"
    assert b["email"] == "asha.verma@example.com"
    assert "98765" in b["phone"]
    assert "payment systems" in b["summary"].lower()

    # Two work entries, each with company, position and highlights.
    assert len(data["work"]) == 2
    companies = {w["company"] for w in data["work"]}
    assert {"PayFlow", "Shopline"} == companies
    payflow = next(w for w in data["work"] if w["company"] == "PayFlow")
    assert payflow["position"] == "Senior Backend Engineer"
    assert payflow.get("current") is True
    assert payflow["startDate"] == "2021-01"
    assert any("latency" in h for h in payflow["highlights"])
    assert len(payflow["highlights"]) == 2

    # Education (two institutions).
    institutions = {e["institution"] for e in data["education"]}
    assert {"TU Munich", "University of Pune"} == institutions

    # Skills flattened into keywords.
    assert data["skills"]
    keywords = data["skills"][0]["keywords"]
    assert "Python" in keywords and "Kafka" in keywords


def test_structure_full_resume_never_invents_extra_sections():
    data = structure.to_resume_json(FULL_RAW)
    # No projects/certifications in the source -> stay empty (never invent).
    assert data["projects"] == []
    assert data["certifications"] == []

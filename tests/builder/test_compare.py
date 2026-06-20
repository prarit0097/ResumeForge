"""Before/after enhancement: service diff + compare page + keep-original."""
import pytest

from apps.ai import enhance
from apps.resumes import schema, services

pytestmark = pytest.mark.django_db


def _raw_resume():
    d = schema.empty_resume()
    d["basics"].update({"name": "Asha Verma", "email": "asha@example.com",
                        "phone": "123", "summary": "i worked on payments"})
    d["work"] = [{"position": "Engineer", "company": "Acme",
                  "highlights": ["worked on the payments system", "did backend stuff"]}]
    d["skills"] = [{"name": "Lang", "keywords": ["Python"]}]
    return d


def test_enhance_returns_valid_resume():
    enhanced = enhance.enhance_resume_data(_raw_resume())
    assert schema.validate_resume_data(enhanced) == []
    # Facts preserved — never invents/removes the job.
    assert enhanced["work"][0]["company"] == "Acme"
    assert enhanced["basics"]["name"] == "Asha Verma"


def test_summary_reports_improvements_and_benefits():
    original = _raw_resume()
    enhanced = enhance.enhance_resume_data(original)
    result = enhance.summarize_improvements(original, enhanced, 55, 82)
    assert result["delta"] == 27
    assert result["improvements"]
    assert any("ATS" in b for b in result["benefits"])


def test_compare_page_renders(client):
    original = _raw_resume()
    enhanced = enhance.enhance_resume_data(original)
    r = services.create_resume("s", data=enhanced, original_data=original)
    resp = client.get(f"/r/{r.id}/compare/?t={r.edit_token}")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Here's what we improved" in body
    assert "Before" in body and "After" in body


def test_keep_original_restores_snapshot(client):
    original = _raw_resume()
    enhanced = enhance.enhance_resume_data(original)
    r = services.create_resume("s", data=enhanced, original_data=original)
    resp = client.post(f"/r/{r.id}/use-original/?t={r.edit_token}")
    assert resp.status_code == 302
    r.refresh_from_db()
    assert r.data["basics"]["summary"] == original["basics"]["summary"]

"""Tailor-to-JD endpoint + score endpoint robustness."""
import json

import pytest

from apps.resumes import services

pytestmark = pytest.mark.django_db


def _resume_with_jd(jd="Python Django engineer with AWS"):
    from apps.resumes import schema
    d = schema.empty_resume()
    d["basics"].update({"name": "A", "summary": "i build things"})
    d["work"] = [{"position": "Eng", "company": "Acme", "highlights": ["did work"]}]
    return services.create_resume("s", data=d, job_description=jd)


def test_tailor_without_jd_returns_400(client):
    r = services.create_resume("s")  # no JD
    resp = client.post(f"/ats/r/{r.id}/tailor/?t={r.edit_token}",
                       data="{}", content_type="application/json")
    assert resp.status_code == 400
    assert "job description" in resp.json()["error"].lower()


def test_tailor_rewrites_and_persists(client):
    r = _resume_with_jd()
    resp = client.post(f"/ats/r/{r.id}/tailor/?t={r.edit_token}",
                       data="{}", content_type="application/json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "ats" in body and "match" in body
    r.refresh_from_db()
    # The mock rewrite injects a metric into the bullet.
    assert any(ch.isdigit() for ch in r.data["work"][0]["highlights"][0])


def test_score_endpoint_falls_back_on_malformed_data(client):
    r = _resume_with_jd()
    resp = client.post(f"/ats/r/{r.id}/score/?t={r.edit_token}",
                       data=json.dumps({"data": {"work": "not-a-list"}, "jd": ""}),
                       content_type="application/json")
    assert resp.status_code == 200  # falls back to saved data, never crashes
    assert "ats" in resp.json()

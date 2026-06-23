"""One-click 'polish' endpoint: enhances the whole resume and saves it."""
import pytest

from apps.resumes import schema, services

pytestmark = pytest.mark.django_db


def _resume():
    d = schema.empty_resume()
    d["basics"].update({
        "name": "Asha", "email": "a@x.com",
        "label": "Backend Engineer | Python Developer",
        "summary": "Backend engineer with Python and Django building scalable APIs.",
    })
    d["work"] = [{"position": "Engineer", "company": "Acme",
                  "highlights": ["worked on the Python payments service with Django and AWS"]}]
    return services.create_resume("s", data=d)


def test_polish_improves_and_persists(client):
    r = _resume()
    resp = client.post(f"/ai/r/{r.id}/polish/?t={r.edit_token}",
                       data="{}", content_type="application/json")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    r.refresh_from_db()
    # Polish keeps real facts (company/name) and adds a skills section.
    assert r.data["work"][0]["company"] == "Acme"
    assert r.data["basics"]["name"] == "Asha"
    assert r.data.get("skills")  # skills surfaced by ensure_ats_polish


def test_polish_requires_valid_token(client):
    r = _resume()
    resp = client.post(f"/ai/r/{r.id}/polish/?t=wrong",
                       data="{}", content_type="application/json")
    assert resp.status_code == 404

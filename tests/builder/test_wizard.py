"""Wizard intake (Step 1) persists data and routes to the template gallery."""
import pytest

from apps.resumes import services

pytestmark = pytest.mark.django_db


def test_wizard_post_persists_and_redirects_to_gallery(client):
    r = services.create_resume("s")
    resp = client.post(f"/r/{r.id}/wizard/?t={r.edit_token}", data={
        "name": "Prarit Sidana", "target_role": "Sales Manager", "experience_level": "mid",
    })
    assert resp.status_code == 302
    assert "/templates/" in resp["Location"]
    r.refresh_from_db()
    assert r.data["basics"]["name"] == "Prarit Sidana"
    assert r.data["basics"]["label"] == "Sales Manager"
    assert r.target_role == "Sales Manager"
    assert r.experience_level == "mid"


def test_wizard_rejects_invalid_experience_level(client):
    r = services.create_resume("s")
    client.post(f"/r/{r.id}/wizard/?t={r.edit_token}", data={
        "name": "X", "target_role": "Dev", "experience_level": "not-a-level",
    })
    r.refresh_from_db()
    assert r.experience_level == ""  # invalid choice not saved

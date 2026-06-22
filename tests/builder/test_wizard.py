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


def test_wizard_prefills_saved_level_so_resubmit_keeps_it(client):
    r = services.create_resume("s")
    # First submit sets senior.
    client.post(f"/r/{r.id}/wizard/?t={r.edit_token}", data={
        "name": "X", "target_role": "Dev", "experience_level": "senior"})
    # Re-open the wizard: the saved level must be pre-checked (not reset to entry).
    page = client.get(f"/r/{r.id}/wizard/?t={r.edit_token}").content.decode()
    senior_idx = page.find('value="senior"')
    assert senior_idx != -1
    # The 'senior' radio carries `checked`; the first (entry) radio does not.
    assert "checked" in page[senior_idx:senior_idx + 120]
    entry_idx = page.find('value="entry"')
    assert "checked" not in page[entry_idx:entry_idx + 120]


def test_wizard_rejects_invalid_experience_level(client):
    r = services.create_resume("s")
    client.post(f"/r/{r.id}/wizard/?t={r.edit_token}", data={
        "name": "X", "target_role": "Dev", "experience_level": "not-a-level",
    })
    r.refresh_from_db()
    assert r.experience_level == ""  # invalid choice not saved

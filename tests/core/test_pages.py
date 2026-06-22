"""Render smoke tests for every user-facing page (catches template errors)."""
import pytest

pytestmark = pytest.mark.django_db


def _new(client):
    loc = client.post("/new/")["Location"]
    rid = loc.split("/r/")[1].split("/")[0]
    token = loc.split("t=")[1]
    return rid, token


def test_wizard_renders(client):
    rid, token = _new(client)
    resp = client.get(f"/r/{rid}/wizard/?t={token}")
    assert resp.status_code == 200
    assert b"Target role" in resp.content


def test_editor_renders(client):
    rid, token = _new(client)
    resp = client.get(f"/r/{rid}/edit/?t={token}")
    assert resp.status_code == 200
    assert b"Live preview" in resp.content


def test_gallery_renders_all_templates(client):
    rid, token = _new(client)
    resp = client.get(f"/r/{rid}/templates/?t={token}")
    assert resp.status_code == 200
    assert b"Choose a template" in resp.content


def test_download_menu_renders(client):
    rid, token = _new(client)
    resp = client.get(f"/r/{rid}/download/?t={token}")
    assert resp.status_code == 200
    assert b"Download your resume" in resp.content


def test_cover_letter_page_renders(client):
    rid, token = _new(client)
    resp = client.get(f"/r/{rid}/cover-letter/?t={token}")
    assert resp.status_code == 200
    assert b"Cover letter" in resp.content


def test_drafts_page_renders(client):
    client.post("/new/")  # create a draft on this session
    resp = client.get("/drafts/")
    assert resp.status_code == 200


def test_privacy_headers_present(client):
    resp = client.get("/")
    assert resp["X-Robots-Tag"].startswith("noindex")
    # same-origin (not no-referrer): protects the token URL from external sites
    # without breaking same-origin form POSTs (which no-referrer does via Origin: null).
    assert resp["Referrer-Policy"] == "same-origin"

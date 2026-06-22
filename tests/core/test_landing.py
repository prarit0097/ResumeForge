"""Smoke tests for key pages and the build/enhance flow."""
import pytest

pytestmark = pytest.mark.django_db


def test_landing_has_both_doors(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Build a new resume" in body
    assert "Enhance an existing" in body


def test_start_new_is_post_only(client):
    # GET must NOT create a draft (prefetch-safe); only POST does.
    assert client.get("/new/").status_code == 405
    resp = client.post("/new/")
    assert resp.status_code == 302
    assert "/wizard/" in resp["Location"]


def test_editor_requires_valid_token(client):
    # Start a draft, capture its edit URL, then verify a bad token 404s.
    start = client.post("/new/")
    wizard_url = start["Location"]
    resume_id = wizard_url.split("/r/")[1].split("/")[0]
    ok = client.get(f"/r/{resume_id}/edit/?t=" + wizard_url.split("t=")[1])
    assert ok.status_code == 200
    bad = client.get(f"/r/{resume_id}/edit/?t=wrong")
    assert bad.status_code == 404


def test_upload_page_renders(client):
    resp = client.get("/enhance/")
    assert resp.status_code == 200
    assert "Enhance an existing resume" in resp.content.decode()

"""End-to-end flow: build -> autosave -> score -> switch template -> export."""
import json

import pytest

pytestmark = pytest.mark.django_db


def _new_resume(client):
    start = client.post("/new/")
    loc = start["Location"]
    rid = loc.split("/r/")[1].split("/")[0]
    token = loc.split("t=")[1]
    return rid, token


def test_full_build_and_export_flow(client):
    rid, token = _new_resume(client)

    # Autosave some content.
    payload = {"data": {"basics": {"name": "Jane Doe", "email": "jane@example.com",
                                   "phone": "+1 555 111 2222", "summary": "x"}}}
    resp = client.post(f"/r/{rid}/autosave/?t={token}", data=json.dumps(payload),
                       content_type="application/json")
    assert resp.status_code == 200
    assert b"Jane Doe" in resp.content

    # Live score.
    resp = client.post(f"/ats/r/{rid}/score/?t={token}",
                       data=json.dumps({"data": payload["data"], "jd": ""}),
                       content_type="application/json")
    assert resp.status_code == 200
    assert "ats" in resp.json()

    # Switch template via ajax.
    resp = client.post(f"/r/{rid}/set-template/?t={token}", data={"template_id": "modern"},
                       HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert resp.status_code == 200

    # DOCX + TXT export.
    docx = client.get(f"/r/{rid}/download/docx/?t={token}")
    assert docx.status_code == 200
    assert docx["Content-Type"].startswith("application/vnd.openxml")
    txt = client.get(f"/r/{rid}/download/txt/?t={token}")
    assert txt.status_code == 200
    assert b"Jane Doe" in txt.content


def test_autosave_rejects_invalid(client):
    rid, token = _new_resume(client)
    resp = client.post(f"/r/{rid}/autosave/?t={token}",
                       data=json.dumps({"data": {"work": "nope"}}),
                       content_type="application/json")
    assert resp.status_code == 400


def test_ai_improve_endpoint(client):
    rid, token = _new_resume(client)
    resp = client.post(f"/ai/r/{rid}/improve/?t={token}",
                       data=json.dumps({"text": "worked on payments", "kind": "bullet"}),
                       content_type="application/json")
    assert resp.status_code == 200
    assert resp.json()["text"]

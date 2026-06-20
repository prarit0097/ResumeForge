"""Cover letter generate/save behavior."""
import pytest

from apps.resumes import services
from apps.resumes.models import CoverLetter

pytestmark = pytest.mark.django_db


def _resume():
    from apps.resumes import schema
    d = schema.empty_resume()
    d["basics"]["name"] = "Jane"
    return services.create_resume("s", data=d, target_role="Designer")


def test_generate_creates_one_letter(client):
    r = _resume()
    resp = client.post(f"/r/{r.id}/cover-letter/generate/?t={r.edit_token}")
    assert resp.status_code == 302
    assert r.cover_letters.count() == 1
    assert r.cover_letters.first().body


def test_regenerate_updates_not_duplicates(client):
    r = _resume()
    client.post(f"/r/{r.id}/cover-letter/generate/?t={r.edit_token}")
    client.post(f"/r/{r.id}/cover-letter/generate/?t={r.edit_token}")
    assert r.cover_letters.count() == 1  # updated, not duplicated


def test_save_truncates_long_body(client):
    r = _resume()
    resp = client.post(f"/r/{r.id}/cover-letter/save/?t={r.edit_token}",
                       data={"body": "x" * 30000})
    assert resp.status_code == 302
    letter = CoverLetter.objects.get(resume=r)
    assert len(letter.body) == 20000


def test_save_requires_valid_token(client):
    r = _resume()
    resp = client.post(f"/r/{r.id}/cover-letter/save/?t=wrong", data={"body": "hi"})
    assert resp.status_code == 404

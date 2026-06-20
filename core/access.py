"""Resume access guard for views: resolves the secret edit_token from the
query string (?t=) or the per-resume cookie, and 404s on mismatch."""
from __future__ import annotations

from django.conf import settings
from django.http import Http404

from apps.resumes import services


def cookie_name(resume_id) -> str:
    return f"rf_t_{resume_id}"


def resume_token(request, resume_id) -> str:
    return request.GET.get("t") or request.COOKIES.get(cookie_name(resume_id), "")


def get_resume_or_404(request, resume_id):
    resume = services.get_resume(resume_id, resume_token(request, resume_id))
    if resume is None:
        raise Http404("Resume not found or link is invalid.")
    return resume


def edit_url(resume) -> str:
    return f"/r/{resume.id}/edit/?t={resume.edit_token}"


def set_token_cookie(response, resume):
    """Persist the resume's edit token in an HttpOnly (and Secure in prod) cookie
    for same-browser convenience."""
    response.set_cookie(
        cookie_name(resume.id), resume.edit_token, max_age=60 * 60 * 24 * 90,
        samesite="Lax", httponly=True, secure=not settings.DEBUG,
    )
    return response

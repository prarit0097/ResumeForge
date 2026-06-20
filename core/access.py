"""Resume access guard for views: resolves the secret edit_token from the
query string (?t=) or the per-resume cookie, and 404s on mismatch."""
from __future__ import annotations

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

"""Upload an existing resume -> parse -> structured draft -> editor."""
from __future__ import annotations

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from apps.ai import enhance
from apps.resumes import services
from core.access import cookie_name
from core.sessions import ensure_session_key

from . import extract, structure


@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def upload(request):
    if request.method == "GET":
        return render(request, "parsing/upload.html")

    uploaded = request.FILES.get("resume")
    if not uploaded:
        return render(request, "parsing/upload.html", {"error": "Please choose a file to upload."})

    try:
        raw_text = extract.extract_text(uploaded)
    except extract.UploadError as exc:
        return render(request, "parsing/upload.html", {"error": str(exc)})

    # Parse the upload into the "before" snapshot, then produce the enhanced one.
    original = structure.to_resume_json(raw_text)
    enhanced = enhance.enhance_resume_data(original)

    session_key = ensure_session_key(request)
    resume = services.create_resume(
        session_key, title="Enhanced resume", data=enhanced, original_data=original,
    )
    # Show the before/after comparison first (the value moment), not the editor.
    response = redirect(reverse("builder:compare", args=[resume.id]) + f"?t={resume.edit_token}")
    response.set_cookie(
        cookie_name(resume.id), resume.edit_token, max_age=60 * 60 * 24 * 90,
        samesite="Lax", httponly=True,
    )
    return response

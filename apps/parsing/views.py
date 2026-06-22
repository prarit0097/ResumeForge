"""Upload an existing resume -> parse -> structured draft -> editor."""
from __future__ import annotations

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from apps.resumes import services
from core.access import set_token_cookie
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

    # Optional target job description -> tailor the enhanced resume to it.
    jd = (request.POST.get("jd") or "").strip()[:8000]

    # One LLM round-trip yields both the faithful "before" and the enhanced
    # "after" (much faster than structuring then enhancing separately).
    original, enhanced = structure.extract_and_enhance(raw_text, jd or None)

    session_key = ensure_session_key(request)
    resume = services.create_resume(
        session_key, title="Enhanced resume", data=enhanced, original_data=original,
        job_description=jd,
    )
    # Show the before/after comparison first (the value moment), not the editor.
    response = redirect(reverse("builder:compare", args=[resume.id]) + f"?t={resume.edit_token}")
    return set_token_cookie(response, resume)

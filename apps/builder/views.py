"""Builder entry points: start a new draft, list device drafts, and the editor."""
from __future__ import annotations

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from apps.resumes import services
from apps.templates_engine import registry
from core.access import cookie_name, edit_url, get_resume_or_404
from core.sessions import ensure_session_key


def start_new(request):
    """Create a fresh draft for this device and send the user to the wizard."""
    session_key = ensure_session_key(request)
    resume = services.create_resume(session_key)
    response = redirect(reverse("builder:wizard", args=[resume.id]) + f"?t={resume.edit_token}")
    response.set_cookie(
        cookie_name(resume.id), resume.edit_token, max_age=60 * 60 * 24 * 90,
        samesite="Lax", httponly=True,
    )
    return response


@require_POST
def create_variant(request, resume_id):
    """Make a tailored copy of a resume (for a specific job) and open it."""
    resume = get_resume_or_404(request, resume_id)
    variant = services.create_variant(resume)
    return redirect(edit_url(variant))


def my_drafts(request):
    session_key = ensure_session_key(request)
    resumes = services.list_session_resumes(session_key).filter(parent__isnull=True)
    return render(request, "builder/my_drafts.html", {"resumes": resumes})


EDITOR_TABS = [
    ("basics", "Basics"),
    ("work", "Experience"),
    ("education", "Education"),
    ("skills", "Skills"),
    ("more", "More"),
]


@ensure_csrf_cookie
def editor(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    context = {
        "resume": resume,
        "template": registry.get(resume.template_id),
        "token": resume.edit_token,
        "edit_url": edit_url(resume),
        "tabs": EDITOR_TABS,
    }
    return render(request, "builder/editor.html", context)


def wizard(request, resume_id):
    """Light intake: name, target role, experience level. Then to the editor."""
    resume = get_resume_or_404(request, resume_id)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()[:120]
        role = request.POST.get("target_role", "").strip()[:200]
        level = request.POST.get("experience_level", "").strip()
        if name:
            resume.data.setdefault("basics", {})["name"] = name
            resume.data["basics"]["label"] = role
        resume.target_role = role
        if level in dict(resume._meta.get_field("experience_level").choices):
            resume.experience_level = level
        if role:
            resume.title = f"{role}"
        resume.save()
        return redirect(edit_url(resume))
    return render(request, "builder/wizard.html", {
        "resume": resume,
        "token": resume.edit_token,
        "edit_url": edit_url(resume),
        "levels": resume._meta.get_field("experience_level").choices,
    })

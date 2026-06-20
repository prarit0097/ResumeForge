"""Builder entry points: start a new draft, list device drafts, and the editor."""
from __future__ import annotations

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.resumes import services
from apps.templates_engine import registry
from core.access import edit_url, get_resume_or_404, set_token_cookie
from core.sessions import ensure_session_key


@ratelimit(key="ip", rate="30/m", block=True)
def start_new(request):
    """Create a fresh draft for this device and send the user to the wizard."""
    session_key = ensure_session_key(request)
    resume = services.create_resume(session_key)
    response = redirect(reverse("builder:wizard", args=[resume.id]) + f"?t={resume.edit_token}")
    return set_token_cookie(response, resume)


@require_POST
@ratelimit(key="ip", rate="20/m", block=True)
def create_variant(request, resume_id):
    """Make a tailored copy of a resume (for a specific job) and open it."""
    resume = get_resume_or_404(request, resume_id)
    variant = services.create_variant(resume)
    return redirect(edit_url(variant))


def my_drafts(request):
    session_key = ensure_session_key(request)
    resumes = services.list_session_resumes(session_key).filter(parent__isnull=True)
    response = render(request, "builder/my_drafts.html", {"resumes": resumes})
    response["Cache-Control"] = "no-store"  # page contains secret edit tokens
    return response


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


def compare(request, resume_id):
    """Before/after view for the enhance flow: original vs AI-enhanced, with the
    ATS score delta and a concrete list of improvements + benefits."""
    from apps.ai import enhance as ai_enhance
    from apps.ats import compatibility
    from apps.templates_engine.render import render_data_partial

    resume = get_resume_or_404(request, resume_id)
    original = resume.original_data or resume.data
    enhanced = resume.data
    meta = registry.get(resume.template_id)

    before = compatibility.score_resume(original, meta)
    after = compatibility.score_resume(enhanced, meta)
    summary = ai_enhance.summarize_improvements(
        original, enhanced, before["score"], after["score"])

    return render(request, "builder/compare.html", {
        "resume": resume,
        "token": resume.edit_token,
        "edit_url": edit_url(resume),
        "before_html": render_data_partial(original, resume.template_id),
        "after_html": render_data_partial(enhanced, resume.template_id),
        "before_score": before,
        "after_score": after,
        "summary": summary,
        "template": meta,
    })


@require_POST
def use_original(request, resume_id):
    """Discard the enhancement and keep the user's original parsed resume."""
    resume = get_resume_or_404(request, resume_id)
    if resume.original_data:
        resume.data = resume.original_data
        resume.save(update_fields=["data", "updated_at"])
    return redirect(edit_url(resume))


@ratelimit(key="ip", rate="60/m", method="POST", block=True)
def wizard(request, resume_id):
    """Step 1: light intake (name, target role, level). Then -> template gallery."""
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
        # Step 2 = pick a template, then the editor opens in that template.
        return redirect(reverse("templates_engine:gallery", args=[resume.id]) + f"?t={resume.edit_token}")
    return render(request, "builder/wizard.html", {
        "resume": resume,
        "token": resume.edit_token,
        "edit_url": edit_url(resume),
        "gallery_url": reverse("templates_engine:gallery", args=[resume.id]) + f"?t={resume.edit_token}",
        "levels": resume._meta.get_field("experience_level").choices,
    })

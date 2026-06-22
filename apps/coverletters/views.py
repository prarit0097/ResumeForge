"""Cover letter editor: generate, edit, save."""
from __future__ import annotations

from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.resumes.models import CoverLetter
from core.access import get_resume_or_404

from . import services


def cover_letter(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    letter = resume.cover_letters.first()
    return render(request, "coverletters/cover_letter.html", {
        "resume": resume,
        "token": resume.edit_token,
        "letter": letter,
    })


@require_POST
@ratelimit(key="ip", rate="15/m", block=True)
def generate(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    body = services.generate_for_resume(resume)
    letter = resume.cover_letters.first()
    if letter:
        letter.body = body
        letter.job_description = resume.job_description
        letter.save()
    else:
        CoverLetter.objects.create(resume=resume, body=body,
                                   job_description=resume.job_description)
    return redirect(f"/r/{resume.id}/cover-letter/?t={resume.edit_token}")


@require_POST
@ratelimit(key="ip", rate="60/m", block=True)
def save(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    body = request.POST.get("body", "")[:20000]
    letter = resume.cover_letters.first()
    if letter:
        letter.body = body
        letter.save(update_fields=["body", "updated_at"])
    else:
        CoverLetter.objects.create(
            resume=resume, body=body, job_description=resume.job_description)
    return redirect(f"/r/{resume.id}/cover-letter/?t={resume.edit_token}")

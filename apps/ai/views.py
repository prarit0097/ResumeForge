"""AI editor endpoints (htmx/fetch). Rate-limited for cost protection."""
from __future__ import annotations

import json

from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.resumes import services as resume_services
from core.access import get_resume_or_404

from . import services

AI_RATE = "30/m"


def _json(request) -> dict | None:
    if len(request.body) > 64 * 1024:
        return None
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


@require_POST
@ratelimit(key="ip", rate=AI_RATE, block=True)
def improve(request, resume_id):
    get_resume_or_404(request, resume_id)
    payload = _json(request)
    if payload is None:
        return HttpResponseBadRequest("Bad payload")
    text = str(payload.get("text", ""))[:6000]
    instruction = payload.get("instruction")
    if instruction:
        result = services.prompt_edit(text, str(instruction)[:500])
    else:
        result = services.improve_text(text, str(payload.get("kind", "summary"))[:40])
    return JsonResponse({"text": result})


@require_POST
@ratelimit(key="ip", rate="10/m", block=True)
def polish(request, resume_id):
    """One-click: rewrite the WHOLE resume to be professional + ATS-strong.
    Honest — improves real content (strong verbs, sharp summary, surfaced skills,
    JD-tailoring if a JD is set); never fabricates jobs, skills or metrics."""
    resume = get_resume_or_404(request, resume_id)
    from apps.ai import enhance

    jd = (resume.job_description or "").strip() or None
    polished = enhance.enhance_resume_data(resume.data, jd)
    errors = resume_services.update_resume_data(resume, polished)
    if errors:
        return JsonResponse({"ok": False, "error": "Could not polish the resume."}, status=400)
    return JsonResponse({"ok": True})


@require_POST
@ratelimit(key="ip", rate=AI_RATE, block=True)
def bullets(request, resume_id):
    get_resume_or_404(request, resume_id)
    payload = _json(request)
    if payload is None:
        return HttpResponseBadRequest("Bad payload")
    context = {
        "position": str(payload.get("position", ""))[:200],
        "company": str(payload.get("company", ""))[:200],
        "summary": str(payload.get("summary", ""))[:2000],
    }
    return JsonResponse({"bullets": services.generate_bullets(context)})

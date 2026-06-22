"""Live scoring + tailoring endpoints used by the editor."""
from __future__ import annotations

import json
from copy import deepcopy

from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.ai import services as ai_services
from apps.resumes import schema
from apps.resumes import services as resume_services
from apps.templates_engine import registry
from core.access import get_resume_or_404

from . import compatibility, jd_match


def _json(request) -> dict | None:
    if len(request.body) > 256 * 1024:
        return None
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


@require_POST
@ratelimit(key="ip", rate="120/m", block=True)
def score(request, resume_id):
    """Return live ATS compatibility + (if JD provided) match score."""
    resume = get_resume_or_404(request, resume_id)
    payload = _json(request)
    if payload is None:
        return HttpResponseBadRequest("Bad payload")

    data = payload.get("data") or resume.data
    # Client-supplied data is untrusted; fall back to the saved (valid) data if
    # it's malformed so the scorers never crash on a bad shape.
    if schema.validate_resume_data(data):
        data = resume.data
    jd = (payload.get("jd") or resume.job_description or "").strip()[:8000]
    meta = registry.get(resume.template_id)

    ats = compatibility.score_resume(data, meta)
    result = {"ats": ats}
    if jd:
        result["match"] = jd_match.score(data, jd)

    # Cache latest scores on the resume.
    resume.ats_score = ats
    resume.match_score = result.get("match")
    if jd and jd != resume.job_description:
        resume.job_description = jd
        resume.save(update_fields=["ats_score", "match_score", "job_description", "updated_at"])
    else:
        resume.save(update_fields=["ats_score", "match_score", "updated_at"])
    return JsonResponse(result)


@require_POST
@ratelimit(key="ip", rate="20/m", block=True)
def tailor(request, resume_id):
    """Rewrite summary + bullets toward the JD, save, and return new scores."""
    resume = get_resume_or_404(request, resume_id)
    jd = (resume.job_description or "").strip()[:8000]  # re-cap (cost guard)
    if not jd:
        return JsonResponse({"ok": False, "error": "Add a job description first."}, status=400)

    # Bound total LLM calls per request: rewrite at most this many bullets.
    MAX_BULLETS = 25
    budget = MAX_BULLETS
    data = deepcopy(resume.data)
    basics = data.get("basics", {})
    if basics.get("summary"):
        basics["summary"] = ai_services.rewrite_to_jd(basics["summary"], jd)
    for job in data.get("work", []):
        new_highlights = []
        for h in (job.get("highlights") or []):
            if h.strip() and budget > 0:
                new_highlights.append(ai_services.rewrite_to_jd(h, jd))
                budget -= 1
            else:
                new_highlights.append(h)
        job["highlights"] = new_highlights

    errors = resume_services.update_resume_data(resume, data)
    if errors:
        return JsonResponse({"ok": False, "error": "Could not save the tailored resume."}, status=400)
    meta = registry.get(resume.template_id)
    return JsonResponse({
        "ok": True,
        "ats": compatibility.score_resume(resume.data, meta),
        "match": jd_match.score(resume.data, jd),
    })

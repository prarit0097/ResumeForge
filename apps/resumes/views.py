"""Resume mutation endpoints used by the editor (htmx/fetch)."""
from __future__ import annotations

import json

from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.templates_engine import registry
from apps.templates_engine.render import render_resume_partial
from core.access import get_resume_or_404

from . import services

MAX_BODY = 256 * 1024  # 256 KB cap on resume JSON payloads


def _parse_body(request) -> dict | None:
    if len(request.body) > MAX_BODY:
        return None
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


@require_POST
@ratelimit(key="ip", rate="120/m", block=True)
def autosave(request, resume_id):
    """Accept resume section data, validate, save, return rendered preview."""
    resume = get_resume_or_404(request, resume_id)
    payload = _parse_body(request)
    if payload is None:
        return HttpResponseBadRequest("Invalid or oversized payload.")

    data = payload.get("data", payload)
    errors = services.update_resume_data(resume, data)
    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    if payload.get("title"):
        resume.title = str(payload["title"])[:200]
        resume.save(update_fields=["title", "updated_at"])

    html = render_resume_partial(resume)
    return HttpResponse(html)


@require_POST
def set_template(request, resume_id):
    """Switch the resume's template (no data loss). Redirects to the editor on a
    normal form POST; returns the new preview HTML for htmx/ajax callers."""
    resume = get_resume_or_404(request, resume_id)
    template_id = request.POST.get("template_id", "")
    meta = registry.get(template_id)
    resume.template_id = meta.id
    resume.save(update_fields=["template_id", "updated_at"])
    if request.headers.get("HX-Request") or request.headers.get("x-requested-with") == "XMLHttpRequest":
        return HttpResponse(render_resume_partial(resume))
    return redirect(f"/r/{resume.id}/edit/?t={resume.edit_token}")

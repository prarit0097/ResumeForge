"""AI editor endpoints (htmx/fetch). Rate-limited for cost protection."""
from __future__ import annotations

import json

from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

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
    text = str(payload.get("text", ""))
    instruction = payload.get("instruction")
    if instruction:
        result = services.prompt_edit(text, str(instruction))
    else:
        result = services.improve_text(text, payload.get("kind", "summary"))
    return JsonResponse({"text": result})


@require_POST
@ratelimit(key="ip", rate=AI_RATE, block=True)
def bullets(request, resume_id):
    get_resume_or_404(request, resume_id)
    payload = _json(request)
    if payload is None:
        return HttpResponseBadRequest("Bad payload")
    context = {
        "position": str(payload.get("position", "")),
        "company": str(payload.get("company", "")),
        "summary": str(payload.get("summary", "")),
    }
    return JsonResponse({"bullets": services.generate_bullets(context)})

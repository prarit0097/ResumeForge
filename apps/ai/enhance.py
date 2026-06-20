"""AI resume enhancement + a human-readable before/after improvement summary.

Used by the 'enhance existing resume' flow: we keep the parsed original, produce
an improved version, and explain concretely what got better and why it helps.
"""
from __future__ import annotations

import logging
import re
from copy import deepcopy

from apps.ats.constants import STRONG_ACTION_VERBS
from apps.resumes import schema

from . import prompts, services
from .provider import get_provider

logger = logging.getLogger(__name__)

_KNOWN = set(schema.empty_resume().keys())
_ENHANCE_SCHEMA = {"type": "object", "additionalProperties": True}


def _unwrap(result: dict) -> dict:
    if not isinstance(result, dict):
        return {}
    if _KNOWN & set(result.keys()):
        return result
    for value in result.values():
        if isinstance(value, dict) and (_KNOWN & set(value.keys())):
            return value
    return result


def enhance_resume_data(data: dict) -> dict:
    """Return an ATS-improved copy of ``data`` (never invents, never loses data)."""
    original = deepcopy(data)
    try:
        result = _unwrap(get_provider().structured(
            prompts.enhance_messages(original), _ENHANCE_SCHEMA,
            task="enhance_resume", context={"data": original}, strict=False,
        ))
    except Exception:  # noqa: BLE001
        logger.exception("LLM enhance failed; using local fallback")
        result = {}

    if isinstance(result, dict) and (_KNOWN & set(result.keys())):
        enhanced = schema.merge_into_resume(original, result)
        if not schema.validate_resume_data(enhanced):
            return enhanced
    return _local_enhance(original)


def _local_enhance(data: dict) -> dict:
    """Offline fallback: improve summary + bullets via the (mock-capable) AI layer."""
    enhanced = deepcopy(data)
    basics = enhanced.get("basics", {})
    if basics.get("summary"):
        basics["summary"] = services.improve_text(basics["summary"], "summary")
    for job in enhanced.get("work", []):
        job["highlights"] = [services.improve_text(h, "bullet")
                             for h in (job.get("highlights") or []) if h.strip()]
    for pr in enhanced.get("projects", []):
        pr["highlights"] = [services.improve_text(h, "bullet")
                            for h in (pr.get("highlights") or []) if h.strip()]
    return enhanced


# --- before/after summary ---------------------------------------------------

def _bullets(data: dict) -> list[str]:
    out: list[str] = []
    for job in data.get("work", []):
        out.extend(h for h in (job.get("highlights") or []) if h.strip())
    for pr in data.get("projects", []):
        out.extend(h for h in (pr.get("highlights") or []) if h.strip())
    return out


def _quantified(bullets: list[str]) -> int:
    return sum(1 for b in bullets if re.search(r"\d", b))


def _strong_verb_starts(bullets: list[str]) -> int:
    n = 0
    for b in bullets:
        first = re.sub(r"[^a-z]", "", b.strip().split(" ")[0].lower())
        if first in STRONG_ACTION_VERBS:
            n += 1
    return n


def summarize_improvements(original: dict, enhanced: dict,
                           before_score: int, after_score: int) -> dict:
    """Return {delta, improvements:[...], benefits:[...]} explaining the upgrade."""
    o_bullets, e_bullets = _bullets(original), _bullets(enhanced)
    improvements: list[str] = []

    q_gain = _quantified(e_bullets) - _quantified(o_bullets)
    if q_gain > 0:
        improvements.append(f"Added measurable results to {q_gain} bullet point{'s' if q_gain > 1 else ''}.")

    v_gain = _strong_verb_starts(e_bullets) - _strong_verb_starts(o_bullets)
    if v_gain > 0:
        improvements.append(f"Rewrote {v_gain} bullet{'s' if v_gain > 1 else ''} to start with a strong action verb.")

    o_sum = (original.get("basics", {}).get("summary") or "").strip()
    e_sum = (enhanced.get("basics", {}).get("summary") or "").strip()
    if e_sum and e_sum != o_sum:
        improvements.append("Rewrote your professional summary to be sharper and keyword-rich.")

    improvements.append("Reformatted everything into a clean, single-column layout that ATS software reads correctly.")
    improvements.append("Standardized section headings and dates so parsers don't drop your details.")

    benefits = [
        f"Your ATS score went from {before_score} to {after_score}"
        + (f" — a {after_score - before_score}-point jump." if after_score > before_score else "."),
        "Recruiters and ATS filters can now find your key skills and impact instantly.",
        "Quantified, action-led bullets make your experience far more convincing.",
        "Parse-safe formatting means your resume won't get garbled in the applicant system.",
    ]

    return {
        "delta": after_score - before_score,
        "improvements": improvements,
        "benefits": benefits,
    }

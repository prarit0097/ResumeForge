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

    enhanced = None
    if isinstance(result, dict) and (_KNOWN & set(result.keys())):
        merged = schema.merge_into_resume(original, result)
        # Never let the model silently DROP jobs/education/projects.
        if not schema.validate_resume_data(merged) and not _dropped_entries(original, merged):
            enhanced = merged
    if enhanced is None:
        enhanced = _local_enhance(original)
    return ensure_ats_polish(enhanced)


def _dropped_entries(original: dict, enhanced: dict) -> bool:
    """True if the enhanced resume has fewer entries in any list section."""
    for key in ("work", "education", "projects", "certifications", "awards"):
        if len(enhanced.get(key, [])) < len(original.get(key, [])):
            return True
    return False


# --- deterministic ATS polish (guarantees the score levers) -----------------

_LABEL_NOISE = {"expert", "specialist", "professional", "head", "lead", "leader"}


def _skill_count(data: dict) -> int:
    return sum(len(s.get("keywords") or []) or (1 if s.get("name") else 0)
              for s in data.get("skills", []))


def ensure_ats_polish(data: dict) -> dict:
    """Guarantee a Skills section (the biggest ATS-compatibility lever) when the
    resume clearly has skills in its content but no skills section. Never
    fabricates — only surfaces skills already present in titles/summary/bullets."""
    if _skill_count(data) >= 6:
        return data

    from apps.ats.keywords import HARD_SKILL_TAXONOMY

    basics = data.get("basics", {})
    derived: list[str] = []

    _LEAD_FILLER = {"in", "and", "the", "a", "an", "of", "with", "for", "to",
                    "on", "at", "by", "driving", "drive", "including", "across"}

    def _add(kw: str):
        words = " ".join(kw.split()).strip(" ,.-").split()
        while words and words[0].lower() in _LEAD_FILLER:
            words = words[1:]
        kw = " ".join(words)
        if kw and kw.lower() not in {d.lower() for d in derived} and 1 <= len(words) <= 4:
            derived.append(kw)

    # 1) Skill phrases from the professional title (e.g. "Revenue Growth Expert").
    label = basics.get("label") or ""
    for part in re.split(r"[|,/•·]| - | – ", label):
        words = [w for w in part.split() if w.lower() not in _LABEL_NOISE]
        if 1 <= len(words) <= 4:
            _add(" ".join(words))

    # 1b) Competency phrases from the summary ("<word> management/leadership/…").
    summary = basics.get("summary") or ""
    for m in re.finditer(
        r"\b([A-Za-z][\w&-]*(?:\s+[A-Za-z][\w&-]*)?)\s+"
        r"(management|leadership|development|operations|strategy|planning|analysis|"
        r"growth|optimization|collaboration|engineering|design|administration)\b",
        summary, re.I):
        _add(m.group(0))

    # 2) Known hard skills mentioned anywhere in the resume text.
    blob = " ".join([
        basics.get("summary") or "", label,
        " ".join(h for j in data.get("work", []) for h in (j.get("highlights") or [])),
        " ".join(j.get("position") or "" for j in data.get("work", [])),
    ]).lower()
    for skill in sorted(HARD_SKILL_TAXONOMY, key=len, reverse=True):
        if re.search(rf"(?<![a-z]){re.escape(skill.lower())}(?![a-z])", blob):
            _add(skill if skill.isupper() else skill.title())

    if len(derived) >= 3:
        data = deepcopy(data)
        existing = data.get("skills") or []
        existing_kw = {k.lower() for s in existing for k in (s.get("keywords") or [])}
        fresh = [d for d in derived if d.lower() not in existing_kw][:12]
        # Prepend a "Core Skills" group so the section is present + scannable.
        data["skills"] = [{"name": "Core Skills", "keywords": fresh}] + existing
    return data


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

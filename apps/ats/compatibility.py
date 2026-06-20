"""ATS compatibility scorer (0-100), JD-independent.

Deterministic and pure-Python so it is fully unit-testable. Each dimension
returns a status and a SPECIFIC, actionable fix — never a vague score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .constants import STRONG_ACTION_VERBS, WEAK_OPENERS

_NUMBER_RE = re.compile(r"\d")
_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


@dataclass
class Dimension:
    key: str
    label: str
    weight: int
    score: float  # 0..1
    status: str  # "ok" | "warn" | "fail"
    fix: str

    def as_dict(self) -> dict:
        return {
            "key": self.key, "label": self.label, "weight": self.weight,
            "score": round(self.score, 2), "status": self.status, "fix": self.fix,
        }


def _all_highlights(data: dict) -> list[str]:
    out: list[str] = []
    for job in data.get("work", []):
        out.extend(h for h in (job.get("highlights") or []) if h.strip())
    for pr in data.get("projects", []):
        out.extend(h for h in (pr.get("highlights") or []) if h.strip())
    return out


def _contact(data: dict) -> Dimension:
    b = data.get("basics", {})
    have = sum(bool((b.get(k) or "").strip()) for k in ("name", "email", "phone"))
    email_ok = bool(_EMAIL_RE.match((b.get("email") or "").strip()))
    if have == 3 and email_ok:
        return Dimension("contact", "Contact info", 15, 1.0, "ok",
                         "Contact details are complete and in the body.")
    missing = [k for k in ("name", "email", "phone") if not (b.get(k) or "").strip()]
    if not email_ok and (b.get("email") or "").strip():
        missing.append("a valid email")
    return Dimension("contact", "Contact info", 15, have / 3, "fail",
                     f"Add {', '.join(missing) or 'valid contact info'} so recruiters can reach you.")


def _summary(data: dict) -> Dimension:
    text = (data.get("basics", {}).get("summary") or "").strip()
    words = len(text.split())
    if 15 <= words <= 80:
        return Dimension("summary", "Summary", 10, 1.0, "ok",
                         "Strong, appropriately sized summary.")
    if words == 0:
        return Dimension("summary", "Summary", 10, 0.0, "warn",
                         "Add a 2-3 sentence professional summary at the top.")
    return Dimension("summary", "Summary", 10, 0.5, "warn",
                     "Aim for a 2-3 sentence summary (roughly 15-80 words).")


def _experience(data: dict) -> Dimension:
    work = data.get("work", [])
    if not work:
        return Dimension("experience", "Work experience", 15, 0.0, "fail",
                         "Add at least one work experience entry.")
    with_bullets = sum(1 for j in work if [h for h in (j.get("highlights") or []) if h.strip()])
    ratio = with_bullets / len(work)
    if ratio == 1:
        return Dimension("experience", "Work experience", 15, 1.0, "ok",
                         "Every role has achievement bullets.")
    return Dimension("experience", "Work experience", 15, ratio, "warn",
                     "Add achievement bullets to every role.")


def _action_verbs(data: dict) -> Dimension:
    bullets = _all_highlights(data)
    if not bullets:
        return Dimension("verbs", "Action verbs", 15, 0.0, "warn",
                         "Start each bullet with a strong action verb (Led, Built, Improved).")
    strong = 0
    for b in bullets:
        first = re.sub(r"[^a-z]", "", b.strip().split(" ")[0].lower())
        if first in STRONG_ACTION_VERBS:
            strong += 1
        elif first in WEAK_OPENERS:
            strong += 0
    ratio = strong / len(bullets)
    if ratio >= 0.8:
        return Dimension("verbs", "Action verbs", 15, 1.0, "ok",
                         "Bullets lead with strong action verbs.")
    return Dimension("verbs", "Action verbs", 15, ratio, "warn",
                     "Rewrite weak bullets to start with action verbs (avoid 'Responsible for', 'Worked on').")


def _quantified(data: dict) -> Dimension:
    bullets = _all_highlights(data)
    if not bullets:
        return Dimension("quantified", "Quantified impact", 15, 0.0, "warn",
                         "Add measurable results (%, $, time saved) to your bullets.")
    quant = sum(1 for b in bullets if _NUMBER_RE.search(b))
    ratio = quant / len(bullets)
    if ratio >= 0.5:
        return Dimension("quantified", "Quantified impact", 15, 1.0, "ok",
                         "Good use of measurable results.")
    return Dimension("quantified", "Quantified impact", 15, ratio, "warn",
                     "At least half your bullets should include a number or metric.")


def _skills(data: dict) -> Dimension:
    skills = data.get("skills", [])
    count = sum(len(s.get("keywords") or []) or (1 if s.get("name") else 0) for s in skills)
    if count >= 6:
        return Dimension("skills", "Skills", 10, 1.0, "ok",
                         "Solid, scannable skills section.")
    if count == 0:
        return Dimension("skills", "Skills", 10, 0.0, "fail",
                         "Add a Skills section with relevant keywords.")
    return Dimension("skills", "Skills", 10, count / 6, "warn",
                     "List more relevant skills (aim for 6+ keywords).")


def _education(data: dict) -> Dimension:
    if data.get("education"):
        return Dimension("education", "Education", 5, 1.0, "ok", "Education present.")
    return Dimension("education", "Education", 5, 0.0, "warn",
                     "Add your education (degree, institution, dates).")


def score_resume(data: dict, template_meta=None) -> dict:
    """Score a resume's ATS compatibility. ``template_meta`` adds a parse-safety
    dimension based on whether the chosen layout is single-column."""
    dims = [
        _contact(data), _summary(data), _experience(data), _action_verbs(data),
        _quantified(data), _skills(data), _education(data),
    ]

    ats_safe = getattr(template_meta, "ats_safe", True)
    dims.append(Dimension(
        "parse", "Parse safety", 15,
        1.0 if ats_safe else 0.4,
        "ok" if ats_safe else "warn",
        "Single-column, parser-friendly layout." if ats_safe else
        "This template is two-column; strict ATS (Taleo, Workday) may drop the sidebar. Pick an ATS-safe template to be safe.",
    ))

    total_weight = sum(d.weight for d in dims)
    score = round(100 * sum(d.score * d.weight for d in dims) / total_weight)
    grade = "Excellent" if score >= 85 else "Good" if score >= 70 else \
        "Needs work" if score >= 50 else "Incomplete"
    summary = f"{grade} — {score}/100 ATS-ready." if score >= 70 else \
        f"{grade} — fix the flagged items to improve your score."
    return {
        "score": score,
        "grade": grade,
        "summary": summary,
        "dimensions": [d.as_dict() for d in dims],
    }

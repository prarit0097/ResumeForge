"""JD-match scorer (0-100). Jobscan-style, weighted toward hard skills + title.

Honest by design: warns above ~88 about over-optimization and never rewards
keyword stuffing (it counts presence, not repetition).
"""
from __future__ import annotations

from . import keywords

# Dimension weights (must sum to 100).
W_HARD = 55
W_TITLE = 20
W_EDUCATION = 10
W_SOFT = 15

# Skill tokens that should display upper-cased rather than title-cased.
_ACRONYMS = {"aws", "gcp", "sql", "api", "css", "html", "ci/cd", "ml", "ai",
             "nlp", "etl", "qa", "ios", "php", "tcp/ip", "rest", "json", "k8s"}


def _display(term: str) -> str:
    t = (term or "").strip()
    if t.lower() in _ACRONYMS:
        return t.upper()
    return t[:1].upper() + t[1:] if t else t


def _ratio(found: list[str], required: list[str]) -> float:
    if not required:
        return 1.0
    have = sum(1 for r in required if r in found)
    return have / len(required)


def score(data: dict, jd_text: str) -> dict:
    """Score how well a resume matches a job description."""
    if not (jd_text or "").strip():
        return {"score": 0, "matched": [], "missing": [], "suggested": [],
                "dimensions": [], "warnings": ["Paste a job description to see your match score."]}

    req = keywords.extract(jd_text)
    rtext = keywords.resume_text(data).lower()

    def present(term: str) -> bool:
        return term.lower() in rtext

    hard_found = [k for k in req["hard"] if present(k)]
    hard_missing = [k for k in req["hard"] if not present(k)]
    soft_found = [k for k in req["soft"] if present(k)]

    hard_ratio = _ratio(hard_found, req["hard"])
    soft_ratio = _ratio(soft_found, req["soft"])
    title_ratio = 1.0 if (req["title"] and req["title"].lower() in rtext) else (
        0.0 if req["title"] else 1.0)
    edu_ratio = 1.0 if (not req["education"] or
                        any(present(t) for t in ("bachelor", "master", "phd", "b.s", "m.s", "degree"))) else 0.0

    raw = (W_HARD * hard_ratio + W_TITLE * title_ratio +
           W_EDUCATION * edu_ratio + W_SOFT * soft_ratio)
    final = round(raw)

    warnings: list[str] = []
    if final >= 88:
        warnings.append("Your match is very high — avoid over-optimizing; keep bullets natural and readable.")
    suggested = (hard_missing + [k for k in req["extra"] if not present(k)])[:10]

    dimensions = [
        {"key": "hard", "label": "Hard skills", "weight": W_HARD,
         "score": round(hard_ratio, 2),
         "fix": f"Add missing skills: {', '.join(hard_missing[:6])}" if hard_missing else "Strong hard-skill match."},
        {"key": "title", "label": "Job title", "weight": W_TITLE,
         "score": round(title_ratio, 2),
         "fix": f"Mention the target title '{req['title']}' if it fits your experience." if title_ratio < 1 and req["title"] else "Title aligns."},
        {"key": "education", "label": "Education", "weight": W_EDUCATION,
         "score": round(edu_ratio, 2),
         "fix": "This role expects a degree — make sure yours is listed." if edu_ratio < 1 else "Education requirement met."},
        {"key": "soft", "label": "Soft skills", "weight": W_SOFT,
         "score": round(soft_ratio, 2),
         "fix": f"Weave in: {', '.join([s for s in req['soft'] if s not in soft_found][:4])}" if soft_ratio < 1 else "Soft skills covered."},
    ]

    return {
        "score": final,
        "matched": [_display(s) for s in hard_found + soft_found],
        "missing": [_display(s) for s in hard_missing],
        "suggested": [_display(s) for s in suggested],
        "dimensions": dimensions,
        "warnings": warnings,
        "target": "Aim for 75%+. Don't chase 100% — keyword stuffing gets you rejected by humans.",
    }

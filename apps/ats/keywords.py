"""Keyword extraction from a job description and from resume data.

Uses a curated skill taxonomy for high-confidence hard-skill detection, plus a
frequency heuristic for the long tail. Pure-Python and deterministic.
"""
from __future__ import annotations

import re

from .constants import STOPWORDS

# A compact curated taxonomy of common hard skills/tools. Matching against this
# gives high-precision hard-skill detection independent of the LLM.
HARD_SKILL_TAXONOMY = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    "react", "angular", "vue", "svelte", "node", "nodejs", "django", "flask",
    "fastapi", "spring", "rails", ".net", "express", "next.js", "nextjs",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "git", "ci/cd", "graphql", "rest", "kafka", "rabbitmq",
    "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "spark",
    "tableau", "power bi", "excel", "figma", "sketch", "photoshop",
    "machine learning", "deep learning", "nlp", "data analysis", "etl",
    "agile", "scrum", "jira", "salesforce", "sap", "seo", "google analytics",
    "product management", "project management", "ux", "ui", "accessibility",
}

SOFT_SKILLS = {
    "communication", "leadership", "teamwork", "collaboration", "problem solving",
    "adaptability", "time management", "critical thinking", "creativity",
    "mentoring", "stakeholder management", "negotiation", "presentation",
}

_TITLE_RE = re.compile(
    r"\b(software engineer|data scientist|data analyst|product manager|"
    r"project manager|designer|developer|engineer|analyst|manager|"
    r"architect|consultant|specialist|lead|director)\b", re.I)

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#./-]{1,}")


def _normalize(text: str) -> str:
    return (text or "").lower()


def _find_phrases(text: str, vocabulary: set[str]) -> list[str]:
    low = _normalize(text)
    found = []
    for term in vocabulary:
        # word-boundary-ish match that tolerates symbols like c++, ci/cd
        pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
        if re.search(pattern, low):
            found.append(term)
    return sorted(set(found))


def extract(jd_text: str) -> dict:
    """Extract structured keyword requirements from a job description."""
    hard = _find_phrases(jd_text, HARD_SKILL_TAXONOMY)
    soft = _find_phrases(jd_text, SOFT_SKILLS)

    # Long-tail frequent capitalized/technical terms not already captured.
    counts: dict[str, int] = {}
    for w in _WORD_RE.findall(jd_text or ""):
        lw = w.lower()
        if lw in STOPWORDS or len(lw) < 3:
            continue
        counts[lw] = counts.get(lw, 0) + 1
    extra = [w for w, c in sorted(counts.items(), key=lambda x: -x[1])
             if c >= 2 and w not in hard and w not in soft][:10]

    title_match = _TITLE_RE.search(jd_text or "")
    education = None
    if re.search(r"\b(bachelor|b\.?s\.?|master|m\.?s\.?|phd|degree)\b", jd_text or "", re.I):
        education = "degree"

    return {
        "hard": hard,
        "soft": soft,
        "extra": extra,
        "title": title_match.group(0).title() if title_match else "",
        "education": education,
    }


def resume_text(data: dict) -> str:
    """Flatten resume data into searchable text for matching."""
    parts: list[str] = []
    b = data.get("basics", {})
    parts.append(b.get("label", ""))
    parts.append(b.get("summary", ""))
    for job in data.get("work", []):
        parts.append(job.get("position", ""))
        parts.append(job.get("summary", ""))
        parts.extend(job.get("highlights") or [])
    for pr in data.get("projects", []):
        parts.append(pr.get("name", ""))
        parts.append(pr.get("description", ""))
        parts.extend(pr.get("highlights") or [])
        parts.extend(pr.get("keywords") or [])
    for s in data.get("skills", []):
        parts.append(s.get("name", ""))
        parts.extend(s.get("keywords") or [])
    for ed in data.get("education", []):
        parts.append(ed.get("studyType", ""))
        parts.append(ed.get("area", ""))
    return " ".join(p for p in parts if p)

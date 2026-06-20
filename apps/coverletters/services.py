"""Cover letter generation (resume + JD aware) via the AI layer."""
from __future__ import annotations

from apps.ai import services as ai_services


def build_context(resume) -> dict:
    b = resume.data.get("basics", {})
    recent = resume.data.get("work", [])
    return {
        "name": b.get("name", ""),
        "label": b.get("label", ""),
        "summary": b.get("summary", ""),
        "target_role": resume.target_role or b.get("label", ""),
        "recent_role": recent[0].get("position") if recent else "",
        "recent_company": recent[0].get("company") if recent else "",
        "jd": resume.job_description or "",
    }


def generate_for_resume(resume) -> str:
    return ai_services.generate_cover_letter(build_context(resume))

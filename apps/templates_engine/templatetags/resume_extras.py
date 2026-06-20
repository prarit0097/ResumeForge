"""Template filters for rendering resume data in an ATS-safe way."""
from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def skills_inline(skills) -> str:
    """Render skills as an inline, parser-friendly delimited string.

    Each skill becomes "Name: kw, kw" (or just the name). Joined with " · ".
    ATS parsers read this linearly far better than a grid of pills.
    """
    if not skills:
        return ""
    parts: list[str] = []
    for skill in skills:
        if not isinstance(skill, dict):
            continue
        name = (skill.get("name") or "").strip()
        keywords = [k for k in (skill.get("keywords") or []) if k]
        if name and keywords:
            parts.append(f"{name}: {', '.join(keywords)}")
        elif name:
            parts.append(name)
        elif keywords:
            parts.extend(keywords)
    return "  ·  ".join(parts)

"""Template registry. Each template is metadata pointing at a Django partial
that renders the resume JSON. The SAME partial is used for live preview and
for PDF/PNG export, so what the user sees is exactly what downloads.

ATS note: ``ats_safe=True`` means single-column, no tables/text-boxes, standard
headings — the layouts that parse cleanly. Creative multi-column templates are
marked False with a human-readable ``ats_risk``.
"""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_TEMPLATE_ID = "classic"


@dataclass(frozen=True)
class TemplateMeta:
    id: str
    name: str
    category: str
    ats_safe: bool
    partial: str  # template path rendered with {resume, meta}
    accent: str = "#4f46e5"
    font: str = "Inter"
    ats_risk: str = ""
    description: str = ""


# Categories: Professional, Modern, Minimal, Creative, Technical, Executive, Academic, Simple
_TEMPLATES: dict[str, TemplateMeta] = {}


def register(meta: TemplateMeta) -> None:
    _TEMPLATES[meta.id] = meta


def get(template_id: str) -> TemplateMeta:
    return _TEMPLATES.get(template_id) or _TEMPLATES[DEFAULT_TEMPLATE_ID]


def all_templates() -> list[TemplateMeta]:
    return list(_TEMPLATES.values())


def categories() -> list[str]:
    seen: list[str] = []
    for meta in _TEMPLATES.values():
        if meta.category not in seen:
            seen.append(meta.category)
    return seen


# --- Starter library. Phase 9 expands this toward 100+. ---
# All point at one of a small number of structural partials, differentiated by
# accent colour, font, and category. The structural partials live in
# templates/resume_templates/<layout>.html.
_STARTER = [
    ("classic", "Classic", "Simple", True, "single_column", "#1f2937", "Inter",
     "Timeless single-column layout. The safest possible ATS parse."),
    ("modern", "Modern", "Modern", True, "single_column", "#4f46e5", "Inter",
     "Clean modern lines with an indigo accent. Fully ATS-safe."),
    ("minimal", "Minimal", "Minimal", True, "single_column", "#0f172a", "Inter",
     "Quiet, typographic, lots of whitespace."),
    ("executive", "Executive", "Executive", True, "single_column", "#7c2d12", "Fraunces",
     "Serif headings for senior and leadership roles."),
    ("technical", "Technical", "Technical", True, "single_column", "#0e7490", "Inter",
     "Skills-forward layout for engineers."),
    ("sidebar", "Sidebar", "Creative", False, "two_column", "#4338ca", "Inter",
     "Two-column with a coloured sidebar. Striking, but parses less reliably."),
]

for _id, _name, _cat, _safe, _layout, _accent, _font, _desc in _STARTER:
    register(TemplateMeta(
        id=_id, name=_name, category=_cat, ats_safe=_safe,
        partial=f"resume_templates/{_layout}.html",
        accent=_accent, font=_font, description=_desc,
        ats_risk="" if _safe else "Two-column sidebars can drop content in strict parsers (Taleo, Workday).",
    ))

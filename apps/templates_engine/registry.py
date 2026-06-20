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
    style_class: str = ""  # CSS modifier classes for visual variation
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


# --- Template catalog --------------------------------------------------------
# Genuinely distinct STRUCTURAL layouts (separate HTML partials), each combined
# with curated colour/font/heading themes to produce a large, distinct library.
# Every template renders the same resume JSON; only the chrome differs.

# Curated colour themes (name, accent hex).
_THEMES = [
    ("Indigo", "#4f46e5"), ("Slate", "#1f2937"), ("Teal", "#0e7490"),
    ("Emerald", "#047857"), ("Crimson", "#b91c1c"), ("Burgundy", "#7c2d12"),
    ("Navy", "#1e3a8a"), ("Royal", "#4338ca"), ("Plum", "#6b21a8"),
    ("Charcoal", "#0f172a"), ("Forest", "#14532d"), ("Bronze", "#92400e"),
    ("Steel", "#334155"), ("Ocean", "#0369a1"), ("Magenta", "#a21caf"),
]

# Structural layouts: (layout_key, partial, ats_safe, category, style_class,
#                       font, blurb, theme_count)
_LAYOUTS = [
    ("classic", "single_column", True, "Simple", "", "Inter",
     "Timeless single-column. The safest possible ATS parse.", 9),
    ("modern", "single_column", True, "Modern", "rf-head-left rf-rule-bold", "Inter",
     "Clean modern lines with a bold section rule.", 9),
    ("minimal", "single_column", True, "Minimal", "rf-rule-thin rf-airy", "Inter",
     "Quiet and typographic with generous whitespace.", 8),
    ("centered", "single_column", True, "Minimal", "rf-head-center", "Inter",
     "Centered header for a calm, balanced look.", 7),
    ("executive", "single_column", True, "Executive", "rf-serif rf-rule-bold", "Fraunces",
     "Serif headings for senior and leadership roles.", 8),
    ("academic", "single_column", True, "Academic", "rf-serif rf-rule-thin", "Fraunces",
     "Restrained serif styling for academic and research CVs.", 7),
    ("banner", "header_banner", True, "Professional", "", "Inter",
     "Full-width accent header band, then a clean single column.", 12),
    ("banner_serif", "header_banner", True, "Executive", "rf-serif", "Fraunces",
     "Accent banner with serif headings for a premium feel.", 7),
    ("compact", "compact", True, "Technical", "rf-rule-thin", "Inter",
     "Dense and space-efficient — fit more on one page.", 9),
    ("timeline", "timeline", True, "Modern", "", "Inter",
     "A subtle accent rail marks each section. Still single-column and ATS-safe.", 9),
    ("sidebar", "two_column", False, "Creative", "", "Inter",
     "Two-column with a coloured sidebar. Striking, parses less reliably.", 9),
    ("sidebar_right", "two_column", False, "Creative", "rf-side-right", "Inter",
     "Sidebar on the right for a fresh asymmetric look.", 8),
]


def _slug(text: str) -> str:
    return text.lower().replace(" ", "-")


def _build_catalog() -> None:
    for layout_key, partial, ats_safe, category, style_class, font, blurb, n in _LAYOUTS:
        for theme_name, accent in _THEMES[:n]:
            tid = f"{layout_key}-{_slug(theme_name)}"
            name = f"{layout_key.replace('_', ' ').title()} · {theme_name}"
            register(TemplateMeta(
                id=tid, name=name, category=category, ats_safe=ats_safe,
                partial=f"resume_templates/{partial}.html",
                accent=accent, font=font, style_class=style_class,
                description=blurb,
                ats_risk="" if ats_safe else
                "Two-column sidebars can drop content in strict parsers (Taleo, Workday).",
            ))


_build_catalog()

# Stable alias so DEFAULT_TEMPLATE_ID ("classic") always resolves.
if DEFAULT_TEMPLATE_ID not in _TEMPLATES:
    _first_classic = next((t for t in _TEMPLATES.values() if t.id.startswith("classic")), None)
    if _first_classic:
        register(TemplateMeta(
            id=DEFAULT_TEMPLATE_ID, name="Classic", category="Simple",
            ats_safe=True, partial="resume_templates/single_column.html",
            accent="#1f2937", font="Inter",
            description="Timeless single-column. The safest possible ATS parse.",
        ))

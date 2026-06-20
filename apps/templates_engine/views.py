"""Template gallery: browse and switch templates without losing data."""
from __future__ import annotations

from django.shortcuts import render

from core.access import get_resume_or_404

from . import registry, samples
from .render import _DataShim


def _is_sparse(data: dict) -> bool:
    """True when the resume has too little content to preview meaningfully."""
    has_work = bool(data.get("work"))
    has_summary = bool(data.get("basics", {}).get("summary"))
    return not (has_work or has_summary)


def gallery(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    category = request.GET.get("category", "")
    templates = registry.all_templates()
    if category:
        templates = [t for t in templates if t.category == category]

    # Thumbnails render real content if the resume has any; otherwise a sample so
    # each template still shows its true look.
    preview_obj = resume if not _is_sparse(resume.data) else _DataShim(
        samples.sample_resume_data(), resume.template_id)

    return render(request, "builder/gallery.html", {
        "resume": resume,
        "token": resume.edit_token,
        "templates": templates,
        "categories": registry.categories(),
        "active_category": category,
        "current_id": resume.template_id,
        "preview_obj": preview_obj,
        "is_sample": _is_sparse(resume.data),
    })

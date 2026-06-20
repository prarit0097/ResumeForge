"""Template gallery: browse and switch templates without losing data."""
from __future__ import annotations

from django.shortcuts import render

from core.access import get_resume_or_404

from . import registry


def gallery(request, resume_id):
    resume = get_resume_or_404(request, resume_id)
    category = request.GET.get("category", "")
    templates = registry.all_templates()
    if category:
        templates = [t for t in templates if t.category == category]
    return render(request, "builder/gallery.html", {
        "resume": resume,
        "token": resume.edit_token,
        "templates": templates,
        "categories": registry.categories(),
        "active_category": category,
        "current_id": resume.template_id,
    })

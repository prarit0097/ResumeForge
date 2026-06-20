"""Resume access services. All lookups verify the secret edit_token in
constant time. There is no user model — possession of the token IS the auth."""
from __future__ import annotations

import hmac
from copy import deepcopy

from django.db.models import QuerySet

from . import schema
from .models import Resume


def create_resume(session_key: str, **kwargs) -> Resume:
    """Create a new draft for a device session."""
    return Resume.objects.create(session_key=session_key or "", **kwargs)


def get_resume(resume_id, edit_token: str) -> Resume | None:
    """Fetch a resume only if the edit_token matches (constant-time compare)."""
    if not edit_token:
        return None
    try:
        resume = Resume.objects.get(pk=resume_id)
    except (Resume.DoesNotExist, ValueError, TypeError):
        return None
    if not hmac.compare_digest(str(resume.edit_token), str(edit_token)):
        return None
    return resume


def list_session_resumes(session_key: str) -> QuerySet[Resume]:
    """All drafts created on this device session (newest first)."""
    if not session_key:
        return Resume.objects.none()
    return Resume.objects.filter(session_key=session_key)


def update_resume_data(resume: Resume, incoming: dict) -> list[str]:
    """Validate + merge incoming sections into resume.data and save.
    Returns validation errors (empty == saved). Immutable-style merge.

    UI-only fields prefixed with ``__`` (e.g. ``__jd`` for the target job
    description) are never persisted into the stored resume document."""
    incoming = {k: v for k, v in (incoming or {}).items() if not str(k).startswith("__")}
    merged = schema.merge_into_resume(resume.data, incoming)
    errors = schema.validate_resume_data(merged)
    if errors:
        return errors
    resume.data = merged
    resume.save(update_fields=["data", "updated_at"])
    return []


def create_variant(resume: Resume) -> Resume:
    """Create a tailored copy linked to its parent (for per-job variants)."""
    return Resume.objects.create(
        session_key=resume.session_key,
        parent=resume,
        title=f"{resume.title} (tailored)",
        data=deepcopy(resume.data),
        template_id=resume.template_id,
        target_role=resume.target_role,
        experience_level=resume.experience_level,
    )

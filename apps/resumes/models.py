"""No-login data models. Identity = unguessable UUID + secret edit_token."""
from __future__ import annotations

import secrets
import uuid

from django.db import models

from . import schema

DEFAULT_TEMPLATE_ID = "classic"

EXPERIENCE_LEVELS = [
    ("entry", "Entry level / student"),
    ("mid", "Mid level"),
    ("senior", "Senior"),
    ("exec", "Executive / leadership"),
]


def _new_token() -> str:
    return secrets.token_urlsafe(32)


class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    edit_token = models.CharField(max_length=64, default=_new_token, editable=False)
    session_key = models.CharField(max_length=64, blank=True, default="", db_index=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="variants"
    )

    title = models.CharField(max_length=200, blank=True, default="Untitled resume")
    data = models.JSONField(default=schema.empty_resume)
    # Snapshot of the resume as first parsed (before AI enhancement), used for the
    # before/after comparison on the enhance flow. Null for from-scratch builds.
    original_data = models.JSONField(null=True, blank=True)
    template_id = models.CharField(max_length=64, default=DEFAULT_TEMPLATE_ID)

    target_role = models.CharField(max_length=200, blank=True, default="")
    experience_level = models.CharField(
        max_length=20, blank=True, default="", choices=EXPERIENCE_LEVELS
    )
    job_description = models.TextField(blank=True, default="")

    ats_score = models.JSONField(null=True, blank=True)
    match_score = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"

    @property
    def display_name(self) -> str:
        return self.data.get("basics", {}).get("name") or self.title


class CoverLetter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name="cover_letters"
    )
    body = models.TextField(blank=True, default="")
    job_description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

"""Turn raw resume text into structured JSON Resume data using the LLM.

Validates the result against the resume schema; on any failure falls back to the
provider's offline structuring so the enhance flow always produces something.
"""
from __future__ import annotations

import logging

from apps.ai import prompts
from apps.ai.provider import get_provider
from apps.resumes import schema

logger = logging.getLogger(__name__)

# Loose schema for the LLM structured call (mirrors resume schema top level).
_STRUCTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "basics": {"type": "object"},
        "work": {"type": "array"},
        "education": {"type": "array"},
        "skills": {"type": "array"},
        "projects": {"type": "array"},
        "certifications": {"type": "array"},
    },
    "additionalProperties": True,
}


def to_resume_json(raw_text: str) -> dict:
    """Structure raw text into a schema-valid resume dict (never invents)."""
    base = schema.empty_resume()
    try:
        result = get_provider().structured(
            prompts.structure_messages(raw_text), _STRUCTURE_SCHEMA,
            task="structure_resume", context={"raw": raw_text},
        )
    except Exception:  # noqa: BLE001
        logger.exception("LLM structuring failed; using offline fallback")
        result = {}

    if not isinstance(result, dict) or not result:
        from apps.ai.mock import MockProvider
        result = MockProvider().structured(
            [], _STRUCTURE_SCHEMA, task="structure_resume", context={"raw": raw_text})

    merged = schema.merge_into_resume(base, result)
    errors = schema.validate_resume_data(merged)
    if errors:
        logger.warning("Structured resume failed validation: %s", errors[:3])
        # Keep only the safe base + basics we can trust.
        safe = schema.merge_into_resume(base, {"basics": merged.get("basics", {})})
        if schema.validate_resume_data(safe):
            return base
        return safe
    return merged

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


_KNOWN_SECTIONS = set(schema.empty_resume().keys())


def _unwrap_envelope(result: dict) -> dict:
    """Some models wrap the resume in an envelope, e.g. {"resume": {...}} or
    {"data": {...}}. If no known section is at the top level but a nested dict
    value carries them, unwrap to that dict so the sections aren't lost."""
    if not isinstance(result, dict):
        return {}
    if _KNOWN_SECTIONS & set(result.keys()):
        return result
    for value in result.values():
        if isinstance(value, dict) and (_KNOWN_SECTIONS & set(value.keys())):
            return value
    return result


def to_resume_json(raw_text: str) -> dict:
    """Structure raw text into a schema-valid resume dict (never invents)."""
    base = schema.empty_resume()
    try:
        # strict=False -> plain json_object mode (NOT closed json_schema). A loose
        # schema under strict json_schema makes some models emit only a minimal
        # subset of fields, which is the root cause of near-empty extractions.
        result = get_provider().structured(
            prompts.structure_messages(raw_text), _STRUCTURE_SCHEMA,
            task="structure_resume", context={"raw": raw_text}, strict=False,
        )
    except Exception:  # noqa: BLE001
        logger.exception("LLM structuring failed; using offline fallback")
        result = {}

    result = _unwrap_envelope(result)

    # If the model gave us nothing usable, fall back to the offline parser.
    if not isinstance(result, dict) or not (_KNOWN_SECTIONS & set(result.keys())):
        from apps.ai.mock import MockProvider
        result = MockProvider().structured(
            [], _STRUCTURE_SCHEMA, task="structure_resume", context={"raw": raw_text})

    merged = schema.merge_into_resume(base, result)
    errors = schema.validate_resume_data(merged)
    if not errors:
        return merged

    logger.warning("Structured resume failed validation: %s", errors[:3])
    # Don't throw away every section because one is malformed. Re-merge each
    # known section individually and keep the ones that validate, so a single
    # bad field (e.g. work[2].startDate) can't blank out the whole resume.
    safe = schema.empty_resume()
    for key in schema.empty_resume().keys():
        if key not in result:
            continue
        candidate = schema.merge_into_resume(safe, {key: result[key]})
        if not schema.validate_resume_data(candidate):
            safe = candidate
    return safe

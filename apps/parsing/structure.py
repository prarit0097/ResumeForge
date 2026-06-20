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

    return _coerce_to_resume(result)


def _coerce_to_resume(result: dict) -> dict:
    """Merge an LLM section dict onto an empty resume, salvaging valid sections."""
    base = schema.empty_resume()
    merged = schema.merge_into_resume(base, result)
    if not schema.validate_resume_data(merged):
        return merged
    # Don't throw away every section because one is malformed. Re-merge each
    # known section individually and keep the ones that validate.
    safe = schema.empty_resume()
    for key in base.keys():
        if key not in result:
            continue
        candidate = schema.merge_into_resume(safe, {key: result[key]})
        if not schema.validate_resume_data(candidate):
            safe = candidate
    return safe


def extract_and_enhance(raw_text: str) -> tuple[dict, dict]:
    """ONE LLM call returning (original, enhanced) — halves the latency of the
    enhance flow vs structuring then enhancing in two separate round-trips.

    Falls back gracefully: if the combined call doesn't yield both, we structure
    once and enhance locally so the flow always produces a usable result."""
    try:
        result = get_provider().structured(
            prompts.extract_and_enhance_messages(raw_text), _STRUCTURE_SCHEMA,
            task="extract_and_enhance", context={"raw": raw_text}, strict=False,
        )
    except Exception:  # noqa: BLE001
        logger.exception("Combined extract+enhance failed")
        result = {}

    orig_raw = result.get("original") if isinstance(result, dict) else None
    enh_raw = result.get("enhanced") if isinstance(result, dict) else None

    if isinstance(orig_raw, dict) and (_KNOWN_SECTIONS & set(orig_raw.keys())):
        original = _coerce_to_resume(_unwrap_envelope(orig_raw))
        if isinstance(enh_raw, dict) and (_KNOWN_SECTIONS & set(enh_raw.keys())):
            enhanced = _coerce_to_resume(_unwrap_envelope(enh_raw))
        else:
            enhanced = original
        return original, enhanced

    # Fallback: faithful structure (handles mock/offline + odd responses), then
    # enhance separately.
    from apps.ai import enhance as ai_enhance

    original = to_resume_json(raw_text)
    enhanced = ai_enhance.enhance_resume_data(original)
    return original, enhanced

"""High-level AI operations used by the editor and other apps. Every call is
wrapped so an LLM failure degrades gracefully instead of erroring the request."""
from __future__ import annotations

import logging

from . import prompts
from .provider import get_provider

logger = logging.getLogger(__name__)

_BULLETS_SCHEMA = {
    "type": "object",
    "properties": {"bullets": {"type": "array", "items": {"type": "string"}}},
    "required": ["bullets"],
    "additionalProperties": False,
}


def _safe_complete(messages, *, task, context=None, fallback="", **opts) -> str:
    try:
        return get_provider().complete(messages, task=task, context=context, **opts)
    except Exception:  # noqa: BLE001 - never break a request on the LLM
        logger.exception("LLM complete failed for task=%s", task)
        return fallback


def improve_text(text: str, kind: str = "bullet") -> str:
    if not (text or "").strip():
        return text
    return _safe_complete(
        prompts.improve_text_messages(text, kind),
        task="improve_text", context={"text": text}, fallback=text,
    )


def write_summary(context: dict) -> str:
    return _safe_complete(
        prompts.summary_messages(context), task="write_summary",
        context=context, fallback="",
    )


def generate_bullets(context: dict) -> list[str]:
    try:
        result = get_provider().structured(
            prompts.bullets_messages(context), _BULLETS_SCHEMA,
            task="generate_bullets", context=context,
        )
        bullets = result.get("bullets") or []
        return [b for b in bullets if isinstance(b, str) and b.strip()]
    except Exception:  # noqa: BLE001
        logger.exception("LLM generate_bullets failed")
        return []


def rewrite_to_jd(text: str, jd: str) -> str:
    if not (text or "").strip():
        return text
    return _safe_complete(
        prompts.tailor_messages(text, jd), task="improve_text",
        context={"text": text}, fallback=text,
    )


def generate_cover_letter(context: dict) -> str:
    return _safe_complete(
        prompts.cover_letter_messages(context), task="cover_letter",
        context=context, fallback="",
    )


def prompt_edit(text: str, instruction: str) -> str:
    return _safe_complete(
        prompts.prompt_edit_messages(text, instruction), task="prompt_edit",
        context={"text": text, "instruction": instruction}, fallback=text,
    )

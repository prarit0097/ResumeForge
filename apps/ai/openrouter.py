"""OpenRouter provider (OpenAI-compatible) targeting DeepSeek.

Used only when OPENROUTER_API_KEY is set. Falls back gracefully: on any API
error the caller catches and the service degrades, but we never crash a request
because of the LLM. Keys are read from settings (env), never hardcoded.
"""
from __future__ import annotations

import json
import logging

from django.conf import settings

from .provider import LLMProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(self):
        from openai import OpenAI

        self._client = OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            max_retries=3,
        )
        self._model = (
            settings.LLM_FREE_MODEL if settings.USE_FREE_LLM else settings.LLM_MODEL
        )
        self._headers = {
            "HTTP-Referer": "https://resumeforge.local",
            "X-Title": "Rezoom",
        }

    def complete(self, messages, *, temperature=0.4, max_tokens=800,
                 task=None, context=None) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=self._headers,
        )
        return (resp.choices[0].message.content or "").strip()

    def structured(self, messages, schema, *, temperature=0.2,
                   task=None, context=None, strict=True) -> dict:
        # Strict json_schema mode only works reliably when the schema is fully
        # closed (every property required, additionalProperties:false). For loose
        # schemas (resume structuring) we use plain JSON-object mode and validate
        # ourselves; otherwise the model tends to return only a tiny subset of
        # fields. ``strict=False`` selects json_object mode.
        if strict and schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "result", "strict": True, "schema": schema},
            }
            extra_body = {"provider": {"require_parameters": True}}
        else:
            response_format = {"type": "json_object"}
            extra_body = None

        kwargs = dict(
            model=self._model,
            messages=messages,
            temperature=temperature,
            response_format=response_format,
            extra_headers=self._headers,
        )
        if extra_body is not None:
            kwargs["extra_body"] = extra_body

        resp = self._client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or "{}"
        return _parse_json(content)


def _parse_json(content: str) -> dict:
    """Parse a model's JSON reply, tolerating ```json fences and leading prose."""
    text = (content or "").strip()
    if text.startswith("```"):
        # Strip a leading ```json / ``` fence and trailing ```
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last resort: grab the outermost {...} block.
        start, end = text.find("{"), text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        logger.warning("OpenRouter returned non-JSON; returning empty dict")
        return {}

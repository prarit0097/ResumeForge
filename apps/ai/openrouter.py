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
            "X-Title": "ResumeForge",
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
                   task=None, context=None) -> dict:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "result", "strict": True, "schema": schema},
            },
            extra_headers=self._headers,
            extra_body={"provider": {"require_parameters": True}},
        )
        content = resp.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("OpenRouter returned non-JSON; returning empty dict")
            return {}

"""Swappable LLM provider. OpenRouter (DeepSeek) when a key is configured,
otherwise a deterministic offline Mock so the whole app works without a key."""
from __future__ import annotations

import abc

from django.conf import settings


class LLMProvider(abc.ABC):
    """Minimal interface every provider implements."""

    name = "base"

    @abc.abstractmethod
    def complete(self, messages: list[dict], *, temperature: float = 0.4,
                 max_tokens: int = 800, task: str | None = None,
                 context: dict | None = None) -> str:
        """Return a plain-text completion for a chat-style message list.

        ``task``/``context`` are hints the offline Mock uses to produce useful
        deterministic output; the real OpenRouter provider ignores them."""

    @abc.abstractmethod
    def structured(self, messages: list[dict], schema: dict, *,
                   temperature: float = 0.2, task: str | None = None,
                   context: dict | None = None) -> dict:
        """Return a JSON object conforming to ``schema``."""


def is_demo_mode() -> bool:
    """True when no API key is configured (Mock provider in use)."""
    return not bool(getattr(settings, "OPENROUTER_API_KEY", ""))


_cached: LLMProvider | None = None


def get_provider() -> LLMProvider:
    """Return the active provider (cached). OpenRouter if key set, else Mock."""
    global _cached
    if _cached is not None:
        return _cached
    if is_demo_mode():
        from .mock import MockProvider

        _cached = MockProvider()
    else:
        from .openrouter import OpenRouterProvider

        _cached = OpenRouterProvider()
    return _cached


def reset_provider_cache() -> None:
    """Test hook: clear the cached provider (e.g. after changing settings)."""
    global _cached
    _cached = None

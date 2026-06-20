"""Tests for the AI provider abstraction and Mock provider."""
from apps.ai import provider, services
from apps.ai.mock import MockProvider


def test_demo_mode_uses_mock(settings):
    settings.OPENROUTER_API_KEY = ""
    provider.reset_provider_cache()
    assert provider.is_demo_mode()
    assert isinstance(provider.get_provider(), MockProvider)
    provider.reset_provider_cache()


def test_improve_text_adds_metric_and_verb():
    out = services.improve_text("worked on the payments system")
    assert out
    assert any(ch.isdigit() for ch in out)  # a metric was injected


def test_generate_bullets_returns_list():
    bullets = services.generate_bullets({"position": "Engineer", "company": "Acme"})
    assert isinstance(bullets, list) and len(bullets) >= 1
    assert all(isinstance(b, str) and b for b in bullets)


def test_mock_structured_keywords():
    result = MockProvider().structured([], {}, task="extract_keywords",
                                       context={"jd": "Python and Django engineer"})
    assert "hard" in result


def test_cover_letter_mentions_role():
    out = services.generate_cover_letter({"name": "Jane", "target_role": "Designer"})
    assert "Designer" in out
    assert "Jane" in out

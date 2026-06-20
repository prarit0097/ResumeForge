"""Template context processor exposing whether AI is in offline demo mode."""
from django.conf import settings


def demo_mode(request):
    key = getattr(settings, "OPENROUTER_API_KEY", "")
    return {"ai_demo_mode": not bool(key)}

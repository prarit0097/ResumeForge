"""Template context processors: AI demo-mode flag + a static-asset cache buster."""
import time

from django.conf import settings

# Changes every server start so browsers always fetch fresh JS/CSS in dev
# (prevents the "I fixed it but the browser shows the old version" problem).
_ASSET_VERSION = str(int(time.time()))


def demo_mode(request):
    key = getattr(settings, "OPENROUTER_API_KEY", "")
    version = getattr(settings, "ASSET_VERSION", _ASSET_VERSION)
    return {"ai_demo_mode": not bool(key), "ASSET_VERSION": version}

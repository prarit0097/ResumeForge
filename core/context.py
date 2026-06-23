"""Template context for analytics + SEO. Driven by env so production-only."""
from django.conf import settings

# Resume pages carry the secret edit-token in the URL; analytics must not run
# there (and we strip the query string in gtag anyway as defence in depth).
_PII_PREFIXES = ("/r/", "/drafts")


def site(request):
    ga = getattr(settings, "GA_MEASUREMENT_ID", "")
    on_pii_page = request.path.startswith(_PII_PREFIXES)
    return {
        # Loaded on every page for full traffic data; gtag (in base.html) masks
        # the resume id and strips the ?t= token query so nothing private leaks.
        "GA_MEASUREMENT_ID": ga,
        "SITE_URL": getattr(settings, "SITE_URL", "").rstrip("/"),
        "INDEXABLE": not on_pii_page,
    }

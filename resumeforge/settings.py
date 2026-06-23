"""Django settings for ResumeForge."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    OPENROUTER_API_KEY=(str, ""),
    LLM_MODEL=(str, "deepseek/deepseek-v4-flash"),
    LLM_FREE_MODEL=(str, "deepseek/deepseek-chat-v3-0324:free"),
    USE_FREE_LLM=(bool, False),
    GA_MEASUREMENT_ID=(str, ""),   # Google Analytics 4 ID, e.g. G-XXXXXXXXXX
    SITE_URL=(str, ""),            # e.g. https://resume.yourdomain.com (for canonical/OG)
    GOOGLE_SITE_VERIFICATION=(str, ""),  # Search Console HTML-tag verification token
)

# Read .env if present (never required; app works without it).
env_file = BASE_DIR / ".env"
if env_file.exists():
    env.read_env(str(env_file))

DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
# Required for CSRF on POST forms when served behind a domain over HTTPS.
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# In production a real SECRET_KEY is mandatory. In DEBUG we generate an
# ephemeral one so local dev needs no config — but never ship a known key.
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        from django.core.management.utils import get_random_secret_key

        SECRET_KEY = get_random_secret_key()
    else:
        raise RuntimeError("SECRET_KEY must be set in production (set it in .env).")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    "apps.resumes",
    "apps.builder",
    "apps.parsing",
    "apps.ai",
    "apps.ats",
    "apps.templates_engine",
    "apps.exporting",
    "apps.coverletters",
    "apps.blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static files in production
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.PrivacyHeadersMiddleware",
]

ROOT_URLCONF = "resumeforge.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "apps.ai.context.demo_mode",
                "core.context.site",
            ],
        },
    },
]

WSGI_APPLICATION = "resumeforge.wsgi.application"
ASGI_APPLICATION = "resumeforge.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# No user accounts -> no auth/admin apps. Session identifies a device's drafts.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SAMESITE = "Lax"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise serves static files directly from the app (no separate nginx static
# config needed). In production it compresses + hashes filenames (cache-busting);
# in dev the plain storage avoids needing collectstatic.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Analytics / SEO (env-driven; empty in dev so nothing loads).
GA_MEASUREMENT_ID = env("GA_MEASUREMENT_ID")
SITE_URL = env("SITE_URL")
GOOGLE_SITE_VERIFICATION = env("GOOGLE_SITE_VERIFICATION")

# --- ResumeForge / LLM config ---
OPENROUTER_API_KEY = env("OPENROUTER_API_KEY")
LLM_MODEL = env("LLM_MODEL")
LLM_FREE_MODEL = env("LLM_FREE_MODEL")
USE_FREE_LLM = env("USE_FREE_LLM")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Upload limits for resume parsing (bytes).
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_UPLOAD_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# Security headers. The TLS-dependent ones only activate outside DEBUG so local
# HTTP development still works.
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Hash + compress static filenames for far-future caching behind WhiteNoise.
    STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

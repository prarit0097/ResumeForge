"""Django settings for ResumeForge."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    OPENROUTER_API_KEY=(str, ""),
    LLM_MODEL=(str, "deepseek/deepseek-chat-v3-0324"),
    LLM_FREE_MODEL=(str, "deepseek/deepseek-chat-v3-0324:free"),
    USE_FREE_LLM=(bool, False),
)

# Read .env if present (never required; app works without it).
env_file = BASE_DIR / ".env"
if env_file.exists():
    env.read_env(str(env_file))

DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

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
    "apps.resumes",
    "apps.builder",
    "apps.parsing",
    "apps.ai",
    "apps.ats",
    "apps.templates_engine",
    "apps.exporting",
    "apps.coverletters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

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

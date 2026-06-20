"""Django settings for ResumeForge."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "dev-insecure-key-change-in-production"),
    ALLOWED_HOSTS=(list, ["*"]),
    OPENROUTER_API_KEY=(str, ""),
    LLM_MODEL=(str, "deepseek/deepseek-chat-v3-0324"),
    LLM_FREE_MODEL=(str, "deepseek/deepseek-chat-v3-0324:free"),
    USE_FREE_LLM=(bool, False),
)

# Read .env if present (never required; app works without it).
env_file = BASE_DIR / ".env"
if env_file.exists():
    env.read_env(str(env_file))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

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

# Security headers tightened in production via env.
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

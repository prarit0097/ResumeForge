"""Root URL configuration for ResumeForge."""
from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
    path("", include("apps.builder.urls")),
    path("", include("apps.resumes.urls")),
    path("", include("apps.templates_engine.urls")),
    path("ai/", include("apps.ai.urls")),
    path("ats/", include("apps.ats.urls")),
    path("", include("apps.parsing.urls")),
    path("", include("apps.exporting.urls")),
    path("", include("apps.coverletters.urls")),
]

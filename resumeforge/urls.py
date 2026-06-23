"""Root URL configuration for ResumeForge."""
from django.urls import include, path

from core import seo

urlpatterns = [
    path("robots.txt", seo.robots_txt),
    path("sitemap.xml", seo.sitemap_xml),
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

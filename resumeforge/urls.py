"""Root URL configuration for ResumeForge (product: Rezoom)."""
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core import seo

urlpatterns = [
    path("robots.txt", seo.robots_txt),
    path("sitemap.xml", sitemap, {"sitemaps": seo.SITEMAPS}, name="sitemap"),
    path("", include("core.urls")),
    path("", include("apps.builder.urls")),
    path("", include("apps.resumes.urls")),
    path("", include("apps.templates_engine.urls")),
    path("ai/", include("apps.ai.urls")),
    path("ats/", include("apps.ats.urls")),
    path("", include("apps.parsing.urls")),
    path("", include("apps.exporting.urls")),
    path("", include("apps.coverletters.urls")),
    path("", include("apps.blog.urls")),
]

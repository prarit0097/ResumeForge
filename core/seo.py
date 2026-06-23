"""SEO endpoints: robots.txt + sitemaps (via Django's sitemap framework).

Public, indexable pages live in StaticPagesSitemap; blog posts in BlogSitemap.
Resume/draft pages and the POST API namespaces are kept out of the index (they
carry PII or aren't content).
"""
from __future__ import annotations

from datetime import date

from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.urls import reverse

_DISALLOW = ["/r/", "/drafts", "/ai/", "/ats/", "/new/"]
# Bumped when the static marketing pages meaningfully change.
_STATIC_LASTMOD = date(2026, 6, 24)


def robots_txt(request):
    base = f"{request.scheme}://{request.get_host()}"
    lines = ["User-agent: *", "Allow: /"]
    lines += [f"Disallow: {p}" for p in _DISALLOW]
    lines += ["", f"Sitemap: {base}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain")


class StaticPagesSitemap(Sitemap):
    """Indexable marketing/content pages (auto lastmod via the framework)."""

    protocol = "https"
    changefreq = "weekly"

    def items(self) -> list[str]:
        return [
            "core:landing",
            "core:ats_checker",
            "core:resume_templates",
            "parsing:upload",
            "blog:index",
        ]

    def location(self, item: str) -> str:
        return reverse(item)

    def priority(self, item: str) -> float:
        return 1.0 if item == "core:landing" else 0.8

    def lastmod(self, item: str) -> date:
        return _STATIC_LASTMOD


class BlogSitemap(Sitemap):
    """One entry per published blog post, with its real lastmod."""

    protocol = "https"
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        from apps.blog.registry import POSTS

        return POSTS

    def location(self, post) -> str:
        return reverse("blog:post", args=[post.slug])

    def lastmod(self, post):
        return post.updated


SITEMAPS = {"static": StaticPagesSitemap, "blog": BlogSitemap}

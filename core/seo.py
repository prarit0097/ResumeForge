"""SEO endpoints: robots.txt and sitemap.xml (no extra apps needed).

Public, indexable pages are listed in PUBLIC_PAGES. Resume/draft pages and the
POST API namespaces are kept out of the index (they carry PII or aren't content).
"""
from __future__ import annotations

from django.http import HttpResponse
from django.urls import reverse
from django.utils.timezone import now

# (url-name, changefreq, priority) for indexable marketing/content pages.
PUBLIC_PAGES = [
    ("core:landing", "weekly", "1.0"),
    ("core:ats_checker", "weekly", "0.9"),
    ("core:resume_templates", "weekly", "0.8"),
    ("parsing:upload", "weekly", "0.8"),
]

_DISALLOW = ["/r/", "/drafts", "/ai/", "/ats/", "/new/"]


def _base(request) -> str:
    return f"{request.scheme}://{request.get_host()}"


def robots_txt(request):
    base = _base(request)
    lines = ["User-agent: *", "Allow: /"]
    lines += [f"Disallow: {p}" for p in _DISALLOW]
    lines += ["", f"Sitemap: {base}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request):
    base = _base(request)
    today = now().date().isoformat()
    urls = []
    for name, changefreq, priority in PUBLIC_PAGES:
        try:
            loc = base + reverse(name)
        except Exception:  # noqa: BLE001 - skip any page not wired yet
            continue
        urls.append(
            f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod>"
            f"<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return HttpResponse(xml, content_type="application/xml")

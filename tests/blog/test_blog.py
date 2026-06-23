"""Blog: index, post rendering, 404, schema, and sitemap inclusion."""
import pytest
from django.urls import reverse

from apps.blog.registry import POSTS

pytestmark = pytest.mark.django_db


def test_blog_index_lists_every_post(client):
    resp = client.get(reverse("blog:index"))
    assert resp.status_code == 200
    assert len(POSTS) >= 4
    for post in POSTS:
        assert post.slug.encode() in resp.content


def test_blog_post_renders_with_schema(client):
    post = POSTS[0]
    resp = client.get(reverse("blog:post", args=[post.slug]))
    assert resp.status_code == 200
    assert post.title.encode() in resp.content
    assert b'"@type":"Article"' in resp.content
    assert b'"@type":"BreadcrumbList"' in resp.content
    assert b'property="og:type" content="article"' in resp.content


def test_unknown_slug_returns_404(client):
    assert client.get("/blog/does-not-exist/").status_code == 404


def test_sitemap_includes_every_post(client):
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert b"/blog/" in resp.content
    for post in POSTS:
        assert f"/blog/{post.slug}/".encode() in resp.content


def test_posts_loaded_and_rendered():
    slugs = {p.slug for p in POSTS}
    assert "ats-friendly-resume-format" in slugs
    assert all(p.html and p.title and p.description for p in POSTS)

"""Blog index + post pages (read-only, file-backed)."""
from django.http import Http404
from django.shortcuts import render

from .registry import BY_SLUG, POSTS


def blog_index(request):
    return render(request, "blog/index.html", {"posts": POSTS})


def blog_post(request, slug: str):
    post = BY_SLUG.get(slug)
    if post is None:
        raise Http404("No such post")
    return render(request, "blog/post.html", {"post": post})

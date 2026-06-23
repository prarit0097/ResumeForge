"""File-based blog. Posts are Markdown files in content/, parsed once at import.

No DB, no admin — fits the no-login architecture. Drop a new `.md` file in
content/ (with the frontmatter below) and it shows up automatically:

    ---
    title: "Post title (also the <h1>)"
    slug: post-url-slug
    target_keyword: primary keyword
    meta_description: "Under ~155 chars."
    date: "2026-06-24"
    ---
    # Post title
    Body in Markdown…
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import markdown

logger = logging.getLogger(__name__)

CONTENT_DIR = Path(__file__).resolve().parent / "content"
_WORDS_PER_MIN = 200
_DEFAULT_DATE = date(2026, 6, 24)
_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
_LEADING_H1 = re.compile(r"^\s*#\s+[^\n]*\n")


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    description: str
    keyword: str
    published: date
    updated: date
    read_min: int
    html: str


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    raw, body = match.group(1), match.group(2)
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body


def _read_minutes(body: str) -> int:
    return max(1, round(len(re.findall(r"\w+", body)) / _WORDS_PER_MIN))


def _parse_date(value: str, fallback: date) -> date:
    try:
        year, month, day = (int(part) for part in value.split("-"))
        return date(year, month, day)
    except (ValueError, AttributeError):
        return fallback


def _load_one(path: Path, renderer: markdown.Markdown) -> Post:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    meta, body = _parse_frontmatter(text)
    body = _LEADING_H1.sub("", body, count=1).strip()  # H1 is rendered by the wrapper
    renderer.reset()
    published = _parse_date(meta.get("date", ""), _DEFAULT_DATE)
    return Post(
        slug=meta.get("slug", path.stem),
        title=meta.get("title", path.stem),
        description=meta.get("meta_description", ""),
        keyword=meta.get("target_keyword", ""),
        published=published,
        updated=_parse_date(meta.get("updated", ""), published),
        read_min=_read_minutes(body),
        html=renderer.convert(body),
    )


def _load() -> list[Post]:
    """Load every post. One bad file is skipped (logged), never crashes startup."""
    if not CONTENT_DIR.is_dir():
        logger.error("Blog content dir missing: %s", CONTENT_DIR)
        return []
    renderer = markdown.Markdown(extensions=["extra", "sane_lists"])
    posts: list[Post] = []
    seen: set[str] = set()
    for path in sorted(CONTENT_DIR.glob("*.md")):
        try:
            post = _load_one(path, renderer)
        except Exception:  # noqa: BLE001 - one bad file must not take down the blog
            logger.exception("Failed to load blog post: %s", path)
            continue
        if post.slug in seen:
            logger.warning("Duplicate blog slug %r (%s) — keeping the first", post.slug, path.name)
            continue
        seen.add(post.slug)
        posts.append(post)
    posts.sort(key=lambda post: post.published, reverse=True)
    return posts


POSTS: list[Post] = _load()
BY_SLUG: dict[str, Post] = {post.slug: post for post in POSTS}

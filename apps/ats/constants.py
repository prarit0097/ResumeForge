"""Shared ATS constants: canonical headings, strong action verbs, stopwords."""
from __future__ import annotations

# Headings ATS parsers reliably recognize. We render these exact labels.
CANONICAL_HEADINGS = {
    "summary", "work experience", "experience", "education", "skills",
    "projects", "certifications", "awards", "languages",
}

STRONG_ACTION_VERBS = {
    "led", "built", "delivered", "improved", "designed", "launched", "drove",
    "optimized", "scaled", "owned", "created", "developed", "managed",
    "increased", "reduced", "achieved", "implemented", "automated", "spearheaded",
    "negotiated", "streamlined", "accelerated", "generated", "directed",
    "established", "engineered", "orchestrated", "transformed", "mentored",
    "analyzed", "architected", "boosted", "cut", "grew", "shipped",
    # additional legitimate strong/leadership verbs
    "oversaw", "supervised", "coordinated", "executed", "championed", "pioneered",
    "headed", "founded", "modernized", "consolidated", "formulated", "devised",
    "facilitated", "expanded", "exceeded", "secured", "partnered", "drove",
    "produced", "introduced", "revamped", "redesigned", "enabled", "maximized",
    "minimized", "resolved", "elevated", "advanced", "guided", "directed",
    "supported", "enhanced", "maintained", "led",
}

WEAK_OPENERS = {
    "responsible", "worked", "helped", "assisted", "involved", "participated",
    "tasked", "duties", "handled",
}

STOPWORDS = {
    "and", "the", "for", "with", "you", "our", "are", "will", "this", "that",
    "have", "from", "your", "who", "all", "but", "not", "can", "has", "was",
    "their", "they", "them", "its", "into", "out", "more", "than", "such",
    "a", "an", "to", "of", "in", "on", "at", "as", "is", "be", "or", "we",
}

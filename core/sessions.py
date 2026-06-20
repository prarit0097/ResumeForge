"""Helpers for the no-login session that indexes 'drafts on this device'."""
from __future__ import annotations


def ensure_session_key(request) -> str:
    """Guarantee the request has a session key and return it."""
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key

"""Resume data schema (JSON Resume aligned) + validation + canonical empty doc.

The resume content is stored as JSON in ``Resume.data``. We validate at the
system boundary (autosave, parsing) before persisting. Validation is lenient
about *missing* keys (drafts are incomplete by nature) but strict about
*types* so downstream renderers and scorers can trust the shape.
"""
from __future__ import annotations

from copy import deepcopy

import jsonschema

# Canonical empty resume. Every section present so the editor/renderer never
# KeyErrors on a fresh draft.
_EMPTY: dict = {
    "basics": {
        "name": "",
        "label": "",
        "email": "",
        "phone": "",
        "location": "",
        "url": "",
        "summary": "",
        "profiles": [],
    },
    "work": [],
    "education": [],
    "skills": [],
    "projects": [],
    "certifications": [],
    "awards": [],
    "languages": [],
    "volunteer": [],
    "custom": [],
}

# JSON Schema used for type validation. additionalProperties is allowed so we
# can evolve without breaking old drafts, but known fields are type-checked.
RESUME_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "basics": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "label": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "location": {"type": "string"},
                "url": {"type": "string"},
                "summary": {"type": "string"},
                "profiles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "network": {"type": "string"},
                            "url": {"type": "string"},
                        },
                    },
                },
            },
        },
        "work": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "position": {"type": "string"},
                    "location": {"type": "string"},
                    "startDate": {"type": "string"},
                    "endDate": {"type": "string"},
                    "current": {"type": "boolean"},
                    "summary": {"type": "string"},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "institution": {"type": "string"},
                    "area": {"type": "string"},
                    "studyType": {"type": "string"},
                    "startDate": {"type": "string"},
                    "endDate": {"type": "string"},
                    "score": {"type": "string"},
                    "courses": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "level": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "url": {"type": "string"},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "issuer": {"type": "string"},
                    "date": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
        },
        "awards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {"type": "string"},
                    "awarder": {"type": "string"},
                    "summary": {"type": "string"},
                },
            },
        },
        "languages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "language": {"type": "string"},
                    "fluency": {"type": "string"},
                },
            },
        },
        "volunteer": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "organization": {"type": "string"},
                    "position": {"type": "string"},
                    "summary": {"type": "string"},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "custom": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "items": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}

_VALIDATOR = jsonschema.Draft202012Validator(RESUME_SCHEMA)


def empty_resume() -> dict:
    """Return a fresh, fully-formed empty resume document."""
    return deepcopy(_EMPTY)


def validate_resume_data(data: object) -> list[str]:
    """Validate a resume data dict. Returns a list of error strings
    (empty list == valid)."""
    if not isinstance(data, dict):
        return ["Resume data must be a JSON object."]
    errors = sorted(_VALIDATOR.iter_errors(data), key=lambda e: list(e.path))
    return [f"{'/'.join(str(p) for p in e.path) or 'root'}: {e.message}" for e in errors]


def merge_into_resume(base: dict, incoming: dict) -> dict:
    """Return a NEW dict: base with top-level resume sections replaced by
    incoming sections. Immutable-style (never mutates inputs)."""
    result = deepcopy(base) if base else empty_resume()
    for key, value in (incoming or {}).items():
        result[key] = deepcopy(value)
    return result

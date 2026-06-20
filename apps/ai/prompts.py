"""Prompt builders. Shared rules keep AI honest: never invent experience,
quantify where possible, keep the candidate's voice, ATS-friendly phrasing."""
from __future__ import annotations

SYSTEM_WRITER = (
    "You are an expert resume writer and ATS optimization specialist. "
    "Rules you must always follow: never invent facts, employers, or metrics "
    "the user did not provide; preserve the candidate's authentic voice; "
    "prefer strong action verbs and quantified results; keep language concise "
    "and ATS-friendly (no tables, emojis, or special characters); never keyword "
    "stuff."
)


def improve_text_messages(text: str, kind: str = "bullet") -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_WRITER},
        {"role": "user", "content": (
            f"Improve this resume {kind}. Make it a single strong, concise line "
            f"with an action verb and a quantified result if one is implied. "
            f"Return only the improved text, no quotes:\n\n{text}"
        )},
    ]


def summary_messages(context: dict) -> list[dict]:
    role = context.get("target_role") or context.get("label") or "the candidate's field"
    return [
        {"role": "system", "content": SYSTEM_WRITER},
        {"role": "user", "content": (
            f"Write a 2-3 sentence professional summary for a {role}. "
            f"Base it only on this context and do not invent specifics:\n{context}"
        )},
    ]


def bullets_messages(context: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_WRITER},
        {"role": "user", "content": (
            f"Generate 3 strong resume bullet points for this role. Each starts "
            f"with an action verb and includes a plausible quantified result the "
            f"user can edit. Role context: {context}. Return JSON {{'bullets': [..]}}."
        )},
    ]


def tailor_messages(text: str, jd: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_WRITER},
        {"role": "user", "content": (
            "Rewrite the following resume text to better match this job "
            "description, weaving in genuinely relevant keywords WITHOUT inventing "
            "experience or stuffing. Return only the rewritten text.\n\n"
            f"JOB DESCRIPTION:\n{jd}\n\nRESUME TEXT:\n{text}"
        )},
    ]


def cover_letter_messages(context: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_WRITER},
        {"role": "user", "content": (
            "Write a concise, specific cover letter (under 250 words) for this "
            "candidate and job. Use only provided facts. Context:\n"
            f"{context}"
        )},
    ]


_STRUCTURE_TARGET_SHAPE = (
    "{\n"
    '  "basics": {"name": "", "label": "", "email": "", "phone": "", '
    '"location": "", "url": "", "summary": "", '
    '"profiles": [{"network": "", "url": ""}]},\n'
    '  "work": [{"company": "", "position": "", "location": "", '
    '"startDate": "YYYY-MM", "endDate": "YYYY-MM", "current": false, '
    '"summary": "", "highlights": ["..."]}],\n'
    '  "education": [{"institution": "", "area": "", "studyType": "", '
    '"startDate": "YYYY-MM", "endDate": "YYYY-MM", "score": ""}],\n'
    '  "skills": [{"name": "", "keywords": ["..."]}],\n'
    '  "projects": [{"name": "", "description": "", "highlights": ["..."]}],\n'
    '  "certifications": [{"name": "", "issuer": "", "date": "YYYY-MM"}],\n'
    '  "awards": [{"title": "", "date": "YYYY-MM", "awarder": ""}],\n'
    '  "languages": [{"language": "", "fluency": ""}]\n'
    "}"
)

_STRUCTURE_EXAMPLE = (
    "Example input:\n"
    "Jane Doe\n"
    "Senior Engineer | jane@x.com | +1 555 0100\n"
    "Summary\nBuilds reliable payment systems.\n"
    "Experience\n"
    "Senior Engineer - Acme  Jan 2021 - Present\n"
    "- Cut latency 40%\n"
    "Skills\nPython, Django, AWS\n\n"
    "Example output:\n"
    '{"basics": {"name": "Jane Doe", "label": "Senior Engineer", '
    '"email": "jane@x.com", "phone": "+1 555 0100", '
    '"summary": "Builds reliable payment systems."}, '
    '"work": [{"company": "Acme", "position": "Senior Engineer", '
    '"startDate": "2021-01", "current": true, '
    '"highlights": ["Cut latency 40%"]}], '
    '"skills": [{"name": "Skills", "keywords": ["Python", "Django", "AWS"]}]}'
)


def structure_messages(raw: str) -> list[dict]:
    return [
        {"role": "system", "content": (
            "You convert raw resume text into a single JSON object using the "
            "JSON Resume shape. Extract EVERY field that is present in the text: "
            "the candidate's name (it is almost always the first non-empty line "
            "at the top of the resume), label/title, email, phone, location, "
            "links, a professional summary, ALL work experience entries (with "
            "company, position, dates and every bullet under each job as a "
            "highlight), all education, all skills (group skill keywords), all "
            "projects, certifications, awards and languages. "
            "Never invent facts, employers, dates or metrics that are not in the "
            "text. Use empty string \"\" or empty array [] for anything missing, "
            "never omit a section key. Normalize all dates to YYYY-MM (or YYYY "
            "if only a year is given); use current:true and an empty endDate for "
            "ongoing roles. Return ONLY the JSON object, no prose, no markdown. "
            "The JSON's TOP-LEVEL keys must be basics, work, education, skills, etc. "
            "Do NOT wrap the result in an outer key like \"resume\" or \"data\".\n\n"
            "Target JSON shape (fill in real values, keep these keys):\n"
            f"{_STRUCTURE_TARGET_SHAPE}\n\n"
            f"{_STRUCTURE_EXAMPLE}"
        )},
        {"role": "user", "content": f"Resume text to convert:\n\n{raw}"},
    ]


def prompt_edit_messages(text: str, instruction: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_WRITER},
        {"role": "user", "content": (
            f"Apply this instruction to the resume text and return only the "
            f"result.\n\nINSTRUCTION: {instruction}\n\nTEXT:\n{text}"
        )},
    ]

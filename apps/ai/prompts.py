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


def structure_messages(raw: str) -> list[dict]:
    return [
        {"role": "system", "content": (
            "You convert raw resume text into structured JSON Resume data. "
            "Extract only what is present; never invent. Use null/empty for "
            "missing fields. Normalize dates to YYYY-MM."
        )},
        {"role": "user", "content": f"Resume text:\n\n{raw}"},
    ]


def prompt_edit_messages(text: str, instruction: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_WRITER},
        {"role": "user", "content": (
            f"Apply this instruction to the resume text and return only the "
            f"result.\n\nINSTRUCTION: {instruction}\n\nTEXT:\n{text}"
        )},
    ]

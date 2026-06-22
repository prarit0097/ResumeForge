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


_JD_TAILOR_CLAUSE = (
    "\n\nA TARGET JOB DESCRIPTION is provided at the end. AGGRESSIVELY TAILOR ONLY "
    "the \"enhanced\" version so a recruiter or interviewer reading it immediately "
    "feels this candidate is a strong, obvious fit for THIS exact job — while "
    "staying truthful (reframe real experience; NEVER invent employers, job "
    "titles, degrees, tools, certifications or metrics that aren't there). Do ALL "
    "of the following in the enhanced resume:\n"
    "1. HEADLINE (basics.label): set it to the JD's target role / title, clean and "
    "aligned. Drop unrelated specializations — e.g. for a Python Developer job use "
    "'Python Developer' (optionally with 1-2 directly relevant tags like 'Backend "
    "| Automation'), NOT a sales-flavoured mashup.\n"
    "2. SUMMARY: 2-3 sentences that position the candidate squarely for THIS role, "
    "leading with their most relevant qualifications and mirroring the JD's core "
    "language and must-have requirements.\n"
    "3. EXPERIENCE ORDER: KEEP the roles in their existing reverse-chronological "
    "order — do NOT move an older role above a newer one (a jumbled timeline reads "
    "as manipulation). Within EACH role you MAY reorder the highlights so the most "
    "JD-relevant genuine bullet comes first.\n"
    "4. BULLETS: rewrite highlights to emphasize the parts of each real role that "
    "genuinely map to the JD, using the JD's terminology ONLY where the work truly "
    "involved it. For the candidate's genuinely relevant role(s) (e.g. an actual "
    "developer role for a developer JD), add honest specificity. For unrelated "
    "roles, surface the JD's SOFT requirements they really demonstrate "
    "(communication, cross-functional collaboration, problem-solving, "
    "remote/distributed coordination, process improvement, data/reporting).\n"
    "5. NO TECHNICAL-WASHING (critical, an interviewer will expose it): NEVER "
    "relabel a non-technical responsibility as technical. Do NOT insert words like "
    "'technical', 'engineering', 'systems', 'software', 'architecture' or "
    "'optimization' into a bullet for a role that was not technical (e.g. a sales / "
    "operations / call-center role stays sales/operations — you reframe it for "
    "leadership, communication, process and data, not for fake engineering work).\n"
    "6. SKILLS: build the skills section AROUND the JD, but list ONLY skills that "
    "trace to a real role or stated experience — put the JD's required/desired "
    "skills the candidate genuinely has FIRST. Do NOT invent skills (no "
    "'System Optimization', 'Remote Collaboration', a framework, etc. unless the "
    "candidate actually shows it).\n"
    "7. HONESTY OVER COVERAGE: if the candidate only partially fits the JD, "
    "emphasize every genuine overlap and transferable strength to the fullest — but "
    "never claim a seniority level, current job title, recency, or skill they never "
    "had. A resume that survives the interview beats one that looks perfect and "
    "collapses under one question. The \"original\" stays a faithful, untailored "
    "extraction."
)


def extract_and_enhance_messages(raw: str, jd: str | None = None) -> list[dict]:
    """One call that returns BOTH a faithful extraction and an ATS-improved
    version — halves latency vs structuring then enhancing separately. When a
    job description is given, the enhanced version is tailored to it."""
    user = f"Resume text:\n\n{raw}"
    if jd:
        user += f"\n\n--- TARGET JOB DESCRIPTION ---\n{jd}"
    return [
        {"role": "system", "content": (
            "You process a raw resume in ONE pass and return a JSON object with "
            "exactly two top-level keys: \"original\" and \"enhanced\".\n"
            "\"original\": a faithful extraction of the resume into the JSON Resume "
            "shape below — extract every field present, infer the name from the top "
            "line, normalize dates to YYYY-MM, never change wording, never invent.\n"
            "\"enhanced\": the SAME resume but ATS-improved. In the enhanced version: "
            "(a) rewrite the summary to be sharp and keyword-rich; (b) rewrite EVERY "
            "work/project highlight so it STARTS WITH A STRONG PAST-TENSE ACTION VERB "
            "(Led, Directed, Built, Drove, Increased, Streamlined, Spearheaded, "
            "Optimized, Delivered, etc.) — never start a bullet with weak words like "
            "'Contributed', 'Assisted', 'Helped', 'Responsible for', 'Worked on', "
            "'Oversaw' is fine; and include a quantified result whenever genuinely "
            "implied; (c) ALWAYS include a 'skills' section with 8-12 relevant skill "
            "keywords drawn from the candidate's titles, summary and experience "
            "(tools, methodologies, domains, competencies they clearly demonstrate — "
            "e.g. for a sales leader: Sales Strategy, Revenue Growth, Team Leadership, "
            "P&L Management, Business Development, CRM, Operations). Keep all companies, "
            "titles, dates and facts exactly; never invent employers, numbers or jobs.\n"
            "Both objects use these keys: basics{name,label,email,phone,location,url,"
            "summary,profiles[]}, work[{company,position,location,startDate,endDate,"
            "current,summary,highlights[]}], education[{institution,area,studyType,"
            "startDate,endDate,score}], skills[{name,keywords[]}], projects[{name,"
            "description,highlights[]}], certifications[{name,issuer,date}], awards[], "
            "languages[{language,fluency}]. Return ONLY the JSON object {\"original\":"
            "{...},\"enhanced\":{...}}, no prose, no markdown."
            + (_JD_TAILOR_CLAUSE if jd else "")
        )},
        {"role": "user", "content": user},
    ]


def enhance_messages(data: dict, jd: str | None = None) -> list[dict]:
    user = f"Resume JSON to improve:\n\n{data}"
    if jd:
        user += f"\n\n--- TARGET JOB DESCRIPTION (tailor toward this) ---\n{jd}"
    return [
        {"role": "system", "content": (
            "You are an expert ATS resume editor. You are given a resume as a JSON "
            "object. Return an IMPROVED version of the SAME JSON object with the "
            "SAME keys and structure. Improvements you must make: rewrite the "
            "'summary' to be sharp, specific and keyword-rich (2-3 sentences); "
            "rewrite every work and project 'highlights' bullet so it STARTS WITH A "
            "STRONG PAST-TENSE ACTION VERB (Led, Directed, Built, Drove, Increased, "
            "Streamlined, Optimized, Delivered…) — avoid weak openers (Contributed, "
            "Assisted, Helped, Responsible for, Worked on) — is concise, and includes "
            "a quantified result when genuinely implied. ALWAYS include a 'skills' "
            "section with 8-12 relevant skill keywords drawn from the candidate's "
            "titles, summary and experience (real competencies they demonstrate; "
            "never fabricate). Keep all companies, titles, dates, education and facts "
            "EXACTLY as given — never invent employers, numbers, or experience that is "
            "not implied. Do not add or remove jobs. Keep the same top-level keys "
            "(basics, work, education, skills, ...). Do NOT wrap the result in an "
            "outer key. Return ONLY the JSON object, no prose, no markdown."
            + (_JD_TAILOR_CLAUSE if jd else "")
        )},
        {"role": "user", "content": user},
    ]


def prompt_edit_messages(text: str, instruction: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_WRITER},
        {"role": "user", "content": (
            f"Apply this instruction to the resume text and return only the "
            f"result.\n\nINSTRUCTION: {instruction}\n\nTEXT:\n{text}"
        )},
    ]

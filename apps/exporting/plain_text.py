"""Plain-text rendering: 'what the ATS sees' + a TXT export option."""
from __future__ import annotations


def as_plain_text(data: dict) -> str:
    b = data.get("basics", {})
    lines: list[str] = []
    if b.get("name"):
        lines.append(b["name"])
    if b.get("label"):
        lines.append(b["label"])
    contact = " | ".join(filter(None, [b.get("email"), b.get("phone"), b.get("location"), b.get("url")]))
    if contact:
        lines.append(contact)
    if b.get("summary"):
        lines += ["", "SUMMARY", b["summary"]]

    if data.get("work"):
        lines += ["", "WORK EXPERIENCE"]
        for job in data["work"]:
            dates = f"{job.get('startDate', '')} - {'Present' if job.get('current') else job.get('endDate', '')}".strip(" -")
            header = " — ".join(filter(None, [job.get("position"), job.get("company")]))
            lines.append(f"{header}  {dates}".rstrip())
            for h in job.get("highlights") or []:
                if h.strip():
                    lines.append(f"- {h}")

    if data.get("education"):
        lines += ["", "EDUCATION"]
        for ed in data["education"]:
            deg = " in ".join(filter(None, [ed.get("studyType"), ed.get("area")]))
            lines.append(" — ".join(filter(None, [deg, ed.get("institution")])))

    if data.get("skills"):
        lines += ["", "SKILLS"]
        for s in data["skills"]:
            kws = ", ".join(s.get("keywords") or [])
            name = s.get("name", "")
            lines.append(f"{name}: {kws}" if name and kws else (name or kws))

    if data.get("certifications"):
        lines += ["", "CERTIFICATIONS"]
        for c in data["certifications"]:
            lines.append(" — ".join(filter(None, [c.get("name"), c.get("issuer"), c.get("date")])))

    return "\n".join(lines).strip() + "\n"

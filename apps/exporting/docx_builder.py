"""ATS-clean DOCX export built programmatically with python-docx.

ATS-safety by construction: single column, no tables, no text boxes, standard
fonts and heading styles, contact info inline in the body.
"""
from __future__ import annotations

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor


def _add_heading(doc, text: str, color: RGBColor) -> None:
    p = doc.add_paragraph()
    p.space_before = Pt(8)
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = color
    p.paragraph_format.space_after = Pt(2)


def build_docx(data: dict, accent_hex: str = "4f46e5") -> bytes:
    accent = RGBColor.from_string(accent_hex.lstrip("#"))
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    b = data.get("basics", {})

    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    name_run = name_p.add_run(b.get("name") or "Your Name")
    name_run.bold = True
    name_run.font.size = Pt(20)

    if b.get("label"):
        lp = doc.add_paragraph()
        lr = lp.add_run(b["label"])
        lr.font.size = Pt(11)
        lr.font.color.rgb = accent

    contact = "  |  ".join(filter(None, [
        b.get("email"), b.get("phone"), b.get("location"), b.get("url"),
    ]))
    if contact:
        cp = doc.add_paragraph()
        cr = cp.add_run(contact)
        cr.font.size = Pt(9)

    if b.get("summary"):
        _add_heading(doc, "Summary", accent)
        doc.add_paragraph(b["summary"])

    if data.get("work"):
        _add_heading(doc, "Work Experience", accent)
        for job in data["work"]:
            p = doc.add_paragraph()
            title = " — ".join(filter(None, [job.get("position"), job.get("company")]))
            run = p.add_run(title)
            run.bold = True
            dates = f"{job.get('startDate', '')} – {'Present' if job.get('current') else job.get('endDate', '')}".strip(" –")
            if dates:
                p.add_run(f"   {dates}").font.size = Pt(9)
            for h in job.get("highlights") or []:
                if h.strip():
                    doc.add_paragraph(h, style="List Bullet")

    if data.get("projects"):
        _add_heading(doc, "Projects", accent)
        for pr in data["projects"]:
            p = doc.add_paragraph()
            p.add_run(pr.get("name", "")).bold = True
            if pr.get("description"):
                doc.add_paragraph(pr["description"])
            for h in pr.get("highlights") or []:
                if h.strip():
                    doc.add_paragraph(h, style="List Bullet")

    if data.get("education"):
        _add_heading(doc, "Education", accent)
        for ed in data["education"]:
            p = doc.add_paragraph()
            deg = " in ".join(filter(None, [ed.get("studyType"), ed.get("area")]))
            p.add_run(deg).bold = True
            tail = " — ".join(filter(None, [ed.get("institution"), ed.get("score")]))
            if tail:
                doc.add_paragraph(tail)

    if data.get("skills"):
        _add_heading(doc, "Skills", accent)
        for s in data["skills"]:
            kws = ", ".join(s.get("keywords") or [])
            name = s.get("name", "")
            line = f"{name}: {kws}" if name and kws else (name or kws)
            if line:
                doc.add_paragraph(line)

    if data.get("certifications"):
        _add_heading(doc, "Certifications", accent)
        for c in data["certifications"]:
            line = " — ".join(filter(None, [c.get("name"), c.get("issuer"), c.get("date")]))
            if line:
                doc.add_paragraph(line, style="List Bullet")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

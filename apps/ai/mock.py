"""Offline deterministic provider. Powers 'demo mode' and all tests.

It produces genuinely useful resume content via rule-based transforms keyed on
the ``task`` hint, so the app is fully usable before an API key is added.
"""
from __future__ import annotations

import re

from .provider import LLMProvider

ACTION_VERBS = [
    "Led", "Built", "Delivered", "Improved", "Designed", "Launched",
    "Drove", "Optimized", "Scaled", "Owned",
]


def _strip(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


class MockProvider(LLMProvider):
    name = "mock"

    def complete(self, messages, *, temperature=0.4, max_tokens=800,
                 task=None, context=None) -> str:
        context = context or {}
        user_text = _strip(messages[-1]["content"]) if messages else ""

        if task == "improve_text":
            return self._improve(user_text)
        if task == "write_summary":
            return self._summary(context)
        if task == "cover_letter":
            return self._cover_letter(context)
        if task == "prompt_edit":
            return self._improve(context.get("text", user_text))
        return self._improve(user_text)

    def structured(self, messages, schema, *, temperature=0.2,
                   task=None, context=None, strict=True) -> dict:
        context = context or {}
        if task == "generate_bullets":
            return {"bullets": self._bullets(context)}
        if task == "extract_keywords":
            return self._keywords(context.get("jd", ""))
        if task == "structure_resume":
            return self._structure(context.get("raw", ""))
        return {}

    # --- generators -------------------------------------------------------
    def _improve(self, text: str) -> str:
        text = _strip(text)
        if not text:
            return "Results-driven professional with a track record of measurable impact."
        # Ensure it starts with a strong action verb.
        first = text.split(" ", 1)[0].rstrip(",.")
        if first.capitalize() not in ACTION_VERBS and not first.endswith("ed"):
            text = f"Delivered {text[0].lower()}{text[1:]}"
        if not re.search(r"\d", text):
            text = text.rstrip(".") + ", improving key metrics by 20%."
        return text

    def _summary(self, context: dict) -> str:
        role = context.get("target_role") or context.get("label") or "professional"
        years = context.get("years") or "several"
        return (
            f"{role.title()} with {years} years of experience delivering measurable "
            f"results. Known for combining strong technical skills with clear "
            f"communication to ship work that moves business metrics."
        )

    def _bullets(self, context: dict) -> list[str]:
        role = context.get("position") or "the role"
        company = context.get("company") or "the company"
        return [
            f"Led key initiatives as {role} at {company}, improving delivery speed by 25%.",
            f"Collaborated cross-functionally to launch features used by 10,000+ users.",
            f"Optimized core processes, cutting costs by 15% year over year.",
        ]

    def _cover_letter(self, context: dict) -> str:
        name = context.get("name") or "the applicant"
        role = context.get("target_role") or "this role"
        return (
            f"Dear Hiring Manager,\n\nI am excited to apply for {role}. "
            f"My background aligns closely with what you're looking for, and I am "
            f"confident I can deliver measurable impact from day one.\n\n"
            f"In previous roles I have consistently driven results, improved key "
            f"metrics, and collaborated across teams to ship work that matters.\n\n"
            f"I would welcome the chance to discuss how I can contribute.\n\n"
            f"Sincerely,\n{name}"
        )

    def _keywords(self, jd: str) -> dict:
        words = re.findall(r"[A-Za-z][A-Za-z+#.]{2,}", jd or "")
        common = {"and", "the", "for", "with", "you", "our", "are", "will", "this",
                  "that", "have", "from", "your", "who", "all", "but", "not"}
        seen: list[str] = []
        for w in words:
            lw = w.lower()
            if lw not in common and w not in seen:
                seen.append(w)
        hard = seen[:12]
        title_match = re.search(r"(engineer|manager|designer|developer|analyst|scientist|lead)", jd or "", re.I)
        return {
            "hard": hard,
            "soft": ["communication", "teamwork", "problem solving"],
            "title": title_match.group(0).title() if title_match else "",
            "education": None,
        }

    def _structure(self, raw: str) -> dict:
        """Best-effort offline structuring.

        The real structuring uses the LLM; this deterministic heuristic parser
        handles the common single-column resume layout so demo mode and tests
        recover the major sections (contact, summary, experience, education,
        skills, projects) instead of just name + email.
        """
        from apps.resumes.schema import empty_resume

        data = empty_resume()
        lines = [l.rstrip() for l in (raw or "").splitlines()]
        nonblank = [l.strip() for l in lines if l.strip()]
        if not nonblank:
            return data

        # --- contact / basics -------------------------------------------------
        data["basics"]["name"] = nonblank[0][:80]
        email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw or "")
        if email:
            data["basics"]["email"] = email.group(0)
        phone = re.search(r"(\+?\d[\d\s().-]{7,}\d)", raw or "")
        if phone:
            data["basics"]["phone"] = phone.group(0).strip()

        sections = self._split_sections(lines)

        summary = sections.get("summary") or sections.get("objective") or sections.get("profile")
        if summary:
            data["basics"]["summary"] = " ".join(summary)[:600]

        work = self._parse_work(
            sections.get("experience") or sections.get("work experience")
            or sections.get("employment") or sections.get("work history") or [])
        if work:
            data["work"] = work

        edu = self._parse_education(
            sections.get("education") or sections.get("academic") or [])
        if edu:
            data["education"] = edu

        skills = self._parse_skills(
            sections.get("skills") or sections.get("technical skills")
            or sections.get("core skills") or [])
        if skills:
            data["skills"] = skills

        projects = self._parse_projects(sections.get("projects") or [])
        if projects:
            data["projects"] = projects

        # If no explicit summary heading, fall back to the lines just under the
        # contact block (old behaviour) so something useful still appears.
        if not data["basics"]["summary"] and len(nonblank) > 1:
            tail = [l for l in nonblank[1:4] if "@" not in l and not re.search(r"\d{3}", l)]
            if tail:
                data["basics"]["summary"] = " ".join(tail)[:400]
        return data

    # --- structuring helpers ------------------------------------------------
    _HEADINGS = {
        "summary", "objective", "profile", "experience", "work experience",
        "employment", "work history", "education", "academic", "skills",
        "technical skills", "core skills", "projects", "certifications",
        "awards", "languages", "interests", "volunteer",
    }

    def _is_heading(self, line: str) -> str | None:
        stripped = line.strip().rstrip(":").strip()
        if not stripped or len(stripped) > 40:
            return None
        low = stripped.lower()
        if low in self._HEADINGS:
            return low
        return None

    def _split_sections(self, lines: list[str]) -> dict:
        """Group raw lines under their (lowercased) heading."""
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for line in lines:
            heading = self._is_heading(line)
            if heading is not None:
                current = heading
                sections.setdefault(current, [])
                continue
            if current is not None and line.strip():
                sections[current].append(line.strip())
        return sections

    @staticmethod
    def _is_bullet(line: str) -> bool:
        return bool(re.match(r"^[-*•‣▪⁃∙·]\s+", line))

    @staticmethod
    def _strip_bullet(line: str) -> str:
        return re.sub(r"^[-*•‣▪⁃∙·]\s+", "", line).strip()

    _DATE_RANGE = re.compile(
        r"(\b\w+\.?\s*\d{4}\b|\b\d{4}\b|present|current)"
        r"\s*[-–to]+\s*"
        r"(\b\w+\.?\s*\d{4}\b|\b\d{4}\b|present|current)",
        re.I,
    )

    def _parse_work(self, lines: list[str]) -> list[dict]:
        jobs: list[dict] = []
        current: dict | None = None
        for line in lines:
            if self._is_bullet(line):
                if current is not None:
                    current["highlights"].append(self._strip_bullet(line))
                continue
            # A non-bullet line starts a new job entry. Split company/position on
            # common separators; capture a date range if present.
            entry: dict = {"company": "", "position": "", "highlights": []}
            date = self._DATE_RANGE.search(line)
            header = line
            if date:
                header = line[: date.start()].strip(" |,-–")
                entry["startDate"] = self._norm_date(date.group(1))
                end = self._norm_date(date.group(2))
                if end in ("present", "current"):
                    entry["current"] = True
                else:
                    entry["endDate"] = end
            parts = re.split(r"\s+(?:[–|@]|at|-)\s+", header, maxsplit=1)
            if len(parts) == 2:
                entry["position"], entry["company"] = parts[0].strip(), parts[1].strip()
            else:
                entry["company"] = header.strip()
            current = entry
            jobs.append(entry)
        return [j for j in jobs if j.get("company") or j.get("position")]

    @staticmethod
    def _norm_date(token: str) -> str:
        token = (token or "").strip().lower()
        if token in ("present", "current"):
            return token
        months = {
            "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05",
            "jun": "06", "jul": "07", "aug": "08", "sep": "09", "oct": "10",
            "nov": "11", "dec": "12",
        }
        m = re.match(r"([a-z]{3})[a-z]*\.?\s*(\d{4})", token)
        if m and m.group(1) in months:
            return f"{m.group(2)}-{months[m.group(1)]}"
        y = re.match(r"(\d{4})", token)
        if y:
            return y.group(1)
        return token

    def _parse_education(self, lines: list[str]) -> list[dict]:
        edu: list[dict] = []
        for line in lines:
            if self._is_bullet(line):
                if edu:
                    edu[-1].setdefault("courses", []).append(self._strip_bullet(line))
                continue
            entry: dict = {"institution": "", "area": ""}
            date = self._DATE_RANGE.search(line)
            header = line
            if date:
                header = line[: date.start()].strip(" |,-–")
                entry["startDate"] = self._norm_date(date.group(1))
                entry["endDate"] = self._norm_date(date.group(2))
            parts = re.split(r"\s+(?:[–|,]|at|-)\s+", header, maxsplit=1)
            if len(parts) == 2:
                entry["institution"], entry["area"] = parts[0].strip(), parts[1].strip()
            else:
                entry["institution"] = header.strip()
            score = re.search(r"(GPA|CGPA)\s*:?\s*([\d.]+)", line, re.I)
            if score:
                entry["score"] = score.group(0)
            edu.append(entry)
        return [e for e in edu if e.get("institution")]

    def _parse_skills(self, lines: list[str]) -> list[dict]:
        keywords: list[str] = []
        for line in lines:
            line = self._strip_bullet(line) if self._is_bullet(line) else line
            # Strip a leading "Category:" label, keep the values.
            if ":" in line:
                line = line.split(":", 1)[1]
            for kw in re.split(r"[,/|•]", line):
                kw = kw.strip()
                if kw and kw not in keywords:
                    keywords.append(kw)
        if not keywords:
            return []
        return [{"name": "Skills", "keywords": keywords}]

    def _parse_projects(self, lines: list[str]) -> list[dict]:
        projects: list[dict] = []
        for line in lines:
            if self._is_bullet(line):
                if projects:
                    projects[-1]["highlights"].append(self._strip_bullet(line))
                continue
            name = line
            description = ""
            if ":" in line:
                name, description = line.split(":", 1)
            else:
                parts = re.split(r"\s+[-–]\s+", line, maxsplit=1)
                if len(parts) == 2:
                    name, description = parts
            projects.append({
                "name": name.strip(),
                "description": description.strip(),
                "highlights": [],
            })
        return [p for p in projects if p.get("name")]

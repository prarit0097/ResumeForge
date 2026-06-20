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
                   task=None, context=None) -> dict:
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
        """Best-effort offline structuring (real structuring needs the LLM)."""
        from apps.resumes.schema import empty_resume

        data = empty_resume()
        lines = [l.strip() for l in (raw or "").splitlines() if l.strip()]
        if lines:
            data["basics"]["name"] = lines[0][:80]
        email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw or "")
        if email:
            data["basics"]["email"] = email.group(0)
        phone = re.search(r"(\+?\d[\d\s().-]{7,}\d)", raw or "")
        if phone:
            data["basics"]["phone"] = phone.group(0).strip()
        if lines[1:]:
            data["basics"]["summary"] = " ".join(lines[1:4])[:400]
        return data

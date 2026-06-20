# ResumeForge — AI ATS Resume Builder — Design Spec

**Date:** 2026-06-20
**Status:** Approved design → implementation
**Owner:** Prarit

---

## 1. Product Summary

A professional, mobile-friendly, **no-login** Django web app that lets users:

1. **Build a new** ATS-optimized resume with AI assistance (with or without a job description), or
2. **Enhance an existing** resume (upload PDF/DOCX → parse → ATS-optimize),

then pick from a large library of templates, edit via **AI prompt / manual edit / one-click recommendations**, see **live ATS + JD-match scores**, and download as **PDF, DOCX, or PNG** — all free and watermark-free.

### Strategic positioning (from market research)

Across 14+ competitors (Zety, Resume.io, Kickresume, Teal, Rezi, Enhancv, Novoresume, Canva, FlowCV, Jobscan, etc.), **no single product** combines all four of:

- Genuinely free, watermark-free **PDF + clean DOCX** export
- A best-in-class **one-click JD-tailoring** engine that preserves the user's voice
- **Honest ATS guidance** (not the debunked "75% auto-rejected by robots" myth)
- A **real-time score** that updates as you type

ResumeForge unifies these. **Honest framing:** ATS is a searchable filing cabinet, not a judge. The real, fixable risks are (a) multi-column/table layouts that break parsing and (b) image-based PDFs. Our promise: *parse-safe structure + the right real keywords so a human reviewer actually finds you* — never keyword stuffing (which we actively warn against).

---

## 2. Tech Stack (decided)

| Layer | Choice | Rationale |
|---|---|---|
| Web framework | **Django 5.x** | Python-max; batteries-included sessions, ORM, JSONField |
| AI gateway | **OpenRouter → `deepseek/deepseek-chat-v3-0324`** via official `openai` SDK | Cheap, capable, JSON-schema support |
| AI abstraction | Swappable `LLMProvider` interface + **offline mock provider** | App fully works before a key is added; key set later in `.env` |
| PDF | **Playwright (headless Chromium)** `page.pdf()` | Full CSS fidelity + **selectable text** (ATS-critical) + clean Windows install. WeasyPrint = pure-Python fallback |
| DOCX | **python-docx** (programmatic) | Guarantees ATS-safe single-column, no tables/text-boxes, by construction |
| PNG | **Playwright `page.screenshot`** | Reuses the same render path; pixel-accurate |
| PDF text extraction | **pdfplumber** (MIT) | Avoids PyMuPDF AGPL; good reading order |
| DOCX text extraction | **python-docx** (walk paragraphs + tables) | Resumes hide contact info in tables |
| Resume structuring | **LLM (DeepSeek)** with strict JSON schema | Regex/pyresparser is brittle and unmaintained |
| Frontend | **Django templates + htmx + Alpine.js + Tailwind** | One preview partial = single source of truth for live preview AND PDF; mobile-first; no Node build needed |
| Persistence | UUID4 pk + secret `edit_token` in URL + `JSONField` | No-login, shareable, resumable, enumeration-safe |
| DB | SQLite (dev) → Postgres-ready (prod) | JSONField works on both |
| Background work | Synchronous in dev; Celery-ready hooks for PDF/AI in prod | Keep dev simple |

**License note:** Use pdfplumber (parsing) + Playwright (PNG) to avoid PyMuPDF's AGPL. WeasyPrint (BSD) is the PDF fallback.

---

## 3. Data Model

```
Resume
  id: UUID4 (pk)
  edit_token: str (secrets.token_urlsafe(32))   # secret, in URL ?t=
  session_key: str (nullable)                    # "drafts on this device" index
  parent: FK self (nullable)                     # for tailored variants
  title: str                                     # "Software Engineer — Acme"
  data: JSONField                                # JSON Resume schema (see §4)
  template_id: str                               # registry key
  target_role: str (nullable)
  experience_level: str (nullable)               # entry/mid/senior/exec
  job_description: text (nullable)               # last pasted JD
  ats_score: JSONField (nullable)                # cached last compatibility result
  match_score: JSONField (nullable)              # cached last JD-match result
  created_at / updated_at: datetime

CoverLetter
  id: UUID4 (pk)
  resume: FK Resume
  body: text
  job_description: text (nullable)
  created_at / updated_at
```

- **No User model.** Identity = possession of the `edit_token` URL. Cookie stores the token for same-browser convenience; `session_key` lists "my drafts on this device."
- Lookups always filter by **pk AND edit_token** (`hmac.compare_digest`).
- `purge_old_resumes` management command deletes drafts untouched > 90 days.

---

## 4. Resume JSON Schema (JSON Resume aligned)

```jsonc
{
  "basics": { "name","label","email","phone","location","url","summary","profiles":[{"network","url"}] },
  "work": [{ "company","position","location","startDate","endDate","current","highlights":[],"summary" }],
  "education": [{ "institution","area","studyType","startDate","endDate","score","courses":[] }],
  "skills": [{ "name","level","keywords":[] }],
  "projects": [{ "name","description","highlights":[],"url","keywords":[] }],
  "certifications": [{ "name","issuer","date","url" }],
  "awards": [{ "title","date","awarder","summary" }],
  "languages": [{ "language","fluency" }],
  "volunteer": [{ "organization","position","summary","highlights":[] }],
  "custom": [{ "heading","items":[] }]            // user-defined sections
}
```

Dates normalized to `YYYY-MM`. Absent fields → `null` / `[]`. Server-side validated (jsonschema/Pydantic) before persist.

---

## 5. Django App Structure (many small focused apps)

```
resumeforge/                 # project settings
apps/
  resumes/        # Resume/CoverLetter models, CRUD, autosave, session "my drafts"
  builder/        # new-resume wizard flow + editor views (htmx)
  parsing/        # upload → text extraction → LLM structuring
  ai/             # LLMProvider abstraction, OpenRouter+mock, prompts, rate limiting
  ats/            # ATS compatibility scorer + JD-match scorer (pure-Python, tested)
  templates_engine/  # template registry, render partials, categories
  exporting/      # PDF (Playwright), DOCX (python-docx), PNG
  coverletters/   # AI cover letter generation
core/             # shared utils, base templates, validation, mixins
static/ , templates/
```

Each module: one clear purpose, well-defined interface, independently testable. Files target 200–400 lines, 800 max.

---

## 6. The Two Scoring Engines (differentiators)

### 6a. ATS Compatibility Score (0–100, JD-independent gate)

Pure-Python, deterministic, fully unit-tested. Dimensions (weighted), each returns a **specific actionable fix**:

| Dimension | What it checks |
|---|---|
| Parse-safety | single-column (enforced by template), no tables/text-boxes, contact in body |
| Standard headings | canonical set: "Work Experience","Education","Skills","Summary"… |
| Contact completeness | name, email, phone present and in body |
| Dates | present + parseable + consistent format |
| Action verbs | bullets start with strong verbs |
| Quantified impact | % of bullets containing numbers/metrics |
| Length | page count vs experience level |
| Section completeness | required sections present |
| File-safety | text-selectable (always true via our export) |

Output: `{ score, grade, dimensions:[{key,score,weight,status,fix}], summary }`.

### 6b. JD-Match Score (0–100, when a JD is provided)

Jobscan-style, **hard-skill-weighted**:

| Dimension | Weight |
|---|---|
| Hard skills match (exact + synonym) | heaviest |
| Job title match | high |
| Education requirement (only if JD requires) | medium |
| Soft skills | low |
| Other keywords | low |

- Extract keywords from JD (LLM-assisted + curated skill taxonomy).
- Report: matched / missing / suggested keywords; target **75% min, 80% sweet spot**; **flag over-optimization > ~88%** and **warn against stuffing**.
- One-click **"Tailor to this job"** → AI rewrites bullets/skills/summary to close real gaps while preserving voice; never invents experience.

---

## 7. AI Layer

- `LLMProvider` abstract interface: `complete(messages, **opts)`, `stream(...)`, `structured(messages, schema)`.
- `OpenRouterProvider` (OpenAI SDK, base_url `https://openrouter.ai/api/v1`, model from settings, `max_retries`, backoff on 429, surface 402).
- `MockProvider` — deterministic, template-based responses so the **entire app works offline** before a key exists.
- Provider chosen via settings: if `OPENROUTER_API_KEY` present → OpenRouter, else → Mock (with a visible "AI in demo mode" banner).
- **Prompted capabilities:** generate bullets, write summary, rewrite/improve text, tailor to JD, structure parsed resume, generate cover letter, suggest recommendations.
- All AI prompts: extract-don't-invent, no hallucination, strict JSON where structured.
- **Rate-limiting** (`django-ratelimit`) + payload caps on all AI endpoints (cost protection).

---

## 8. User Flows

### 8a. Build New
Landing → `Build New` → intake (target role + experience level) → guided wizard (Contact → Experience → Education → Skills → Summary) with AI generate/improve per step → optional paste JD → live ATS + match scores → `OK` → template gallery → editor (live preview) → download.

### 8b. Enhance Existing
Landing → `Enhance` → upload PDF/DOCX → parse → structured fields + instant ATS audit + fix list → optional JD → AI ATS-optimize/tailor → template → editor → download.

### 8c. Editor (shared)
- Manual edit (htmx form ↔ live preview partial)
- **Edit by AI prompt** ("make my summary punchier", "tailor to this JD")
- **One-click recommendations** panel (from ATS + match engines)
- Template switch (no data loss)
- Cover letter tab
- "My drafts on this device" list; create tailored variant (parent link)

---

## 9. Templates

- **Registry**: each template = `{ id, name, category, ats_safe: bool, ats_risk_note, html_partial, css_tokens }`, all driven by the same resume JSON.
- Categories: Professional, Modern, Minimal, Creative, Technical, Executive, Academic, Simple/ATS-Safe.
- ATS-safe single-column core set is the default and clearly labeled; multi-column/creative templates labeled with their parse risk.
- **Target 100+ distinct layouts**, delivered in batches. Honest scope: a substantial launch library + the engine to keep adding genuinely distinct designs (not trivial recolors).
- Same partial feeds live preview AND PDF/PNG → guaranteed WYSIWYG.

---

## 10. Export

- **PDF** — Playwright, text-selectable, watermark-free.
- **DOCX** — python-docx, ATS-clean single-column.
- **PNG** — Playwright screenshot.
- **"What the ATS sees"** plain-text round-trip preview.

---

## 11. Security & Quality

- Unguessable UUID + `edit_token`; `hmac.compare_digest`; filter by pk+token.
- `X-Robots-Tag: noindex`, `Referrer-Policy: no-referrer` (resumes contain PII).
- CSRF on all mutations; payload size caps; upload validation (type, size, content).
- Rate-limit AI/export endpoints.
- No secrets in code; `.env` via `django-environ`; `.env.example` provided.
- Tests: scoring engines (unit), parsing (fixtures), export smoke tests, key flows.

---

## 12. Out of Scope for v1 (deferred)

- Job application tracker (kanban)
- Chrome extension
- LinkedIn import/optimizer
- Human review marketplace
- User accounts / multi-device sync beyond shareable link
- Multi-language UI (English first)

---

## 13. Included extras (v1)

- **Cover letter generator** (resume + JD aware)
- **Multiple resume versions** (base + tailored variants via `parent`)

---

## 14. Phasing (build order)

1. **Foundation** — Django project, apps scaffold, settings/.env, base layout (Tailwind+htmx+Alpine), Resume model + no-login session/token plumbing, autosave.
2. **Resume data + editor** — JSON schema, wizard + editor with htmx live preview, "my drafts".
3. **Template engine** — registry + initial ATS-safe + creative template set + gallery + switching.
4. **AI layer** — provider abstraction + OpenRouter + mock; generate/improve/rewrite; prompt editing.
5. **ATS engine** — compatibility scorer + JD-match scorer + recommendations panel + tailor-to-JD.
6. **Parsing** — upload → extract → LLM structure → enhance flow.
7. **Export** — PDF + DOCX + PNG + "what the ATS sees".
8. **Cover letters + variants.**
9. **Template library expansion** toward 100+ (batched).
10. **Polish** — mobile QA, accessibility, performance, security pass, tests, docs/README.

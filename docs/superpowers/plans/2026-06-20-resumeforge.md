# ResumeForge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A no-login Django web app to build/enhance ATS-optimized resumes with AI, pick from many templates, score against ATS + a JD, edit by prompt/manually/recommendations, and export PDF/DOCX/PNG.

**Architecture:** Django 5 with many small apps. A single resume-preview template partial is the source of truth for live preview AND PDF/PNG export. AI runs behind a swappable `LLMProvider` (OpenRouter→DeepSeek, or an offline Mock). Pure-Python scoring engines are deterministic and unit-tested. Resume content lives in a `JSONField`; identity is an unguessable UUID + edit_token (no accounts).

**Tech Stack:** Django 5, openai SDK (→OpenRouter/DeepSeek), Playwright (PDF/PNG), python-docx (DOCX), pdfplumber (PDF parse), htmx + Alpine.js + Tailwind, pytest-django, django-environ.

## Global Constraints

- Python 3.10+ (`python` on PATH is 3.10.11). Windows 10 dev. Use the Bash tool for POSIX scripts; venv at `.venv`.
- No login/accounts. Identity = UUID `Resume.id` + secret `edit_token`; always filter by both, compare with `hmac.compare_digest`.
- No secrets in code. Config via `.env` (`django-environ`); ship `.env.example`. App must fully work with NO key (Mock AI provider + "demo mode" banner).
- ATS output is always single-column, text-selectable. Never produce keyword-stuffing; warn against it.
- One preview partial drives preview + PDF + PNG (no WYSIWYG drift).
- Files focused: 200–400 lines target, 800 max. Validate input at boundaries. Immutable-style updates.
- Resume JSON follows JSON Resume schema (spec §4). Dates `YYYY-MM`.
- Tests: pytest-django. Scoring engines and parsing structuring must have unit tests.

---

## Phase 1 — Foundation

### Task 1.1: Project scaffold + settings + env

**Files:**
- Create: `requirements.txt`, `.env.example`, `manage.py`, `resumeforge/{__init__,settings,urls,wsgi,asgi}.py`, `pytest.ini`, `conftest.py`, `core/__init__.py`
- Create: `apps/__init__.py` and empty package dirs for each app

**Steps:**
- [ ] Create `.venv`, install: `django`, `openai`, `python-docx`, `pdfplumber`, `playwright`, `django-environ`, `django-ratelimit`, `jsonschema`, `pytest`, `pytest-django`, `beautifulsoup4`. Pin in `requirements.txt`. Run `playwright install chromium`.
- [ ] `django-admin startproject resumeforge .`; configure `settings.py` with `django-environ`, `INSTALLED_APPS` for each `apps.*`, SQLite default, `STATIC`/`MEDIA`, templates dir, security headers (`X-Robots-Tag` middleware later), `LLM` settings block (`OPENROUTER_API_KEY`, `LLM_MODEL`).
- [ ] `pytest.ini` with `DJANGO_SETTINGS_MODULE=resumeforge.settings`; `conftest.py` enabling DB.
- [ ] Verify: `python manage.py check` passes; `pytest -q` runs (0 tests OK).
- [ ] Commit: `chore: django project scaffold + env config`.

### Task 1.2: Base layout (Tailwind + htmx + Alpine), landing page

**Files:**
- Create: `templates/base.html`, `templates/landing.html`, `static/css/app.css`, `core/views.py`, `core/urls.py`
- Modify: `resumeforge/urls.py`

**Steps:**
- [ ] `base.html`: responsive shell, Tailwind (CDN for dev, build step noted for prod), htmx + Alpine via CDN, nav, mobile-friendly, "AI demo mode" banner slot.
- [ ] `landing.html`: hero + two big CTAs `Build New Resume` / `Enhance Existing Resume`, value props from research (free, ATS-safe, PDF+DOCX, JD tailoring). Designed, not template-generic (per design-quality rules).
- [ ] `core/views.py: landing_view`; wire urls. Verify page renders at `/`.
- [ ] Test: `tests/core/test_landing.py` — GET `/` returns 200 and contains both CTA labels.
- [ ] Commit: `feat: base layout + landing page`.

### Task 1.3: Resume model + no-login token plumbing

**Files:**
- Create: `apps/resumes/models.py`, `apps/resumes/schema.py` (JSON Resume validation), `apps/resumes/services.py` (create/get/update/list-by-session), `apps/resumes/migrations/`
- Test: `tests/resumes/test_models.py`, `tests/resumes/test_services.py`

**Interfaces (Produces):**
- `Resume` model per spec §3. `CoverLetter` model.
- `services.create_resume(session_key, **kw) -> Resume`
- `services.get_resume(resume_id, edit_token) -> Resume | None` (constant-time token check)
- `services.list_session_resumes(session_key) -> QuerySet`
- `schema.validate_resume_data(data: dict) -> list[str]` (returns error strings; empty = valid)
- `schema.empty_resume() -> dict`

**Steps:**
- [ ] Write failing tests: create resume sets uuid+token; get with wrong token returns None; get with right token returns it; list filters by session; `validate_resume_data` rejects malformed, accepts `empty_resume()`.
- [ ] Run tests → fail.
- [ ] Implement models, `secrets.token_urlsafe(32)` default for token, `JSONField(default=schema.empty_resume)`, `schema.py` with jsonschema validator + canonical empty doc.
- [ ] `makemigrations` + run tests → pass.
- [ ] Commit: `feat: resume model + session/token services`.

---

## Phase 2 — Editor + autosave

### Task 2.1: Builder entry + draft creation + "my drafts"

**Files:**
- Create: `apps/builder/views.py`, `apps/builder/urls.py`, `templates/builder/my_drafts.html`
- Modify: `resumeforge/urls.py`

**Steps:**
- [ ] `start_new` view: create Resume for session, redirect to editor URL `/r/<uuid>/edit/?t=<token>`.
- [ ] `my_drafts` view: list session resumes with links.
- [ ] `@ensure_csrf_cookie` on editor view. Set cookie with token for convenience.
- [ ] Test: starting new creates a resume + redirects; drafts page lists it.
- [ ] Commit: `feat: builder entry + drafts list`.

### Task 2.2: Editor shell + preview partial + autosave

**Files:**
- Create: `templates/builder/editor.html`, `templates/preview/_resume.html` (THE source-of-truth partial), `templates/preview/preview_css/` token files, `apps/builder/forms.py` (section forms), `apps/resumes/views.py` (autosave endpoint)
- Test: `tests/builder/test_autosave.py`

**Interfaces (Produces):**
- `_resume.html` renders a full resume from `{resume, template}` context — used by preview, PDF, PNG.
- Autosave endpoint `POST /r/<uuid>/autosave/?t=` accepts JSON section data, validates via `schema.validate_resume_data`, saves, returns re-rendered preview partial (htmx swap).

**Steps:**
- [ ] Build `_resume.html` as a clean single-column ATS-safe default render of the JSON.
- [ ] Editor: left = section forms (Contact/Experience/Education/Skills/Summary), right = `#preview` (sticky desktop, collapsible mobile via Alpine). Forms `hx-post` autosave on `keyup changed delay:500ms`.
- [ ] Autosave endpoint: validate + last-write-wins save + return partial.
- [ ] Test: autosave persists data and returns 200 with updated content; invalid data rejected (400).
- [ ] Commit: `feat: editor shell + live preview + autosave`.

### Task 2.3: New-resume wizard (intake → sections)

**Files:**
- Create: `templates/builder/wizard/*.html`, wizard views in `apps/builder/views.py`
- Test: `tests/builder/test_wizard.py`

**Steps:**
- [ ] Intake step: target role + experience level → store on Resume.
- [ ] Step-by-step section capture writing into `data`; "skip" allowed; finish → editor.
- [ ] Optional "paste JD" field stored on Resume.
- [ ] Test: wizard flow stores role/level and section data.
- [ ] Commit: `feat: new-resume wizard`.

---

## Phase 3 — Template engine

### Task 3.1: Template registry + render service

**Files:**
- Create: `apps/templates_engine/registry.py`, `apps/templates_engine/render.py`, `templates/resume_templates/<id>/template.html` + `style.css` per template
- Test: `tests/templates_engine/test_registry.py`

**Interfaces (Produces):**
- `registry.TEMPLATES: dict[str, TemplateMeta]` where `TemplateMeta = {id,name,category,ats_safe,ats_risk_note,dir}`.
- `registry.get(template_id) -> TemplateMeta` (falls back to default).
- `render.render_resume_html(resume, template_id) -> str` (full standalone HTML for export) and a partial variant for preview.

**Steps:**
- [ ] Define registry + 6 starter templates spanning categories (≥3 ATS-safe single-column, others labeled with risk).
- [ ] Render service injects resume JSON + template CSS.
- [ ] Test: registry returns metas; unknown id → default; render produces HTML containing the resume name.
- [ ] Commit: `feat: template registry + render service`.

### Task 3.2: Template gallery + switching

**Files:**
- Create: `templates/builder/gallery.html`, gallery views
- Test: `tests/templates_engine/test_gallery.py`

**Steps:**
- [ ] Gallery: filter by category, ATS-safe badge, live thumbnail (render partial scaled), "Use template" sets `Resume.template_id` (no data loss).
- [ ] Test: switching template updates resume and preview uses new template.
- [ ] Commit: `feat: template gallery + switching`.

---

## Phase 4 — AI layer

### Task 4.1: LLMProvider abstraction + Mock + OpenRouter

**Files:**
- Create: `apps/ai/provider.py` (abstract + factory), `apps/ai/openrouter.py`, `apps/ai/mock.py`, `apps/ai/prompts.py`
- Test: `tests/ai/test_provider.py` (Mock only; OpenRouter behind a marker)

**Interfaces (Produces):**
- `provider.get_provider() -> LLMProvider` (OpenRouter if key set else Mock).
- `LLMProvider.complete(messages, **opts) -> str`
- `LLMProvider.structured(messages, schema) -> dict`
- `provider.is_demo_mode() -> bool`

**Steps:**
- [ ] Write tests: factory returns Mock when no key; Mock.complete returns deterministic non-empty text; Mock.structured returns schema-valid dict.
- [ ] Implement abstraction, Mock (deterministic helpful stubs), OpenRouter (openai SDK, base_url, retries/backoff, 402 surfaced, JSON schema response_format).
- [ ] Run tests → pass.
- [ ] Commit: `feat: AI provider abstraction + mock + openrouter`.

### Task 4.2: AI content endpoints (generate/improve/rewrite/prompt-edit)

**Files:**
- Create: `apps/ai/services.py` (generate_bullets, write_summary, improve_text, rewrite_to_jd, prompt_edit), `apps/ai/views.py`, `apps/ai/urls.py`
- Test: `tests/ai/test_services.py`

**Steps:**
- [ ] Services compose prompts (extract-don't-invent rules) + call provider; validate outputs.
- [ ] htmx endpoints used by editor buttons ("Improve", "Generate bullets", "Tailor", free-text "Edit by prompt"). Rate-limited.
- [ ] Test (Mock provider): each service returns expected shape; prompt_edit applies to a field.
- [ ] Commit: `feat: AI content services + editor endpoints`.

---

## Phase 5 — ATS engines

### Task 5.1: ATS compatibility scorer (pure-Python, TDD)

**Files:**
- Create: `apps/ats/compatibility.py`, `apps/ats/constants.py` (canonical headings, action verbs)
- Test: `tests/ats/test_compatibility.py`

**Interfaces (Produces):**
- `compatibility.score_resume(data: dict, template_meta) -> dict` returning `{score, grade, dimensions:[{key,score,weight,status,fix}], summary}` per spec §6a.

**Steps:**
- [ ] Write tests covering each dimension: empty resume scores low with fixes; a complete quantified single-column resume scores high; missing contact flagged; bullets without verbs flagged; non-quantified bullets flagged.
- [ ] Run → fail.
- [ ] Implement weighted dimensions deterministically.
- [ ] Run → pass.
- [ ] Commit: `feat: ATS compatibility scorer`.

### Task 5.2: JD-match scorer (pure-Python + keyword extraction, TDD)

**Files:**
- Create: `apps/ats/jd_match.py`, `apps/ats/keywords.py` (skill taxonomy + extraction; LLM-assisted optional with Mock fallback)
- Test: `tests/ats/test_jd_match.py`

**Interfaces (Produces):**
- `jd_match.score(data: dict, jd_text: str) -> dict` → `{score, matched:[], missing:[], suggested:[], dimensions:[...], warnings:[]}` (over-optimization warning > ~88, stuffing warning).
- `keywords.extract(jd_text) -> {hard:[], soft:[], title:str, education:str|None}`

**Steps:**
- [ ] Tests: resume missing JD hard-skills → low + missing list; full match → high + over-opt warning; weighting favors hard skills/title.
- [ ] Run → fail. Implement extraction + weighted match. Run → pass.
- [ ] Commit: `feat: JD-match scorer + keyword extraction`.

### Task 5.3: Scores + recommendations panel in editor + Tailor-to-JD

**Files:**
- Create: `apps/ats/views.py`, `apps/ats/urls.py`, `templates/builder/_score_panel.html`
- Test: `tests/ats/test_views.py`

**Steps:**
- [ ] Endpoints: live ATS score + (if JD) match score; recommendations list with one-click apply (each rec maps to an AI service or field fix). "Tailor to this job" calls `ai.rewrite_to_jd` then re-scores.
- [ ] Editor shows live score (htmx, debounce) + recommendations + stuffing warning.
- [ ] Test: score endpoint returns scores; tailor improves match in Mock path.
- [ ] Commit: `feat: live scores + recommendations + tailor-to-JD`.

---

## Phase 6 — Parsing (Enhance existing)

### Task 6.1: Text extraction + LLM structuring

**Files:**
- Create: `apps/parsing/extract.py` (pdf via pdfplumber, docx via python-docx incl. tables), `apps/parsing/structure.py` (LLM → JSON Resume, Mock fallback), `apps/parsing/views.py`, `apps/parsing/urls.py`, `templates/parsing/upload.html`
- Test: `tests/parsing/test_extract.py`, `tests/parsing/test_structure.py` (Mock)

**Interfaces (Produces):**
- `extract.extract_text(uploaded_file) -> str` (validates type/size; raises on bad input)
- `structure.to_resume_json(raw_text) -> dict` (schema-valid; never invents)

**Steps:**
- [ ] Tests: extract from a fixture PDF and DOCX returns expected substrings; bad type rejected; oversized rejected; `to_resume_json` (Mock) returns schema-valid dict; structuring validated against schema.
- [ ] Run → fail. Implement extraction + structuring + upload view that creates a Resume and redirects to editor with instant ATS audit. Run → pass.
- [ ] Commit: `feat: resume upload parsing + structuring (enhance flow)`.

---

## Phase 7 — Export

### Task 7.1: PDF + PNG via Playwright

**Files:**
- Create: `apps/exporting/render_browser.py` (launch chromium, html→pdf, html→png), `apps/exporting/views.py`, `apps/exporting/urls.py`
- Test: `tests/exporting/test_export.py`

**Interfaces (Produces):**
- `render_browser.html_to_pdf(html: str) -> bytes`
- `render_browser.html_to_png(html: str) -> bytes`
- Download views `/r/<uuid>/download/pdf|png/?t=` returning correct content types.

**Steps:**
- [ ] Tests: html_to_pdf returns bytes starting `%PDF`; html_to_png returns PNG signature bytes; download views require valid token.
- [ ] Run → fail. Implement (reuse one browser; sync API in dev). Run → pass.
- [ ] Commit: `feat: PDF + PNG export`.

### Task 7.2: DOCX (python-docx, ATS-clean) + "what the ATS sees"

**Files:**
- Create: `apps/exporting/docx_builder.py`, `apps/exporting/plain_text.py`
- Test: `tests/exporting/test_docx.py`

**Interfaces (Produces):**
- `docx_builder.build_docx(data: dict) -> bytes` (single-column, no tables/text-boxes, standard styles)
- `plain_text.as_plain_text(data: dict) -> str`

**Steps:**
- [ ] Tests: docx bytes are a valid zip with `word/document.xml`; contains name + a skill; no `<w:tbl>` in document.xml; plain text contains sections.
- [ ] Run → fail. Implement. Run → pass.
- [ ] Commit: `feat: ATS-clean DOCX export + plain-text view`.

---

## Phase 8 — Cover letters + variants

### Task 8.1: Cover letter generation

**Files:**
- Create: `apps/coverletters/services.py`, `apps/coverletters/views.py`, `apps/coverletters/urls.py`, `templates/coverletters/*.html`
- Test: `tests/coverletters/test_services.py`

**Steps:**
- [ ] Service: `generate(resume_data, jd_text) -> str` (resume+JD aware, Mock fallback). View: editor "Cover letter" tab, editable, exportable (PDF/DOCX reuse).
- [ ] Test (Mock): generates non-empty letter referencing role.
- [ ] Commit: `feat: AI cover letter generator`.

### Task 8.2: Tailored variants

**Files:**
- Modify: `apps/resumes/services.py`, editor templates
- Test: `tests/resumes/test_variants.py`

**Steps:**
- [ ] `services.create_variant(resume) -> Resume` (copies data, sets `parent`). UI: "Create tailored copy for a job".
- [ ] Test: variant copies data and links parent; drafts list groups variants.
- [ ] Commit: `feat: tailored resume variants`.

---

## Phase 9 — Template library expansion

### Task 9.x: Add templates in batches toward 100+

**Files:** `templates/resume_templates/<id>/*`, registry entries
- [ ] Add genuinely-distinct layouts per category in batches; each must render from the same JSON and pass a render smoke test; ATS-safe ones validated single-column.
- [ ] Maintain a `tests/templates_engine/test_all_render.py` that renders every registered template against a sample resume and asserts no error + name present.
- [ ] Commit per batch: `feat: add resume templates batch N`.

---

## Phase 10 — Polish

### Task 10.1: Security, mobile, a11y, perf, docs

**Files:** `core/middleware.py` (noindex/referrer headers), `README.md`, `.env.example`
- [ ] Security middleware headers; rate-limit verified on AI/export; upload caps; token checks audited.
- [ ] Mobile QA (320–1440), keyboard nav, reduced-motion, contrast.
- [ ] `README.md` (setup, add OpenRouter key, run), `.env.example` complete.
- [ ] Run full `pytest`; `python manage.py check --deploy` review.
- [ ] Commit: `chore: security + a11y + docs polish`.

---

## Self-Review Notes

- **Spec coverage:** §2 stack→all phases; §3 model→1.3; §4 schema→1.3; §5 apps→all; §6 engines→5.1/5.2; §7 AI→4.1/4.2; §8 flows→2.x/5.3/6.1; §9 templates→3.x/9.x; §10 export→7.x; §11 security→10.1; §13 extras→8.x. Covered.
- **Demo mode:** Mock provider (4.1) ensures whole app works with no key.
- **Source-of-truth partial:** introduced in 2.2, consumed by render (3.1) + export (7.1).

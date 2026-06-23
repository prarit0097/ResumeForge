# Rezoom — Master Reference

> **One file to understand the whole project.** What it is, why it exists, what it
> solves, how it's built, how it's deployed, and every moving part. If you (human or AI)
> read only one file, read this one.
>
> ⚠️ **Keep this file in sync.** Whenever anything in the app changes — a feature, a
> route, an env var, a deployment detail — update the relevant section here **and** the
> [Changelog](#16-changelog) at the bottom. Treat `REZOOM.md` as part of "done".

- **Live site:** https://rezoom.praritsidana.com
- **Git repo:** https://github.com/prarit0097/ResumeForge  (product = *Rezoom*; the Django package/repo stays named `resumeforge`/`ResumeForge` to avoid breaking imports & deploys)
- **Status:** In production (deployed 2026-06-23) on a Hostinger VPS.

---

## Table of Contents
1. [What is Rezoom](#1-what-is-rezoom)
2. [Why it exists / the problem](#2-why-it-exists--the-problem)
3. [What it does (features)](#3-what-it-does-features)
4. [Honest-by-design philosophy](#4-honest-by-design-philosophy)
5. [Pros & cons](#5-pros--cons)
6. [Tech stack](#6-tech-stack)
7. [Architecture & the 8 apps](#7-architecture--the-8-django-apps)
8. [Data model & no-login security](#8-data-model--no-login-security)
9. [AI layer](#9-ai-layer)
10. [ATS scoring](#10-ats-scoring)
11. [Templates, rendering & export](#11-templates-rendering--export)
12. [Full route map](#12-full-route-map)
13. [Project structure](#13-project-structure)
14. [Configuration (env vars)](#14-configuration-env-vars)
15. [Local development](#15-local-development)
16. [Testing](#16-testing)
17. [Deployment (production)](#17-deployment-production)
18. [Updating / redeploying](#18-updating--redeploying)
19. [Maintenance & operations](#19-maintenance--operations)
20. [SEO](#20-seo)
21. [Changelog](#21-changelog)
22. [Quick-reference card](#22-quick-reference-card)

---

## 1. What is Rezoom

Rezoom is a **free, no-login, AI-powered ATS resume builder and ATS checker** (web app, Django).
A user can:
- **Build a new resume** from scratch with AI writing strong, quantified bullets, **or**
- **Enhance an existing resume** (upload a PDF/Word file → it's restructured to be ATS-friendly), **or**
- **Check an ATS score instantly** by uploading a resume on the landing page.

Then: get a live **0–100 ATS compatibility score** with specific fixes, optionally **tailor to a
job description**, pick from **103 templates**, and download a clean **PDF / Word / PNG / TXT** —
**no account, no watermark, no paywall.**

---

## 2. Why it exists / the problem

- Most job seekers get filtered out by **Applicant Tracking Systems (ATS)** because their resume
  **doesn't parse cleanly** (two-column layouts, tables, graphics, missing standard headings) or
  **lacks the right keywords** for the role.
- Existing "free" builders usually **paywall the download** or **stamp a watermark**, force an
  **account**, and many **lie** that they can "beat the bots".
- **Rezoom's solution:** a genuinely free, no-login tool that (a) guarantees a **parse-safe
  structure**, (b) surfaces the **right *real* keywords**, (c) gives an **honest ATS score** with
  actionable fixes, and (d) lets you **download for free** in any format.

**What it does NOT do (by design):** it never fabricates skills, employers, metrics, degrees, or
dates. ATS is a searchable database, not a judge — so we optimize *parseability + real keyword
surfacing*, not keyword-stuffing or fake experience (which collapses in interviews).

---

## 3. What it does (features)

- **Two entry flows + instant check** — build new (guided wizard → editor), enhance existing
  (upload → before/after compare), or instant ATS score on the landing page.
- **AI writing** (OpenRouter → DeepSeek): rewrite bullets with strong action verbs, write a
  summary, generate achievement bullets, one-click "polish whole resume", tailor to a JD.
- **ATS compatibility score (0–100)** — pure-Python, deterministic, 8 weighted dimensions, each
  with a concrete fix.
- **JD match score (0–100)** — keyword/title/education/soft-skill match against a pasted job
  description, with missing-keyword guidance (and an over-optimization warning).
- **Before/after comparison** for enhanced resumes (old score vs new, what improved, why it helps).
- **103 resume templates** (86 ATS-safe single-column + creative two-column), 5 layout families ×
  color themes; switch any time without losing content.
- **Live editor** — htmx + Alpine, debounced autosave, live preview that drives the export (no
  drift), guided onboarding, splits pasted multi-line bullets, fit-to-width preview.
- **Exports** — PDF & PNG (headless Chromium via Playwright), DOCX (python-docx, ATS-safe), TXT.
- **Cover letter generator** (AI, from the resume + JD).
- **No login** — drafts are remembered per device (session + secret token cookie); "My drafts".
- **Offline demo mode** — with no API key, a deterministic mock provider still produces output.
- **SEO** — robots.txt, sitemap.xml, JSON-LD (WebApplication + FAQ), per-page meta/OG, GA4.

---

## 4. Honest-by-design philosophy

This is a **core product principle**, enforced in code (`apps/ai/prompts.py`, `apps/ai/enhance.py`):

- **Never invent** employers, titles, degrees, tools, certifications, metrics, or dates.
- **Keep** real metrics; **never** add placeholder numbers (`by X%`, `$Y`) — these are stripped.
- **Skills** are only *surfaced* from text already in the resume, never fabricated; sentence-like
  "skills" are dropped, keeping concise scannable keywords.
- **Skill-gap honesty** — instead of faking missing JD skills, it guides the user on what's
  genuinely missing.
- **No technical-washing** when tailoring to a JD — relevance reordering & honest keyword surfacing,
  not pretending unrelated experience is what the JD wants.

The user asked for fake skills/metrics more than once; this was deliberately declined because it
backfires in interviews. **Do not regress this.**

---

## 5. Pros & cons

**Pros**
- Genuinely free, no login, no watermark — low friction, shareable.
- Honest output that survives interviews; clean ATS-parseable structure.
- Fast: single combined LLM call for extract+enhance; warm Chromium per worker for quick exports.
- Self-contained: SQLite + WhiteNoise (no separate DB server or static host needed).
- Swappable LLM provider; works offline (mock) for demos/tests.
- Strong SEO + analytics foundation.

**Cons / limitations (be honest)**
- **SQLite** — fine for a single small VPS; not built for high concurrency / horizontal scale.
- **No accounts** — drafts live on the device (session + token cookie); clearing cookies loses the
  "my drafts" list (the resume still exists if its `?t=` link/cookie is kept).
- **PDF/PNG need Chromium** on the host (~300 MB); first export per worker is slower (cold launch).
- **LLM dependency/cost** — needs an OpenRouter key for live AI; rate-limited per endpoint to cap cost.
- **Two-column templates** are marked *not ATS-safe* (some strict parsers drop sidebar content).
- Running gunicorn as `root` on the VPS is pragmatic but not best-practice hardening.

---

## 6. Tech stack

| Layer | Choice |
|---|---|
| Web framework | **Django 5.1.4** (no auth/admin apps — no login) |
| Language | Python 3.12 |
| AI | **OpenRouter** via the `openai` SDK → **DeepSeek** (`deepseek/deepseek-v4-flash`) |
| DB | **SQLite** (`db.sqlite3`) |
| Frontend | Server-rendered Django templates + **Tailwind (CDN)** + **htmx** + **Alpine.js** |
| Parsing | **pdfplumber** (PDF), **python-docx** (DOCX) |
| Export | **Playwright** headless Chromium (PDF/PNG), **python-docx** (DOCX) |
| Static | **WhiteNoise** (compressed + hashed in prod) |
| Server | **gunicorn** behind **nginx**, **Let's Encrypt** TLS |
| Validation | **jsonschema** (JSON Resume shape) |
| Rate limiting | **django-ratelimit** |
| Config | **django-environ** (`.env`) |
| Tests | **pytest** + **pytest-django** (101 tests) |

Pinned versions live in [`requirements.txt`](requirements.txt).

---

## 7. Architecture & the 8 Django apps

Server-rendered Django. One **`Resume`** row (UUID id + secret token) holds a **JSON Resume**
document in a `JSONField`. The **same render path** produces the live editor preview and the
PDF/PNG export (so what you see is what you download). Code is organized by domain into 8 apps
under `apps/` plus a `core/` package for cross-cutting concerns.

| App | Responsibility |
|---|---|
| `apps.resumes` | Data: `Resume` + `CoverLetter` models, JSON Resume schema, token-based access services, autosave/set-template views, `purge_old_resumes` command. |
| `apps.builder` | Flows: new-resume wizard, the editor, drafts list, variants, before/after **compare**, use-original. |
| `apps.parsing` | Upload → text extraction (PDF/DOCX) → structured JSON; the **enhance** flow & the instant **ats-check** endpoint. |
| `apps.ai` | LLM provider abstraction (OpenRouter/Mock), prompts, enhancement + **honesty/ATS-polish**, AI endpoints (improve/bullets/polish). |
| `apps.ats` | **ATS compatibility score** (0–100), **JD match score**, keyword extraction, shared constants (action verbs etc.), score/tailor endpoints. |
| `apps.templates_engine` | 103-template registry (ATS metadata), resume→HTML render (shared preview/export), gallery, custom template tags. |
| `apps.exporting` | PDF/PNG (Playwright), DOCX (python-docx), TXT, download menu. |
| `apps.coverletters` | AI cover-letter generation + editor. |
| `core` | Landing/marketing pages, no-login access control, sessions, context processor, privacy middleware, SEO (robots/sitemap). |

---

## 8. Data model & no-login security

### Models (`apps/resumes/models.py`)
- **`Resume`** — `id` (UUID pk), `edit_token` (secret, `secrets.token_urlsafe(32)`), `session_key`
  (device), `parent` (FK self, for per-job variants), `title`, `data` (JSON Resume), `original_data`
  (pre-enhancement snapshot for compare), `template_id`, `target_role`, `experience_level`,
  `job_description`, `ats_score`/`match_score` (cached JSON), timestamps.
- **`CoverLetter`** — `id` (UUID), FK `resume`, `body`, `job_description`, timestamps.

### JSON Resume schema (`apps/resumes/schema.py`)
- `empty_resume()` returns the full empty shape: `basics`, `work`, `education`, `skills`,
  `projects`, `certifications`, `awards`, `languages`, `volunteer`, `custom`.
- `validate_resume_data(data)` → list of errors (lenient on missing keys, strict on types present).
- `merge_into_resume(base, incoming)` → **new** dict (immutable merge, never mutates).

### No-login ownership model (`core/access.py`, `apps/resumes/services.py`)
A resume is owned by **(unguessable UUID id + secret `edit_token`)** — no accounts.
1. `POST /new/` creates a `Resume` with a random UUID + token; the token is stored in an **HttpOnly
   cookie** (`rf_t_<id>`, Secure in prod, SameSite=Lax, 90 days) and embedded in the editor URL as `?t=`.
2. Every protected view resolves the token via `resume_token()` (from `?t=` or the cookie) and calls
   `get_resume_or_404()` → `services.get_resume()`, which verifies with **`hmac.compare_digest()`**
   (constant-time). Mismatch → 404.
3. The **Django session** (`session_key`) ties drafts to a device → powers **My drafts**.
4. Privacy: `PrivacyHeadersMiddleware` sets `X-Robots-Tag: noindex` on `/r/*` and `/drafts/*`, and
   `Referrer-Policy: same-origin` so the secret `?t=` token never leaks to external origins.

---

## 9. AI layer (`apps/ai/`)

- **`provider.py`** — `LLMProvider` ABC with `complete()` (text) and `structured()` (JSON).
  `get_provider()` returns **OpenRouter** when `OPENROUTER_API_KEY` is set, else **Mock**.
  `is_demo_mode()` is true with no key.
- **`openrouter.py`** — `OpenRouterProvider` calls DeepSeek via the OpenAI SDK (model from
  `LLM_MODEL`, or `LLM_FREE_MODEL` if `USE_FREE_LLM`). `structured()` uses strict `json_schema` for
  small schemas, loose `json_object` for resume structuring. `_parse_json()` tolerates markdown
  fences/prose. Sends `X-Title: Rezoom` header. Retries 3×; returns `{}` on parse failure.
- **`mock.py`** — `MockProvider`: deterministic offline output (improves text, generates bullets,
  structures raw resume text heuristically). Powers demo mode + hermetic tests.
- **`services.py`** — high-level ops with `_safe_complete()` so **LLM failures degrade gracefully**
  (return original/empty, never crash): `improve_text`, `write_summary`, `generate_bullets`,
  `rewrite_to_jd`, `generate_cover_letter`, `prompt_edit`.
- **`enhance.py`** — `enhance_resume_data(data, jd=None)` (LLM enhance + local fallback +
  `_dropped_entries` guard so nothing real is lost); `ensure_ats_polish()` cleans artifacts and
  **surfaces** (never fabricates) skills if <6; `_clean_text()` strips quotes/markdown/placeholder
  metrics; `_clean_skills()` drops sentence-like "skills"; `summarize_improvements()` for the compare page.
- **`prompts.py`** — `SYSTEM_WRITER` + message builders encoding the **anti-fabrication** rules,
  strong-verb requirement, and the JD-tailoring clause (honest, no technical-washing).
- **`views.py`** — `improve` (30/m), `bullets` (30/m), `polish` (10/m).

---

## 10. ATS scoring (`apps/ats/`)

### Compatibility score — `compatibility.score_resume(data, template_meta)` (0–100, weighted)
| Dimension | Weight | Checks |
|---|---|---|
| Contact | 15 | name + email + phone present, valid email |
| Summary | 10 | 15–80 word professional summary |
| Experience | 15 | ≥1 work entry, every role has bullets |
| Action verbs | 15 | % of bullets starting with a strong verb (≥80% = ok) |
| Quantified | 15 | % of bullets containing a number (≥50% = ok) |
| Skills | 10 | ≥6 keywords |
| Education | 5 | education section present |
| Parse safety | 15 | template is single-column / ATS-safe |

Returns `{score, grade (Excellent/Good/Needs work/Incomplete), summary, dimensions[]}`; each
dimension has a `status` (ok/warn/fail) + actionable `fix`.

### JD match — `jd_match.score(data, jd_text)` (0–100)
Weights: **hard skills 55 + title 20 + education 10 + soft skills 15**. Uses `keywords.extract(jd)`
(curated `HARD_SKILL_TAXONOMY`, `SOFT_SKILLS`, frequency heuristic, title/education regex) vs
`keywords.resume_text(data)`. Returns matched/missing/suggested + an **over-optimization warning**
if ≥88. Constants (`STRONG_ACTION_VERBS`, `WEAK_OPENERS`, `CANONICAL_HEADINGS`, `STOPWORDS`) live in
`constants.py`. Endpoints: `score` (120/m), `tailor` (20/m, caps LLM rewrites at 25 bullets).

---

## 11. Templates, rendering & export

### Templates (`apps/templates_engine/`)
- **103 templates** (`registry.all_templates()`), **86 ATS-safe**, 8 categories: Academic,
  Creative, Executive, Minimal, Modern, Professional, Simple, Technical.
- Generated by combining **layout families** × **color themes**. Base HTML families live in
  `templates/resume_templates/`: `single_column.html`, `two_column.html`, `compact.html`,
  `timeline.html`, `header_banner.html` (+ shared `_parts/header.html`, `_parts/sections.html`).
- `TemplateMeta` carries `id, name, category, ats_safe, partial, accent, font, ats_risk, description`.
  Two-column sidebars are `ats_safe=False` with an `ats_risk` note.
- `render.py` — `render_resume_partial()` (editor preview), `render_resume_document()` (standalone
  HTML for export, inlines `resume.css`). **Same path for preview & export → no drift.**
- `samples.py` — sample data for previewing templates on an empty resume.
- `templatetags/resume_extras.py` — `skills_inline` filter (ATS-friendly inline skills).

### Export (`apps/exporting/`)
- **`render_browser.py`** — Playwright headless Chromium; **warm browser per worker thread**
  (thread-local), so first export ~2–4 s, then ~0.3–0.8 s. `html_to_pdf` (Letter, backgrounds),
  `html_to_png` (816×1056). Self-heals if the browser/loop dies.
- **`docx_builder.py`** — `build_docx(data, accent_hex)` → ATS-safe DOCX (single column, Calibri,
  standard headings, no tables).
- **`plain_text.py`** — `as_plain_text(data)` (the "ATS view").
- **`views.py`** — `download_menu` (60/m), `download_pdf`/`download_png` (20/m),
  `download_docx`/`download_txt` (30/m). PDF/PNG fall back to 503 if Chromium is unavailable.

---

## 12. Full route map

**Public / marketing** (indexable)
| Method | Path | Name | View |
|---|---|---|---|
| GET | `/` | `core:landing` | landing (build/enhance/check-ATS + instant ATS check) |
| GET | `/ats-resume-checker/` | `core:ats_checker` | ATS checker info page |
| GET | `/resume-templates/` | `core:resume_templates` | templates gallery (SEO) |
| GET | `/robots.txt` | — | `core.seo.robots_txt` |
| GET | `/sitemap.xml` | — | `core.seo.sitemap_xml` |

**Builder**
| Method | Path | Name |
|---|---|---|
| POST | `/new/` | `builder:start_new` |
| GET | `/drafts/` | `builder:my_drafts` |
| GET | `/r/<uuid>/edit/` | `builder:editor` |
| GET/POST | `/r/<uuid>/wizard/` | `builder:wizard` |
| POST | `/r/<uuid>/variant/` | `builder:create_variant` |
| GET | `/r/<uuid>/compare/` | `builder:compare` |
| POST | `/r/<uuid>/use-original/` | `builder:use_original` |

**Resume data**
| POST | `/r/<uuid>/autosave/` | `resumes:autosave` (120/m, 256 KB cap) |
| POST | `/r/<uuid>/set-template/` | `resumes:set_template` (60/m) |

**Templates** — GET `/r/<uuid>/templates/` → `templates_engine:gallery`

**Parsing** — GET/POST `/enhance/` → `parsing:upload` (10/m) · POST `/ats-check/` → `parsing:ats_check` (8/m)

**AI** — POST `/ai/r/<uuid>/improve/` (30/m) · `/ai/r/<uuid>/bullets/` (30/m) · `/ai/r/<uuid>/polish/` (10/m)

**ATS** — POST `/ats/r/<uuid>/score/` (120/m) · `/ats/r/<uuid>/tailor/` (20/m)

**Exporting** — GET `/r/<uuid>/download/` · `/download/pdf/` · `/download/png/` · `/download/docx/` · `/download/txt/`

**Cover letters** — GET `/r/<uuid>/cover-letter/` · POST `…/generate/` (15/m) · POST `…/save/` (60/m)

---

## 13. Project structure

```
AtsResumeBuilder/
├── manage.py                     # Django entrypoint
├── requirements.txt              # pinned deps
├── pytest.ini · conftest.py      # test config (forces Mock provider in tests)
├── gunicorn.conf.py              # gunicorn config (bind via GUNICORN_BIND env)
├── .env.example                  # config template (.env is gitignored)
├── README.md · DEPLOYMENT.md · REZOOM.md
├── resumeforge/                  # Django project (settings, urls, wsgi, asgi)
├── core/                         # landing, access.py, sessions.py, context.py, middleware.py, seo.py, views.py
├── apps/
│   ├── resumes/                  # models, schema, services, views, migrations, management/commands/purge_old_resumes.py
│   ├── builder/                  # wizard, editor, drafts, variants, compare
│   ├── parsing/                  # extract.py, structure.py, views.py (upload + ats_check)
│   ├── ai/                       # provider, openrouter, mock, services, enhance, prompts, views, context
│   ├── ats/                      # compatibility, jd_match, keywords, constants, views
│   ├── templates_engine/         # registry, render, samples, views, templatetags/
│   ├── exporting/                # render_browser, docx_builder, plain_text, views
│   └── coverletters/             # services, views
├── templates/                    # base.html, landing.html, builder/*, parsing/*, pages/*, resume_templates/*, seo/*
├── static/                       # css/app.css, css/resume.css, js/editor.js
├── tests/                        # 101 tests across the apps
└── deploy/                       # rezoom.service, nginx.conf, deploy.sh
```

---

## 14. Configuration (env vars)

Read by `resumeforge/settings.py` via django-environ. In `DEBUG` mode everything has safe defaults
(no `.env` needed locally). Production requires a real `SECRET_KEY`. See `.env.example`.

| Var | Default | Purpose |
|---|---|---|
| `DEBUG` | `True` | `False` in production (enables TLS redirect, HSTS, hashed static). |
| `SECRET_KEY` | (empty) | **Required in prod** (ephemeral auto-gen only in DEBUG). |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Prod: `rezoom.praritsidana.com`. |
| `CSRF_TRUSTED_ORIGINS` | (empty) | Prod: `https://rezoom.praritsidana.com`. |
| `OPENROUTER_API_KEY` | (empty) | Live AI; empty → demo/mock mode. |
| `LLM_MODEL` | `deepseek/deepseek-v4-flash` | Primary model. |
| `LLM_FREE_MODEL` | `deepseek/deepseek-chat-v3-0324:free` | Used when `USE_FREE_LLM=True`. |
| `USE_FREE_LLM` | `False` | Switch to the free model. |
| `GA_MEASUREMENT_ID` | (empty) | GA4 id (`G-XXXX`); empty → no analytics loaded. |
| `SITE_URL` | (empty) | Base URL for canonical/OG/sitemap. |

Other settings: upload cap **5 MB**, allowed types **PDF + DOCX**, SQLite DB, session-backed identity.

---

## 15. Local development

```bash
# from the project root
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python -m playwright install chromium     # for PDF/PNG export
python manage.py migrate
python manage.py runserver                # http://127.0.0.1:8000
```
- No `.env` needed to run (demo/mock AI). For live AI, create `.env` with `OPENROUTER_API_KEY=...`.
- See also the memory note `run-commands.md`.

---

## 16. Testing

```bash
python -m pytest -q                # 101 tests (pytest + pytest-django)
```
- `conftest.py` forces the **Mock** LLM provider so tests are hermetic (no network/API key).
- Coverage spans every app: ai, ats, parsing, builder, resumes, templates_engine, exporting,
  coverletters, core. A gitignored `_live_walkthrough.py` drives a Playwright smoke walk when needed.

---

## 17. Deployment (production)

**Where:** Hostinger VPS · Ubuntu 24.04 · root @ `187.127.132.106` · domain
`rezoom.praritsidana.com`. The VPS hosts ~7–8 other apps, so **everything is namespaced as
`rezoom` and isolated** — folder `/var/www/rezoom`, systemd service `rezoom`, gunicorn on
`127.0.0.1:8011`, its own nginx server block. Nothing else on the box is touched.

**Stack on the box:** gunicorn (systemd unit `rezoom`, port 8011) ← nginx reverse-proxy (80+443) ←
Let's Encrypt TLS (certbot, auto-renews). Static served by WhiteNoise. DB = SQLite in the project dir.

**Deploy artifacts** (in `deploy/`, copied into place on the box):
- `rezoom.service` → `/etc/systemd/system/rezoom.service` (User=root, WorkingDirectory=/var/www/rezoom,
  `GUNICORN_BIND=127.0.0.1:8011`, ExecStart gunicorn `resumeforge.wsgi`).
- `nginx.conf` → `/etc/nginx/sites-available/rezoom` (symlinked into `sites-enabled/`), proxies to
  `127.0.0.1:8011`, `client_max_body_size 6M`, `proxy_read_timeout 120s`. certbot adds the 443 block.
- `deploy.sh` → the one-command update script.

**First-time deploy (run on the VPS as root):**
```bash
# 1. system deps (idempotent)
apt update && apt install -y python3-venv python3-pip git nginx

# 2. clone into an isolated folder
mkdir -p /var/www && cd /var/www
git clone https://github.com/prarit0097/ResumeForge.git rezoom && cd rezoom

# 3. venv + deps + Chromium
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install --with-deps chromium

# 4. .env (auto-gen SECRET_KEY; paste the real OpenRouter key)
cat > .env <<EOF
DEBUG=False
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key as k; print(k())")
ALLOWED_HOSTS=rezoom.praritsidana.com
CSRF_TRUSTED_ORIGINS=https://rezoom.praritsidana.com
OPENROUTER_API_KEY=PASTE_YOUR_OPENROUTER_KEY_HERE
LLM_MODEL=deepseek/deepseek-v4-flash
SITE_URL=https://rezoom.praritsidana.com
GA_MEASUREMENT_ID=
EOF
nano .env   # replace the placeholder key

# 5. DB + static
python manage.py migrate
python manage.py collectstatic --noinput

# 6. gunicorn service
cp deploy/rezoom.service /etc/systemd/system/rezoom.service
systemctl daemon-reload && systemctl enable --now rezoom
systemctl status rezoom --no-pager      # expect: active (running)

# 7. nginx (new block; doesn't touch other apps)
cp deploy/nginx.conf /etc/nginx/sites-available/rezoom
ln -s /etc/nginx/sites-available/rezoom /etc/nginx/sites-enabled/   # skip if "File exists"
nginx -t && systemctl reload nginx

# 8. DNS A record: rezoom -> 187.127.132.106  (set where praritsidana.com DNS lives)
dig +short rezoom.praritsidana.com       # must return 187.127.132.106 before certbot

# 9. HTTPS
apt install -y certbot python3-certbot-nginx
certbot --nginx -d rezoom.praritsidana.com   # choose redirect HTTP->HTTPS
```

**DNS:** an **A record** `rezoom` → `187.127.132.106` (subdomain of `praritsidana.com`).

> **Gotcha (seen on first deploy):** re-running `cp deploy/nginx.conf` overwrites certbot's `443`
> block. If HTTPS suddenly 504s after a config copy, re-run
> `certbot --nginx -d rezoom.praritsidana.com` and pick **1 (reinstall)** to re-attach the SSL block.

---

## 18. Updating / redeploying

Normal loop — **edit locally → commit → push → pull on the VPS**:
```bash
# local
git add -A && git commit -m "..." && git push origin main

# on the VPS
cd /var/www/rezoom
chmod +x deploy/deploy.sh        # first time only
./deploy/deploy.sh               # git pull + pip install + playwright + migrate + collectstatic + restart rezoom
```
`deploy.sh` runs: `git pull --ff-only` → install deps → ensure Chromium → `migrate` →
`collectstatic` → `systemctl restart rezoom`.

---

## 19. Maintenance & operations

- **Logs:** `journalctl -u rezoom -n 100 -f` (app) · `/var/log/nginx/` (nginx) ·
  `/var/log/letsencrypt/` (certbot).
- **Restart / status:** `systemctl restart rezoom` · `systemctl status rezoom`.
- **TLS renewal:** automatic via the certbot systemd timer (`systemctl list-timers | grep certbot`).
- **Purge old drafts (no-login hygiene):** `python manage.py purge_old_resumes --days 90`
  (add `--dry-run` to preview). Good as a periodic cron.
- **Change the port (if 8011 clashes):** edit `GUNICORN_BIND` in the unit + `proxy_pass` in nginx,
  then `daemon-reload && systemctl restart rezoom && systemctl reload nginx`.
- **Enable analytics later:** set `GA_MEASUREMENT_ID=G-XXXX` in `.env` → `systemctl restart rezoom`.

---

## 20. SEO

- `core/seo.py` — `robots_txt` (disallows `/r/`, `/drafts`, `/ai/`, `/ats/`, `/new/`) + `sitemap_xml`
  over `PUBLIC_PAGES` (landing, ats_checker, resume_templates, enhance).
- `templates/base.html` — per-page `<title>`/meta/canonical, Open Graph + Twitter, **JSON-LD**
  WebApplication (free, price 0) + FAQ schema, GA4 gtag (masks resume id, strips the `?t=` token).
- `PrivacyHeadersMiddleware` keeps private `/r/*` & `/drafts` pages `noindex`.

---

## 21. Changelog

> Append newest at the top. Keep entries one line. Update this whenever the app changes.

- **2026-06-23** — Removed the "My drafts" link from the header nav (route/page `builder:my_drafts` still exists, just not surfaced).
- **2026-06-23** — Renamed product to **Rezoom**; unified landing into a 3-card row (Build / Enhance
  / Check ATS) with an on-theme result panel + loading-lock; deployed to production at
  https://rezoom.praritsidana.com (Hostinger VPS, `/var/www/rezoom`, service `rezoom`, port 8011,
  nginx + Let's Encrypt). Added this `REZOOM.md`.
- **2026-06-21/22** — Deep SEO foundation (robots/sitemap/JSON-LD/GA4/meta); instant landing-page ATS
  check; deployment artifacts.
- **2026-06-20 (and earlier)** — Core app: build + enhance flows, AI (OpenRouter/DeepSeek), ATS &
  JD scoring, 103 templates, PDF/DOCX/PNG/TXT export, guided editor, before/after compare, honest
  anti-fabrication output, no-login model. (See `git log` for full history.)

---

## 22. Quick-reference card

| Thing | Value |
|---|---|
| Live URL | https://rezoom.praritsidana.com |
| Repo | https://github.com/prarit0097/ResumeForge |
| VPS | Hostinger, Ubuntu 24.04, root @ 187.127.132.106 |
| App folder (VPS) | `/var/www/rezoom` |
| Service | `systemctl {status,restart} rezoom` (gunicorn, port 8011) |
| nginx | `/etc/nginx/sites-available/rezoom` → 80+443 → 8011 |
| Update | `cd /var/www/rezoom && ./deploy/deploy.sh` |
| Logs | `journalctl -u rezoom -f` |
| Local run | `python manage.py runserver` (after venv + migrate) |
| Tests | `python -m pytest -q` (101) |
| Templates | 103 (86 ATS-safe) |
| AI model | `deepseek/deepseek-v4-flash` via OpenRouter |
| DB | SQLite (`db.sqlite3`) |
| Django package | `resumeforge` (product brand = Rezoom) |

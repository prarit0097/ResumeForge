# ResumeForge

A free, no-login, **ATS-optimized AI resume builder**. Build a new resume with AI,
or upload an existing one to enhance it — score it against real ATS rules, tailor it
to any job description, pick from **100+ templates**, and download clean **PDF / Word /
PNG** files. No accounts, no watermarks, no paywall.

> Honest by design: ATS is a searchable database, not a judge. ResumeForge guarantees
> a **parse-safe structure** and surfaces the **right real keywords** so a human
> recruiter actually finds you — it never keyword-stuffs.

## Features

- **Two flows:**
  - **Build new:** guided intake (Step 1) → **pick a template** from 103 options with live sample previews (Step 2) → editor in that template.
  - **Enhance existing:** upload a PDF/DOCX (and, optionally, paste a **target job description**) → AI parses + improves it in one pass, **tailoring to the JD when given** (real skills only, never fabricated) → a **before/after comparison** showing the ATS-score jump, the JD-match jump, exactly what changed, and why it helps → continue editing or keep the original.
- **AI content** (OpenRouter → DeepSeek): generate/improve bullets, write summaries, tailor to a job description, edit by prompt. Works in **offline demo mode** with no API key.
- **Live ATS compatibility score** (0–100) with specific, actionable fixes — shown the moment the editor opens.
- **JD-match score** with an honest missing-keyword report and anti-stuffing warnings.
- **One-click "Tailor to this job."**
- **103 distinct templates** across 8 categories (ATS-safe single-column + creative two-column, each clearly labelled). Every template renders the same data; switch anytime with no data loss.
- **Export:** text-selectable PDF, ATS-clean DOCX, PNG, and a "what the ATS sees" plain-text preview. (PDF/PNG reuse a warm headless-Chromium per worker for fast repeat downloads.)
- **Cover letter generator** + **tailored resume variants**.
- Mobile-friendly (fit-to-width previews), live preview, autosave, shareable resumable edit links — all without an account.

## Tech stack

Django 5 · OpenRouter/DeepSeek (OpenAI SDK) · Playwright (PDF/PNG) · python-docx ·
pdfplumber · htmx + Alpine.js + Tailwind. See [docs/superpowers/specs](docs/superpowers/specs) for the full design.

## Setup (Windows / macOS / Linux)

```bash
# 1. Create and activate a virtualenv
python -m venv .venv
# Windows:  .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the headless browser used for PDF/PNG export
playwright install chromium

# 4. (Optional) configure environment
cp .env.example .env        # then edit .env

# 5. Migrate and run
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/.

### Enabling live AI

The app works fully **without any key** (AI runs in deterministic demo mode). For
live AI generation, get an [OpenRouter](https://openrouter.ai/) API key and set it in
`.env`:

```
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=deepseek/deepseek-chat-v3-0324
# Set USE_FREE_LLM=True to use the free (rate-limited) DeepSeek model.
```

Never commit `.env`. Restart the server after changing it.

## Tests

```bash
pytest
```

## Maintenance

```bash
python manage.py purge_old_resumes --days 90      # delete stale anonymous drafts
python manage.py purge_old_resumes --dry-run
```

## Project layout

```
apps/
  resumes/         # Resume/CoverLetter models, schema, services (no-login token auth)
  builder/         # wizard + editor + drafts views
  parsing/         # upload -> text extraction -> LLM structuring
  ai/              # swappable LLM provider (OpenRouter / Mock) + content services
  ats/             # ATS compatibility + JD-match scorers (pure-Python, tested)
  templates_engine/# template registry + render + gallery (103 templates)
  exporting/       # PDF/PNG (Playwright), DOCX (python-docx), plain text
  coverletters/    # AI cover letter generation
core/              # shared access guard, sessions, middleware
templates/, static/
```

## Security notes

- No user accounts. A resume is reached only via its unguessable UUID + secret
  `edit_token` (constant-time compared). Resumes are `noindex`; `Referrer-Policy:
  same-origin` keeps the token URL off external sites while keeping CSRF working.
- Mutating + AI + export endpoints are rate-limited; uploads are type/size validated
  and parsed in memory; AI inputs are length-capped (cost/prompt-injection guard).
- Per-resume token cookies are `HttpOnly` (and `Secure` when not `DEBUG`); secure
  cookies, HSTS and SSL-redirect activate automatically outside `DEBUG`.
- All config via environment; no secrets in code; `SECRET_KEY` has no insecure default.

### Before deploying to production (hardening checklist)

- Set `DEBUG=False`, a real `SECRET_KEY`, and an explicit `ALLOWED_HOSTS`.
- Self-host or pin-with-SRI the CDN scripts (Tailwind/htmx/Alpine) and add a
  Content-Security-Policy; build Tailwind via CLI instead of the CDN.
- Configure a Redis/memcached cache and a forwarded-IP resolver so `django-ratelimit`
  works behind a reverse proxy.
- Self-host the WOFF2 fonts (Inter/Fraunces) so PDF export needs no outbound network.
- Run PDF/PNG export in a Celery worker (it's synchronous Chromium today).
- **Rotate the OpenRouter key and `SECRET_KEY` if `.env` was ever shared.**

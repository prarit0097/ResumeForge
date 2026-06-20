# How ATS Parse and Score Resumes — Research Report

> Product research to inform an ATS-optimized AI resume builder.
> Date: 2026-06-20. Sources cited inline; key authoritative anchors are Jobscan (vendor with a 2.5M-scan dataset), Enhancv (the only source with a controlled parsing test and hard percentages), the Ladders 2018 eye-tracking study, and the commercial parsing engines (Sovren/Textkernel, HireAbility) that actually power many ATS platforms.

---

## TL;DR — what to build

1. **Parse-ability is the gate.** If the ATS cannot extract clean text, nothing else matters. The dominant failure mode is **reading order** broken by multi-column layouts, tables, and text boxes. Single-column is the safe default.
2. **Keywords are the score.** ATS rank candidates by matching job-description (JD) keywords — heavily weighted toward **hard skills** and the **exact job title**. Assume dumb exact-match; mirror the JD's literal phrasing.
3. **Two scorers to build:** (a) an **ATS-compatibility checker** (deterministic, rule-based on the file/structure) and (b) a **JD-match scorer** (keyword extraction + weighted matching against a pasted JD). Specs in §6.
4. **Target a 75–80% JD match** — high enough to pass filters, low enough to avoid robotic over-optimization.

---

## 1. How ATS Parsing Works

### 1.1 The pipeline
A resume parser sits between the upload and the recruiter's database: file in → text extraction → sectioning → named-entity recognition (NER) → structured fields stored and shown to recruiters ([HireAbility](https://www.hireability.com/hireability-resume-job-parsers/), [Resume Optimizer Pro](https://resumeoptimizerpro.com/blog/how-resume-parsers-actually-work)). Each stage's failure cascades into the next. Best commercial parsers reach ~**87% field-level accuracy vs ~96% for humans** ([Resume Optimizer Pro](https://resumeoptimizerpro.com/blog/how-resume-parsers-actually-work)).

### 1.2 Text extraction: PDF vs DOCX, and OCR
- **DOCX is the most reliable to extract.** A `.docx` is XML under the hood, so the parser reads headings, paragraphs, and lists directly from the markup — no ambiguity about reading order in a single-column doc ([Adeptiq](https://adeptiq.be/blog/what-is-cv-parsing-how-ai-reads-resumes-for-you)).
- **Text-based PDF carries a text layer** (text objects + bounding-box coordinates). Parsers extract that layer, but because it stores objects by position rather than logical order, reading order can be reconstructed wrong — especially in multi-column layouts ([Unstract](https://unstract.com/blog/guide-to-ai-resume-parsing-with-unstract/), [jobshinobi](https://www.jobshinobi.com/blog/resume-scanner-pdf-vs-docx-which-is-better)).
- **Scanned / image-only PDFs fail.** No text layer; the file is "just images to the software" ([smallpdf](https://smallpdf.com/blog/do-applicant-tracking-systems-prefer-resumes-in-pdf-format)). Recovery requires OCR, which many older parsers don't run, and quality varies ([Affinda](https://www.affinda.com/blog/ocr-resume-scanning/), [Eden AI](https://www.edenai.co/post/resume-parsing-ocr-which-solution-to-choose)). Modern AI parsers use text-layer extraction first, OCR (and LLMs) as fallback ([Unstract](https://unstract.com/blog/guide-to-ai-resume-parsing-with-unstract/)).
- **Design-tool trap:** PDFs from InDesign/Canva often bake text into graphics/vectors, so extraction fails even though the file is technically a PDF, not a scan ([jobshinobi](https://www.jobshinobi.com/blog/resume-scanner-pdf-vs-docx-which-is-better)).

**The real danger is not "PDF" — it's "image PDF" or "design-tool PDF."** Clean text-based PDF and DOCX parse comparably in modern testing.

### 1.3 What breaks parsing
The unifying failure is **reading order**: most parsers read a continuous linear stream, left-to-right, top-to-bottom ([Jobscan](https://www.jobscan.co/blog/resume-tables-columns-ats/)).

| Element | What goes wrong | Source |
|---|---|---|
| **Multi-column layouts** | "Top failure mode by a wide margin" (~34% of errors). Parser reads across both columns line-by-line, interleaving left+right into nonsense. | [Resume Optimizer Pro](https://resumeoptimizerpro.com/blog/how-resume-parsers-actually-work), [Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/) |
| **Tables** | Parser "slices through the table horizontally"; cells extracted in non-logical order → garbled rows. | [Jobscan](https://www.jobscan.co/blog/resume-tables-columns-ats/) |
| **Text boxes** | Treated as floating layers outside main flow; many parsers ignore them → content invisible. | [Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/) |
| **Headers/footers** | "Many ATS parsers ignore these layers entirely." TopResume: ~25% of ATS fail to read contact info placed there. | [Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/) |
| **Images / graphics / skill bars** | Unreadable. "80% Java" skill bars convey nothing. | [Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/) |
| **Icons / emoji** | Contact icons lose underlying data; cause character-substitution errors. Replace with text labels ("Phone:"). | [Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/) |
| **Decorative/embedded fonts** | Drop to placeholder glyphs → "Pro?le" or `[NULL]`. | [Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/), [airesume](https://airesume.guru/blog/special-characters-that-break-ats-what-to-avoid-on-your-resume) |
| **Special chars / decorative bullets** | ★ → ➤, smart quotes, em dashes, math symbols (≤ ½) skipped/misread → lost keywords, merged bullets. | [airesume](https://airesume.guru/blog/special-characters-that-break-ats-what-to-avoid-on-your-resume) |

**Self-test (worth replicating in the product):** paste the resume into plain-text Notepad/TextEdit. If it scrambles there, the ATS sees the same scramble ([airesume](https://airesume.guru/blog/special-characters-that-break-ats-what-to-avoid-on-your-resume)).

### 1.4 Single-column vs two-column — the real nuance
Vendor guidance (Jobscan) is absolute: use single-column, avoid columns/tables/text boxes (derived from analyzing 2.5M+ scans) ([Jobscan templates](https://www.jobscan.co/blog/20-ats-friendly-resume-templates/)).

Independent testing shows a **graded reality, not a hard break** (Enhancv, tested through Indeed's ATS) ([Enhancv myth-busting](https://enhancv.com/blog/busting-ats-myths/)):
- Single-column ~**93%** vs double-column ~**86%** average parse rate. Single is modestly safer.
- But well-built double-column from the best builders scored *higher* (Enhancv 98% vs 95% single).
- **PDF vs DOC performed comparably**; colors and fonts "generally don't tip the scales"; the real damage comes from columns/tables/graphics/symbols.
- Canva's infographic designs averaged only **73%** vs **85%** for its simple ones.

**How you build columns matters:** a borderless 2-column *table* parses more reliably than Word's native Columns feature, and the cardinal rule is to keep contact/experience/education **out of a sidebar** ([Resumemate](https://www.resumemate.io/blog/are-two-column-resumes-ats-friendly-2026-tests--safe-alternatives/)).

**Resolution:** Two-column does not universally break ATS, but it raises risk, the risk is parser-dependent, and the failure (sidebar dropped, columns interleaved) is severe when it happens. **Single-column is the safe default precisely because it removes that variance** — recommend it for the product's default templates.

### 1.5 Field mapping
After extraction, NLP sectioning + NER populate a fixed schema: contact (name, email, phone, LinkedIn/URL), work history (employer, title, start/end dates, location, responsibilities), education (institution, degree, field, year), skills/certifications/languages, summary ([Candidately](https://www.candidately.com/glossary/resume-parsing)). Commercial engines (Sovren/Textkernel, HireAbility) tag hundreds of entity types. Standard section headings and normalized dates are critical to correct mapping (see §2).

### 1.6 Older vs modern ATS (the architectural distinction that matters)
Source: [Resume Optimizer Pro parser comparison](https://resumeoptimizerpro.com/blog/how-resume-parsers-actually-work) (directional — SEO blog, not vendor docs), corroborated by Jobscan examples.

| ATS | Parsing behavior | Recruiter view |
|---|---|---|
| **Taleo (Oracle)** | Oldest/strictest. Exact-match labels, strict dates, linear single-column only. Loses entries, scrambles tables. | Parsed profile = primary |
| **Workday** | Clean on standard DOCX; strict dates; "fails hard" on columns/tables. | Parsed profile = primary |
| **iCIMS** | Textkernel/Sovren-based. Reads full page width → two-column collapses (**89% single-col → 67% two-col**). | Parsed profile = primary |
| **Lever** | Forgiving on contact; **silently drops sidebars** (empty skills array reported). | Mixed |
| **Greenhouse** | Strongest parser (Sovren); flexible dates; recruiter usually reads the **actual PDF**, parsed fields are metadata. Every app reaches a human. | Original doc = primary |

**Key insight:** In Taleo/Workday/iCIMS the *parsed profile is what the recruiter sees*, AND they're the strictest parsers — a double penalty for fancy layouts. In Greenhouse/Lever the human sees the original doc, so layout tolerance is higher — but database **search still depends on clean parsing**. Build for the strict case.

---

## 2. ATS-Safe Formatting Rules

### 2.1 Section headings — use EXACT standard names
ATS categorize content by recognizing conventional labels ([Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/), [Jobscan templates](https://www.jobscan.co/resume-templates/ats-templates), [Enhancv](https://enhancv.com/blog/resume-headings/)):

**Safe (use these):**
- `Work Experience` or `Professional Experience` (both recognized)
- `Education`
- `Skills`
- `Certifications`
- `Summary` / `Professional Summary`

**Unsafe (cause sections to be missed/miscategorized):** "My Journey," "Where I've Worked," "What I Bring to the Table," "My Expertise," "The Toolkit." Jobscan: with non-standard headings, "your 'Work Experience' might be categorized under 'Education,' or your 'Professional Summary' could disappear."

### 2.2 Dates
Two reliable formats, applied **identically across all entries** ([Jobscan dates](https://www.jobscan.co/blog/resume-dates/), [ATS Verification](https://atsverification.com/blog/how-to-format-dates-resume-ats/)):
- **`MM/YYYY`** → `03/2022` (max compatibility)
- **`Month YYYY`** → `January 2022` / `Jan 2022` (more readable; also widely accepted)

Ranges: `Jan 2021 – Mar 2023` or `01/2021 – 03/2023`, **en-dash** separator (the word "to" can confuse parsers). Include month + year on every entry.

**Avoid:** mixing formats across entries (breaks tenure calculation); apostrophe/two-digit years (`'21`); day-first (`DD/MM/YYYY`). Parser-specific gotchas: iCIMS recognizes "Present" but fails "Ongoing/Now/Current"; Workday normalizes "March 2022" but fails "Mar. 2022" ([Resume Optimizer Pro](https://resumeoptimizerpro.com/blog/how-resume-parsers-actually-work)).

### 2.3 Bullets
- **Safe:** standard round bullet `•`, hyphen `-`, asterisk `*`.
- **Break parsing:** stars (★), arrows (→ ➤), diamonds, checkmarks, emoji, smart quotes, em dashes, custom dingbats → can "merge bullet points into a block of text" ([Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/), [airesume](https://airesume.guru/blog/special-characters-that-break-ats-what-to-avoid-on-your-resume)).

### 2.4 Fonts & sizes
- **Safe:** Calibri, Arial, Helvetica, Georgia, Times New Roman, Garamond, Cambria ([Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/)). A 2026 study: Calibri 11pt ~99% parse-completeness, Arial 10.5pt ~98%, classic serifs ~89.7% (loss on older Taleo/iCIMS where thin serifs trigger OCR fallback) ([Resume Optimizer Pro fonts](https://resumeoptimizerpro.com/blog/best-resume-fonts)). **Default to Calibri or Arial.**
- **Sizes:** body 10–12pt (11pt sweet spot); headings 12–16pt, often bold.
- **Avoid:** custom/decorative/embedded fonts (corruption → `[NULL]`).

### 2.5 File format — report both positions honestly
Genuine vendor disagreement:
- **Jobscan (2025) recommends PDF** "unless the job posting specifically requests .docx," because most ATS "read and parse PDF resumes more accurately," and some had issues parsing special characters in `.docx` ([Jobscan PDF vs Word](https://www.jobscan.co/blog/resume-pdf-vs-word/)). **Assumes a text-based PDF.**
- **Earlier analysis + conservative camp: `.docx` is the safest default** for backward compatibility with older parsers.

**Product recommendation:** (1) honor any format the posting specifies; (2) otherwise export a **clean text-based PDF by default**, offer **DOCX** as the conservative alternative; (3) generate both. Never output image/scanned/design-baked PDFs.

### 2.6 Layout — avoid
Headers/footers for contact info (keep contact in the body), tables, multi-column, text boxes, images/graphics/logos/headshots, icons/emoji, decorative borders. Use **single-column** with content in the main body ([Jobscan](https://www.jobscan.co/blog/ats-formatting-mistakes/), [Jobscan tables/columns](https://www.jobscan.co/blog/resume-tables-columns-ats/)).

---

## 3. Keyword Optimization

### 3.1 How matching works — assume the dumbest engine
Three escalating levels exist across real platforms ([resumegyani](https://resumegyani.in/ats-guides/ats-keyword-matching-algorithm), [Jobscan](https://www.jobscan.co/blog/top-resume-keywords-boost-resume/)):
1. **Exact string match** (basic): "machine learning" ≠ "ML."
2. **Fuzzy/stemming**: handles plurals/tenses — but Jobscan warns many ATS still miss singular vs plural.
3. **Semantic** (NLP, e.g. Jobscan's own): understands "project management" ≈ "managed projects."

Because you can't know the engine, **assume exact-match and mirror the JD's literal phrasing.** Separately, recruiters run **Boolean searches** (AND/OR/NOT, quoted exact phrases, wildcards) over the parsed database — rewarding exact phrasing a recruiter would type ([Indeed Boolean](https://www.indeed.com/career-advice/career-development/boolean-search-strings)).

### 3.2 Hard vs soft skills
Hard skills dominate ([Resume Optimizer Pro](https://resumeoptimizerpro.com/blog/soft-skills-vs-hard-skills), [Jobscan tutorial](https://www.jobscan.co/jobscan-tutorial)):
- ATS scan for hard skills as exact-match keywords; soft skills are recognized but weighted far less.
- "Hard skills get your resume opened. Soft skills get you hired."
- Vague soft-skill adjectives ("excellent communicator") are "nearly invisible to parsers." Demonstrate soft skills inside quantified bullets.
- Suggested mix: ~**70% hard / 30% soft** in the skills section.

### 3.3 Which JD keywords matter most (priority order)
1. **Exact job title** — most-searched term; include near the top. Jobscan: exact title → **10.6× more likely** to get an interview.
2. **Frequently repeated terms** — most important keywords appear most often in the JD. **If a term appears 3+ times, include it** (if true).
3. **Placement in JD** — title/requirements outrank "nice-to-have." Weight by frequency × placement × semantic importance ([TheLadders](https://www.theladders.com/career-advice/how-to-find-keywords-in-a-job-description-for-your-resume), [Resumly](https://www.resumly.ai/blog/analyzing-job-descriptions-to-extract-highvalue-keywords)).

Coverage target: ≥80% of required keywords, ≥50% of preferred. Typical resume carries 10–20 targeted keywords.

### 3.4 Density & stuffing
- **Ideal:** each important keyword **2–3 times across different sections**, naturally ([resumegyani](https://resumegyani.in/ats-guides/ats-keyword-matching-algorithm)).
- **Stuffing** = keyword-loading with no regard for the human reader; Jobscan caps the target ~80% to avoid "robotic" resumes that fail human review ([Jobscan stuffing](https://www.jobscan.co/blog/resume-keyword-stuffing/), [Jobscan match rate](https://www.jobscan.co/blog/what-jobscan-match-rate-should-i-aim-for/)).
- **White-text stuffing fails and is dangerous:** many ATS dump all parsed text to a profile page exposing hidden words; density/color analysis flags it; recruiters highlight-all or use "Inspect Document." Result: rejection, offer revocation, blacklisting ([Cangrade](https://www.cangrade.com/blog/talent-acquisition/white-fonting-what-it-is-why-its-risky-and-how-employers-should-respond/), [airesume](https://airesume.guru/blog/hidden-keywords-white-text-on-resumes-the-myth-that-gets-you-blacklisted)). **Never implement this; actively warn against it.**

### 3.5 Exact-match vs synonyms; acronyms
- **Mirror the JD's exact wording** when it's true, "because ATS systems don't reliably recognize synonyms" ([Jobscan](https://www.jobscan.co/blog/top-resume-keywords-boost-resume/)).
- **Acronyms: include BOTH** spelled-out and acronym, first use as `Search Engine Optimization (SEO)` ([Careerflow](https://www.careerflow.ai/blog/resume-keywords)).

### 3.6 Where keywords go
Professional summary/headline (weighted heavily; lead with target title + top 3–4 keywords) → Skills section (software, tools, soft skills) → Work-experience bullets (action + keyword + result) ([LinkedIn](https://www.linkedin.com/top-content/career/resume-tips/resume-keywords-for-ats-and-recruiters/), [Jobscan](https://www.jobscan.co/blog/top-resume-keywords-boost-resume/)).

### 3.7 How Jobscan computes its match rate
1–100% score vs a pasted JD ([Jobscan tutorial](https://www.jobscan.co/jobscan-tutorial), [Jobscan match rate](https://www.jobscan.co/blog/what-jobscan-match-rate-should-i-aim-for/)):
- **Weighting order:** (1) hard skills [much heaviest], (2) education level [only if JD requires an advanced degree], (3) job title, (4) soft skills, (5) other keywords. Shows JD-mention-count vs resume-mention-count per skill.
- **Report sections:** searchability, hard skills, soft skills, recruiter tips, formatting.
- **Not in the score:** word count and measurable results (shown as separate tips).
- **Target: ≥75% minimum, ~80% sweet spot.** Above ~80% risks over-optimization.

---

## 4. ATS Scoring — Dimensions & Implementable Rubric

### 4.1 What real checkers evaluate
**Enhancv** — most granular published model: **27 checks / 7 categories** (ATS essentials, sections, content quality, job tailoring, recruiter red flags, bias, seniority/impact); score = % parsed content + count of issues; **>80 = good** ([Enhancv checker](https://enhancv.com/resources/resume-checker/)).
**Jobscan** — keyword/skill-match centric; hard vs soft breakdown; **75% min / 80% sweet spot** ([Jobscan](https://www.jobscan.co/blog/what-jobscan-match-rate-should-i-aim-for/)).
**Resume Worded** — Impact (action verbs, quantification, weak-phrasing flags), Brevity, Style; **target ≥80** ([Resume Worded](https://resumeworded.com/resume-bullet-points)).

### 4.2 Proposed scoring rubric (implement this)
Two separate scores — keep them distinct so users understand "will it parse?" vs "does it match THIS job?"

**Score A — ATS Compatibility (0–100), JD-independent.** This is a *gate*; cap the overall product score if this is low.

| Dimension | Weight | How to measure |
|---|---:|---|
| File type & integrity | 12 | Text-based PDF or DOCX = full; image/scanned PDF or empty text layer = 0 |
| Single-column / reading order | 18 | Detect columns, tables, text boxes; plain-text round-trip test preserves order |
| Standard section headings | 14 | Match against canonical set (§2.1); each missing/non-standard heading deducts |
| Contact info parseable | 12 | Email + phone present **in body**, not header/footer; valid email regex, ≥10-digit phone |
| Safe fonts | 8 | Embedded font names ∈ safe list; flag custom/decorative |
| Safe bullets & characters | 8 | No decorative bullets/emoji/smart-quotes/math symbols; flag char-substitution risk |
| No images/graphics/icons for content | 10 | Detect skill-bar images, icon-encoded contact, headshots |
| Consistent parseable dates | 10 | All entries match one format (§2.2); no mixed/apostrophe/`to`-separator |
| Length / word count | 8 | 1 page ≤2 yrs exp; ≤2 pages senior; ~475–600 words optimal |

**Score B — JD Match (0–100), requires a pasted JD.** Mirrors Jobscan's weighting.

| Dimension | Weight | How to measure |
|---|---:|---|
| Hard-skill keyword match | 45 | % of JD hard skills present (exact + stemmed); weight each by JD frequency × placement |
| Exact job title present | 15 | Target title appears near top of resume |
| Soft-skill match | 10 | % of JD soft skills demonstrated (prefer in-bullet over listed) |
| Other keyword/coverage | 10 | Remaining JD terms (tools, certs, methodologies) |
| Education/qualification match | 8 | Only weighted if JD specifies a degree/cert; else redistribute |
| Keyword placement quality | 7 | Top keywords appear in summary + skills + ≥1 bullet, not stuffed in one block |
| Over-optimization penalty | −up to 5 | Penalize density >3× per keyword / unnatural repetition / hidden text |

**Content-quality sub-score (feeds Score A or shown separately):** quantified-achievement ratio (% of bullets with a number), strong-vs-weak action-verb ratio, readability (sentence length / grade level), repetition/filler/buzzword flags, spelling & grammar.

**Thresholds to surface in UI:** JD match ≥75 (pass), ≥80 (strong), >88 flag over-optimization; Compatibility ≥85 to call "ATS-safe."

---

## 5. Resume Content Best Practices

### 5.1 Bullet formula
**Action verb + task/context + quantified result** ([Resume Worded](https://resumeworded.com/resume-bullet-points)):
- "Responsible for implementing features" → **"Implemented 10+ features that increased app engagement time 2×."**
- "Helped reduce support calls" → **"Led transition to paperless system, reducing labor costs 30%."**
Quantify with: %, revenue/growth, time saved, scope (team size, users, participants).

### 5.2 Summary vs objective
- **Summary** (looks back; experienced / same field): 3–5 sentences, open with title + years of experience, include metrics + JD keywords. Resumes with summaries reportedly get **+340% callbacks** vs objectives ([Indeed](https://www.indeed.com/career-advice/resumes-cover-letters/resume-summary-vs-objective)).
- **Objective** (looks forward; entry-level / career changer): 1–2 sentences.

### 5.3 Tailoring & recruiter behavior
- Tailor every application; mirror JD language; include exact title; if a keyword appears 3+ times in the JD, include it ([Jobscan tailor](https://www.jobscan.co/blog/tailor-resume-job-description/)).
- **Recruiters spend ~7.4 seconds** on the initial scan (Ladders 2018 eye-tracking, up from 6s in 2012), skimming in an E/F pattern for titles, companies, dates, headings, keywords ([Ladders study](https://www.theladders.com/static/images/basicSite/pdfs/TheLadders-EyeTracking-StudyC2.pdf) via [HR Dive](https://www.hrdive.com/news/eye-tracking-study-shows-recruiters-look-at-resumes-for-7-seconds/541582/)). Favor clear sections, bold headings, white space.

### 5.4 Length
~1 page per 10 years of experience; 0–2 yrs → 1 page; senior/exec → 2 pages. 2025 survey of 1,013 HR pros: 82% say 1–2 pages, 51% prefer two; ResumeGo: recruiters 2.3× prefer two-page. Optimal word count ~475–600 ([Enhancv length](https://enhancv.com/blog/how-long-should-a-resume-be/), [Monster](https://www.monster.com/career-advice/resume/one-page-vs-two-page-resume)).

### 5.5 Action verbs
- **Strong:** Spearheaded, Directed, Orchestrated, Pioneered, Accelerated, Delivered, Optimized, Transformed, Engineered, Streamlined, Negotiated, Analyzed, Forecasted ([Enhancv](https://enhancv.com/blog/resume-action-verbs/), [Harvard MCS](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/)).
- **Avoid:** "Responsible for" (Harvard's #1 phrase to delete), "Helped/Assisted/Worked on/Participated in/Supported"; buzzword adjectives "team player / detail-oriented / hard worker / results-driven"; personal pronouns; filler ("various," "multiple").

### 5.6 Common mistakes
Typos/grammar (fastest rejection), generic non-tailored resume (#1), clichés/buzzwords, poor formatting, broken contact info.

---

## 6. Implementable Specs

### 6.1 (a) ATS-Compatibility Checker

**Input:** resume file (PDF or DOCX), optional rendered page count.

**Pipeline:**
1. **Detect file type & text layer.** DOCX → parse XML. PDF → extract text layer; if extracted chars / page is near-zero, classify **image/scanned PDF → fail file-type check**, recommend regenerating as text-based.
2. **Plain-text round-trip test.** Extract to plain text; compare logical order. Heuristics for column/table interleaving: detect lines mixing two unrelated content streams (e.g., a date fragment adjacent to an unrelated word), repeated tab/multi-space columns, or table XML in DOCX.
3. **Structure detection.** Flag tables, text boxes, multi-column, header/footer content (esp. email/phone in header), embedded images, skill-bar graphics, icon-encoded contact.
4. **Heading check.** Normalize and match section headings to canonical set: `{work experience, professional experience, employment history, education, skills, certifications, summary, professional summary, projects}`. Report missing/non-standard.
5. **Contact check.** Require email (regex) + phone (≥10 digits) **in body**; detect LinkedIn URL; flag if found only in header/footer.
6. **Font check.** Read embedded font names; compare to safe list `{Calibri, Arial, Helvetica, Georgia, Times New Roman, Garamond, Cambria}`.
7. **Character/bullet check.** Scan for decorative bullets, emoji, smart quotes, em dashes, math symbols; flag char-substitution risk.
8. **Date check.** Extract all date tokens; verify single consistent format; flag mixed/apostrophe/`to`-separator/missing months.
9. **Length check.** Page count + word count vs rubric.

**Output (JSON):**
```json
{
  "compatibilityScore": 0-100,
  "gate": "pass" | "warn" | "fail",
  "checks": [
    {"id":"file_type","status":"pass|warn|fail","weight":12,"message":"...","fix":"..."},
    {"id":"single_column", "...": "..."}
  ],
  "criticalIssues": ["Contact info found only in header — ~25% of ATS will miss it"],
  "extractedFields": { "name":"", "email":"", "phone":"", "sectionsFound":[] }
}
```
Each check returns status + weight + human-readable message + concrete fix. Compatibility gate caps the headline product score.

### 6.2 (b) JD-Match Scorer

**Inputs:** (1) parsed resume text + structured fields; (2) pasted job-description text.

**Pipeline:**
1. **Extract JD keywords.** NER/skill-dictionary tagging → classify each as hard skill / soft skill / tool / cert / title / qualification. Record per-keyword **frequency** and **placement** (in title? in a "requirements/qualifications" block? in "nice-to-have"?).
2. **Weight keywords:** `weight = base(by_type) × freqFactor × placementFactor`. Base: hard 10–15, preferred 5–8, soft 3–5, nice-to-have 1–3. Mark keywords appearing 3+ times or in the title as **required**.
3. **Match against resume.** For each JD keyword, check exact match → stemmed match → known synonym/acronym expansion (`SEO`↔`Search Engine Optimization`). Record found/not-found, count, and **section** found in (summary/skills/bullet).
4. **Compute Score B** per the §4.2 weights. Hard-skill coverage drives ~45%.
5. **Placement quality:** reward top keywords appearing in summary + skills + ≥1 bullet; penalize one-block clustering.
6. **Over-optimization guard:** penalize any keyword appearing >3× unnaturally; run hidden-text/white-font detection; cap effective score.
7. **Gap report:** list missing required keywords first, then preferred, with suggested true placements.

**Output (JSON):**
```json
{
  "matchScore": 0-100,
  "verdict": "needs_work <75 | good 75-80 | strong 80-88 | over_optimized >88",
  "hardSkills": [{"keyword":"Python","jdCount":4,"resumeCount":1,"required":true,"found":true}],
  "softSkills": [...],
  "jobTitleMatch": true,
  "missingRequired": ["Kubernetes","CI/CD"],
  "missingPreferred": ["Terraform"],
  "placement": {"summary":["Python"],"skills":["Python","AWS"],"bullets":["AWS"]},
  "suggestions": [
    {"keyword":"Kubernetes","action":"Add to Skills and one Experience bullet","truthCheck":true}
  ],
  "overOptimizationFlags": []
}
```

**Integration:** Surface both scores separately in UI. Headline = `min(compatibilityGate, weighted(compatibility, jdMatch, contentQuality))`. Always pair a score with the **specific, actionable fix** (missing keyword + where to add it; header contact → move to body; two-column → switch template).

---

## 7. Source-Quality Notes
- **Strongest anchors:** Jobscan (vendor, 2.5M-scan dataset, transparent on its own weighting), Enhancv (the only controlled parse test with hard percentages — but only on Indeed's ATS), the Ladders 2018 eye-tracking study (the canonical "~7s" source), and Sovren/Textkernel/HireAbility (the engines powering many ATS).
- **Directional only:** per-vendor parser specifics (Workday date rules, iCIMS 89%→67%, Taleo strictness) come from SEO-oriented resume-optimization blogs (Resume Optimizer Pro, hireflow). Internally consistent and aligned with known vendor behavior, but not peer-reviewed or official vendor docs. Treat broad mechanisms as solid, precise per-vendor percentages as approximate.
- **Genuine disagreement:** PDF vs DOCX. Reported both positions; product should output clean text-based PDF by default with DOCX as a conservative option, and never image/design-baked PDFs.

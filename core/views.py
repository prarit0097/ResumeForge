from django.shortcuts import render

from apps.templates_engine import registry, samples
from apps.templates_engine.render import _DataShim

LANDING_FEATURES = [
    ("🎯", "Real ATS scoring", "Live 0–100 compatibility score with specific fixes — no vanity numbers."),
    ("🧲", "Tailor to any job", "Paste a job description and we match keywords honestly — never stuffing."),
    ("📥", "PDF · Word · Image", "Download clean, parse-safe files free. No watermarks, no paywall."),
]

# FAQs are reused for the visible accordion AND the FAQPage JSON-LD (rich results).
LANDING_FAQS = [
    ("Is this resume builder really free?",
     "Yes — completely free. You can build or enhance a resume, score it against ATS rules, "
     "tailor it to a job, and download clean PDF, Word or PNG files with no watermark, no "
     "paywall and no account."),
    ("Do I need to sign up or log in?",
     "No. Rezoom needs no login. Your resume lives at a private, unguessable link you "
     "can bookmark and return to from the same device."),
    ("What is an ATS and will it reject my resume?",
     "An Applicant Tracking System (ATS) is a searchable database recruiters use to store and "
     "find applicants — not a robot judge that auto-rejects you. The real risks are layouts that "
     "parse badly (multi-column, tables, images) and missing keywords. Rezoom guarantees a "
     "parse-safe, single-column structure and shows exactly which real keywords to add."),
    ("How does the ATS resume checker score work?",
     "It checks the things that actually matter for parsing and recruiter scanning: contact "
     "details, a strong summary, achievement bullets led by action verbs, quantified results, a "
     "skills section, standard headings and a single-column layout — and gives each a specific, "
     "actionable fix."),
    ("Can it tailor my resume to a specific job?",
     "Yes. Paste the job description and Rezoom shows your match score, the missing skills, "
     "and can rewrite your summary and bullets to fit the role — using your real experience, "
     "never fabricating skills or numbers."),
    ("Are the resume templates ATS-friendly?",
     "Yes. Every template renders the same data and the ATS-safe ones are single-column with "
     "standard headings and selectable text — exactly what parsers read reliably. Creative "
     "two-column templates are clearly labelled with their parse risk."),
    ("What file formats can I download?",
     "Text-selectable PDF (the ATS standard), an ATS-clean Word (DOCX) file, and a PNG image — "
     "all free and watermark-free. There's also a 'what the ATS sees' plain-text preview."),
    ("What's the best file format for an ATS — PDF or Word?",
     "Both work. A text-selectable PDF is the safest, most common choice and keeps your formatting; "
     "some application systems specifically ask for an editable Word (.docx) file. Rezoom exports "
     "both for free, so you can match whatever the application asks for."),
    ("Can I convert my existing resume to an editable Word document?",
     "Yes. Upload your current PDF or Word resume, we parse it into the editor, and you can export a "
     "clean, editable .docx — without retyping it from scratch."),
]


def _sample_template_previews(limit=6):
    """Rendered thumbnails of a few templates for the public templates page."""
    data = samples.sample_resume_data()
    return [{"meta": meta, "obj": _DataShim(data, meta.id)}
            for meta in registry.all_templates()[:limit]]


def landing_view(request):
    """Home page: free AI resume builder + ATS checker."""
    return render(request, "landing.html", {
        "features": LANDING_FEATURES,
        "faqs": LANDING_FAQS,
    })


def ats_checker_view(request):
    """SEO landing for 'ATS resume checker / ATS checker / resume score'."""
    faqs = [
        ("How do I check if my resume is ATS-friendly?",
         "Upload or build your resume in Rezoom and you instantly get a 0–100 ATS "
         "compatibility score with a checklist of specific fixes — contact info, action verbs, "
         "quantified results, a skills section, standard headings and a single-column layout."),
        ("Is the ATS checker free?",
         "Yes, the ATS resume checker is 100% free with no login. You also get an honest "
         "missing-keyword report when you paste a job description."),
        ("What ATS score should I aim for?",
         "Aim for 80+ on compatibility and a 75%+ match to a specific job. Chasing a perfect "
         "100% by keyword-stuffing backfires — recruiters and the interview catch it."),
    ] + LANDING_FAQS[2:4]
    return render(request, "pages/ats_checker.html", {"faqs": faqs})


def resume_templates_view(request):
    """SEO landing for 'ATS resume templates / free resume templates'."""
    faqs = [
        ("Are these resume templates free?",
         "Yes — every template is free to use and download with no watermark and no account."),
        ("Which resume template is best for ATS?",
         "A clean single-column template with standard headings and selectable text parses most "
         "reliably. Rezoom labels every template as ATS-safe or creative so you can choose "
         "with confidence."),
        ("Can I switch templates without losing my content?",
         "Yes. All templates render the same resume data, so you can switch any time and your "
         "content stays intact."),
    ]
    all_t = registry.all_templates()
    return render(request, "pages/resume_templates.html", {
        "previews": _sample_template_previews(),
        "categories": registry.categories(),
        "template_count": len(all_t),
        "ats_safe_count": sum(1 for t in all_t if t.ats_safe),
        "faqs": faqs,
    })

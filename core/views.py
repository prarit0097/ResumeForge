from django.shortcuts import render

LANDING_FEATURES = [
    ("🎯", "Real ATS scoring", "Live 0–100 compatibility score with specific fixes — no vanity numbers."),
    ("🧲", "Tailor to any job", "Paste a job description and we match keywords honestly — never stuffing."),
    ("📥", "PDF · Word · Image", "Download clean, parse-safe files free. No watermarks, no paywall."),
]


def landing_view(request):
    """Home page: two doors — build new or enhance existing."""
    return render(request, "landing.html", {"features": LANDING_FEATURES})

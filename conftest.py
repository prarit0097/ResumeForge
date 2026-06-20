"""Shared pytest fixtures."""
import pytest

from apps.resumes import schema


@pytest.fixture(autouse=True)
def _force_mock_ai(settings):
    """Make the whole suite hermetic: never call the real LLM API (even when a
    key is set in .env). Forces the deterministic offline Mock provider."""
    from apps.ai import provider

    settings.OPENROUTER_API_KEY = ""
    provider.reset_provider_cache()
    yield
    provider.reset_provider_cache()


@pytest.fixture
def strong_resume_data():
    """A complete, quantified, single-column-friendly resume."""
    data = schema.empty_resume()
    data["basics"].update({
        "name": "Jane Doe",
        "label": "Senior Software Engineer",
        "email": "jane@example.com",
        "phone": "+1 555 123 4567",
        "location": "Berlin",
        "summary": "Senior software engineer with eight years building scalable "
                   "platforms and leading teams to ship reliable, measurable products.",
    })
    data["work"] = [{
        "position": "Senior Engineer", "company": "Acme", "location": "Berlin",
        "startDate": "2021-01", "endDate": "", "current": True, "summary": "",
        "highlights": [
            "Led a team of 6 to cut API latency by 40%.",
            "Built a CI pipeline that reduced deploy time by 70%.",
        ],
    }]
    data["education"] = [{
        "studyType": "B.Sc.", "area": "Computer Science", "institution": "TU Berlin",
        "startDate": "2013-09", "endDate": "2017-06", "score": "",
    }]
    data["skills"] = [
        {"name": "Languages", "keywords": ["Python", "JavaScript", "Go", "SQL"]},
        {"name": "Cloud", "keywords": ["AWS", "Docker", "Kubernetes"]},
    ]
    return data

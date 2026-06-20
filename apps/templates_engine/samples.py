"""A representative sample resume used to render template gallery thumbnails so
each template shows its real look even before the user has entered content."""
from __future__ import annotations

from apps.resumes import schema


def sample_resume_data() -> dict:
    d = schema.empty_resume()
    d["basics"].update({
        "name": "Alex Morgan",
        "label": "Senior Product Designer",
        "email": "alex@email.com",
        "phone": "+1 555 0140",
        "location": "San Francisco, CA",
        "url": "linkedin.com/in/alexmorgan",
        "summary": "Product designer with 7+ years crafting intuitive, accessible "
                   "experiences that lifted engagement and revenue across web and mobile.",
    })
    d["work"] = [
        {"position": "Senior Product Designer", "company": "Northwind", "location": "SF",
         "startDate": "2021-03", "endDate": "", "current": True, "summary": "",
         "highlights": [
             "Led the redesign of the onboarding flow, increasing activation by 32%.",
             "Built and maintained a 60-component design system used by 8 teams.",
         ]},
        {"position": "Product Designer", "company": "Brightlabs", "location": "Remote",
         "startDate": "2018-06", "endDate": "2021-02", "current": False, "summary": "",
         "highlights": [
             "Shipped a checkout revamp that cut drop-off by 24%.",
         ]},
    ]
    d["education"] = [
        {"institution": "UC Berkeley", "area": "Human-Computer Interaction",
         "studyType": "B.A.", "startDate": "2014", "endDate": "2018", "score": ""},
    ]
    d["skills"] = [
        {"name": "Design", "keywords": ["Figma", "Prototyping", "Design Systems", "UX Research"]},
        {"name": "Frontend", "keywords": ["HTML", "CSS", "React"]},
    ]
    d["languages"] = [{"language": "English", "fluency": "Native"},
                      {"language": "Spanish", "fluency": "Fluent"}]
    return d

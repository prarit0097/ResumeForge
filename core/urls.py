from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("ats-resume-checker/", views.ats_checker_view, name="ats_checker"),
    path("resume-templates/", views.resume_templates_view, name="resume_templates"),
]

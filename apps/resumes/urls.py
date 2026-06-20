from django.urls import path

from . import views

app_name = "resumes"
urlpatterns = [
    path("r/<uuid:resume_id>/autosave/", views.autosave, name="autosave"),
    path("r/<uuid:resume_id>/set-template/", views.set_template, name="set_template"),
]

from django.urls import path

from . import views

app_name = "ats"
urlpatterns = [
    path("r/<uuid:resume_id>/score/", views.score, name="score"),
    path("r/<uuid:resume_id>/tailor/", views.tailor, name="tailor"),
]

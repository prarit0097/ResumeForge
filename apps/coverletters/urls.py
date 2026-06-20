from django.urls import path

from . import views

app_name = "coverletters"
urlpatterns = [
    path("r/<uuid:resume_id>/cover-letter/", views.cover_letter, name="cover_letter"),
    path("r/<uuid:resume_id>/cover-letter/generate/", views.generate, name="generate"),
    path("r/<uuid:resume_id>/cover-letter/save/", views.save, name="save"),
]

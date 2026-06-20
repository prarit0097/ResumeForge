from django.urls import path

from . import views

app_name = "templates_engine"
urlpatterns = [
    path("r/<uuid:resume_id>/templates/", views.gallery, name="gallery"),
]

from django.urls import path

from . import views

app_name = "ai"
urlpatterns = [
    path("r/<uuid:resume_id>/improve/", views.improve, name="improve"),
    path("r/<uuid:resume_id>/bullets/", views.bullets, name="bullets"),
    path("r/<uuid:resume_id>/polish/", views.polish, name="polish"),
]

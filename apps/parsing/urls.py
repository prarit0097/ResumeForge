from django.urls import path

from . import views

app_name = "parsing"
urlpatterns = [
    path("enhance/", views.upload, name="upload"),
]

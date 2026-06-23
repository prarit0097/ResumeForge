from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("blog/", views.blog_index, name="index"),
    path("blog/<slug:slug>/", views.blog_post, name="post"),
]

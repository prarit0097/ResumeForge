from django.urls import path

from . import views

app_name = "builder"
urlpatterns = [
    path("new/", views.start_new, name="start_new"),
    path("drafts/", views.my_drafts, name="my_drafts"),
    path("r/<uuid:resume_id>/edit/", views.editor, name="editor"),
    path("r/<uuid:resume_id>/wizard/", views.wizard, name="wizard"),
    path("r/<uuid:resume_id>/variant/", views.create_variant, name="create_variant"),
    path("r/<uuid:resume_id>/compare/", views.compare, name="compare"),
    path("r/<uuid:resume_id>/use-original/", views.use_original, name="use_original"),
]

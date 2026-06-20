from django.urls import path

from . import views

app_name = "exporting"
urlpatterns = [
    path("r/<uuid:resume_id>/download/", views.download_menu, name="download_menu"),
    path("r/<uuid:resume_id>/download/pdf/", views.download_pdf, name="download_pdf"),
    path("r/<uuid:resume_id>/download/png/", views.download_png, name="download_png"),
    path("r/<uuid:resume_id>/download/docx/", views.download_docx, name="download_docx"),
    path("r/<uuid:resume_id>/download/txt/", views.download_txt, name="download_txt"),
]

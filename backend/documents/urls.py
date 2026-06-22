# backend/documents/urls.py

from django.urls import path

from .views import (
    DocumentUploadView,
    DocumentListView,
    DocumentStatusView,
    DocumentChunksView,
)

urlpatterns = [
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),

    path(
        "project/<int:project_id>/",
        DocumentListView.as_view(),
        name="document-list",
    ),

    path(
        "<int:document_id>/status/",
        DocumentStatusView.as_view(),
        name="document-status",
    ),

    path(
        "<int:document_id>/chunks/",
        DocumentChunksView.as_view(),
        name="document-chunks",
    ),
]
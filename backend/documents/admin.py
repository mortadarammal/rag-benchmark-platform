# backend/documents/admin.py

from django.contrib import admin
from .models import UploadedDocument, DocumentChunk


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "original_name",
        "project",
        "status",
        "created_at",
        "processed_at",
    ]

    list_filter = ["status", "created_at"]
    search_fields = ["original_name"]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "document",
        "chunk_index",
        "created_at",
    ]

    search_fields = ["text", "document__original_name"]
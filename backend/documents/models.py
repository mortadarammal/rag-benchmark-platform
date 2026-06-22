
# backend/documents/models.py

from django.db import models
from projects.models import Project


class UploadedDocument(models.Model):
    STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("processing", "Processing"),
        ("chunked", "Chunked"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    file = models.FileField(upload_to="documents/")
    original_name = models.CharField(max_length=255)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="uploaded",
    )

    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.original_name


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        UploadedDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    chunk_index = models.IntegerField()
    text = models.TextField()

    # Empty in Phase 1.
    # Later, in Phase 2, this will store the Qdrant vector ID.
    vector_id = models.CharField(max_length=255, blank=True)

    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.original_name} - chunk {self.chunk_index}"
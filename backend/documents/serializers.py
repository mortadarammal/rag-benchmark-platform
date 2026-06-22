# backend/documents/serializers.py

from rest_framework import serializers
from .models import UploadedDocument, DocumentChunk


class UploadedDocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.SerializerMethodField()

    class Meta:
        model = UploadedDocument
        fields = [
            "id",
            "project",
            "file",
            "original_name",
            "status",
            "error_message",
            "chunks_count",
            "created_at",
            "processed_at",
        ]

        read_only_fields = [
            "original_name",
            "status",
            "error_message",
            "chunks_count",
            "created_at",
            "processed_at",
        ]

    def get_chunks_count(self, obj):
        return obj.chunks.count()


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "document",
            "chunk_index",
            "text",
            "metadata",
            "created_at",
        ]
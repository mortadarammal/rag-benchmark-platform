# backend/projects/serializers.py

from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    documents_count = serializers.SerializerMethodField()
    questions_count = serializers.SerializerMethodField()
    runs_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "documents_count",
            "questions_count",
            "runs_count",
            "created_at",
        ]

    def get_documents_count(self, obj):
        return obj.documents.count()

    def get_questions_count(self, obj):
        return obj.generated_questions.count()

    def get_runs_count(self, obj):
        return obj.benchmark_runs.count()
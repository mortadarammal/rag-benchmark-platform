# backend/benchmarks/admin.py

from django.contrib import admin
from .models import GeneratedQuestion, BenchmarkRun, ModelAnswer, EvaluationResult


@admin.register(GeneratedQuestion)
class GeneratedQuestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "project",
        "selected",
        "status",
        "created_at",
    ]

    list_filter = ["selected", "status", "created_at"]
    search_fields = ["question", "project__name"]


@admin.register(BenchmarkRun)
class BenchmarkRunAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "project",
        "question",
        "status",
        "created_at",
        "completed_at",
    ]

    list_filter = ["status", "created_at"]
    search_fields = ["question__question", "project__name"]


@admin.register(ModelAnswer)
class ModelAnswerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "benchmark_run",
        "model_key",
        "status",
        "latency_ms",
        "created_at",
    ]

    list_filter = ["model_key", "status", "created_at"]
    search_fields = ["model_key", "model_name", "question", "answer"]



@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "answer",
        "judge_model",
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        #"context_recall",
        "context_sufficiency",
        "final_score",
        "created_at",
    ]

    list_filter = ["judge_model", "created_at"]
    search_fields = ["answer__model_key", "answer__model_name"]
# backend/benchmarks/serializers.py

from rest_framework import serializers
from .models import (
    GeneratedQuestion,
    BenchmarkRun,
    ModelAnswer,
    EvaluationResult,
)


class GeneratedQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedQuestion
        fields = [
            "id",
            "project",
            "question",
            "source_chunk_ids",
            "source_document_ids",
            "status",
            "selected",
            "created_at",
        ]


class EvaluationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationResult
        fields = [
            "id",
            "judge_model",
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            #"context_recall",
            "context_sufficiency",
            "final_score",
            "faithfulness_reasoning",
            "answer_relevancy_reasoning",
            "context_precision_reasoning",
            #"context_recall_reasoning",
            "context_sufficiency_reasoning",
            "raw_judge_output",
            "created_at",
        ]


class ModelAnswerSerializer(serializers.ModelSerializer):
    evaluation = EvaluationResultSerializer(read_only=True)

    class Meta:
        model = ModelAnswer
        fields = [
            "id",
            "benchmark_run",
            "model_key",
            "model_name",
            "question",
            "answer",
            "retrieved_contexts",
            "full_context",
            "latency_ms",
            "status",
            "error_message",
            "evaluation",
            "created_at",
            "completed_at",
        ]


class BenchmarkRunSerializer(serializers.ModelSerializer):
    answers = ModelAnswerSerializer(many=True, read_only=True)
    question_text = serializers.CharField(
        source="question.question",
        read_only=True,
    )

    class Meta:
        model = BenchmarkRun
        fields = [
            "id",
            "project",
            "question",
            "question_text",
            "status",
            "error_message",
            "answers",
            "created_at",
            "completed_at",
        ]


class RankingRowSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    model_key = serializers.CharField()
    model_name = serializers.CharField()
    answer_id = serializers.IntegerField()
    final_score = serializers.FloatField()
    faithfulness = serializers.FloatField()
    answer_relevancy = serializers.FloatField()
    context_precision = serializers.FloatField()
    #context_recall = serializers.FloatField()
    context_sufficiency = serializers.FloatField()
    latency_ms = serializers.IntegerField(allow_null=True)
    answer = serializers.CharField()
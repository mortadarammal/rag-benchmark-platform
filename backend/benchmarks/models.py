from django.db import models
from projects.models import Project


class GeneratedQuestion(models.Model):
    STATUS_CHOICES = [
        ("generated", "Generated"),
        ("selected", "Selected"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="generated_questions",
    )

    question = models.TextField()

    # Optional but useful for traceability
    source_chunk_ids = models.JSONField(default=list)
    source_document_ids = models.JSONField(default=list)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="generated",
    )

    selected = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question[:100]

class BenchmarkRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="benchmark_runs",
    )

    question = models.ForeignKey(
        GeneratedQuestion,
        on_delete=models.CASCADE,
        related_name="benchmark_runs",
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pending",
    )

    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Run {self.id} - {self.question.question[:60]}"
    

class ModelAnswer(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    benchmark_run = models.ForeignKey(
        BenchmarkRun,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    model_key = models.CharField(max_length=100, default="unknown_model")
    model_name = models.CharField(max_length=255, default="unknown_model")

    question = models.TextField(default="")
    answer = models.TextField(blank=True)

    retrieved_contexts = models.JSONField(default=list)
    full_context = models.TextField(blank=True)

    latency_ms = models.IntegerField(blank=True, null=True)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pending",
    )

    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.model_key} - run {self.benchmark_run_id}"
    
class EvaluationResult(models.Model):
    answer = models.OneToOneField(
        ModelAnswer,
        on_delete=models.CASCADE,
        related_name="evaluation",
    )

    #judge_model = models.CharField(max_length=255,default="mistralai/mistral-large-3-675b-instruct-2512",)
    judge_model = models.CharField(max_length=255,default="openai/gpt-oss-120b",)
    #judge_model = models.CharField(max_length=255,default="qwen/qwen3.5-397b-a17b",)


    faithfulness = models.FloatField(default=0.0)
    answer_relevancy = models.FloatField(default=0.0)
    context_precision = models.FloatField(default=0.0)
    #context_recall = models.FloatField(default=0.0)
    context_sufficiency = models.FloatField(default=0.0)

    final_score = models.FloatField(default=0.0)


    faithfulness_reasoning = models.TextField(blank=True, default="")
    answer_relevancy_reasoning = models.TextField(blank=True, default="")
    context_precision_reasoning = models.TextField(blank=True, default="")
    #context_recall_reasoning = models.TextField(blank=True, default="")
    context_sufficiency_reasoning = models.TextField(blank=True, default="")

    raw_judge_output = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.answer.model_key} score={self.final_score:.3f}"


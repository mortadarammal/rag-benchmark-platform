# backend/benchmarks/views.py
import json
from django.http import HttpResponse
from benchmarks.exports import build_ranking_data, build_ranking_csv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status

from rag.config import RAG_CONFIG

from .models import GeneratedQuestion, BenchmarkRun, ModelAnswer
from .serializers import (
    GeneratedQuestionSerializer,
    BenchmarkRunSerializer,
)
from .tasks import (
    generate_questions_task,
    generate_answers_for_selected_question_task,
    evaluate_benchmark_run_task,
)


class GenerateQuestionsView(APIView):
    """
    Phase 3.
    Start question generation for a project.
    """

    def post(self, request):
        project_id = request.data.get("project_id")
        number_of_questions = request.data.get("number_of_questions", 10)

        if not project_id:
            return Response(
                {"error": "project_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            number_of_questions = int(number_of_questions)
        except ValueError:
            return Response(
                {"error": "number_of_questions must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = generate_questions_task.delay(
            project_id=int(project_id),
            number_of_questions=number_of_questions,
        )

        return Response(
            {
                "message": "Question generation started.",
                "task_id": task.id,
                "project_id": int(project_id),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ProjectQuestionsView(generics.ListAPIView):
    serializer_class = GeneratedQuestionSerializer

    def get_queryset(self):
        project_id = self.kwargs["project_id"]

        return GeneratedQuestion.objects.filter(
            project_id=project_id,
        ).order_by("-created_at")


class SelectQuestionView(APIView):
    """
    Select one generated question for the next benchmark phase.
    """

    def post(self, request, question_id):
        try:
            question = GeneratedQuestion.objects.get(id=question_id)
        except GeneratedQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        GeneratedQuestion.objects.filter(
            project=question.project,
            selected=True,
        ).update(
            selected=False,
            status="generated",
        )

        question.selected = True
        question.status = "selected"
        question.save(update_fields=["selected", "status"])

        return Response(
            {
                "message": "Question selected.",
                "question": GeneratedQuestionSerializer(question).data,
            }
        )


class AvailableGeneratorModelsView(APIView):
    """
    Returns the available answer-generation models.
    """

    def get(self, request):
        models = [
            {
                "model_key": key,
                "model_name": value,
            }
            for key, value in RAG_CONFIG["generator_models"].items()
        ]

        return Response({"models": models})


class GenerateAnswersView(APIView):
    """
    Phase 4.
    Generate answers from multiple LLMs for the selected question.

    Body:
    {
        "question_id": 1,
        "selected_model_keys": ["llama_3b", "llama_8b"]
    }

    If selected_model_keys is not provided, all models run.
    """

    def post(self, request):
        question_id = request.data.get("question_id")
        selected_model_keys = request.data.get("selected_model_keys")

        if not question_id:
            return Response(
                {"error": "question_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            question = GeneratedQuestion.objects.get(id=question_id)
        except GeneratedQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not question.selected:
            return Response(
                {
                    "error": (
                        "This question is not selected. "
                        "Select it first before generating answers."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = generate_answers_for_selected_question_task.delay(
            question_id=int(question_id),
            selected_model_keys=selected_model_keys,
        )

        return Response(
            {
                "message": "Answer generation started.",
                "task_id": task.id,
                "question_id": int(question_id),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ProjectBenchmarkRunsView(generics.ListAPIView):
    serializer_class = BenchmarkRunSerializer

    def get_queryset(self):
        project_id = self.kwargs["project_id"]

        return BenchmarkRun.objects.filter(
            project_id=project_id,
        ).order_by("-created_at")


class BenchmarkRunDetailView(generics.RetrieveAPIView):
    serializer_class = BenchmarkRunSerializer
    queryset = BenchmarkRun.objects.all()


class EvaluateBenchmarkRunView(APIView):
    """
    
    Starts judge evaluation for all answers in a benchmark run.
    """

    def post(self, request, run_id):
        try:
            benchmark_run = BenchmarkRun.objects.get(id=run_id)
        except BenchmarkRun.DoesNotExist:
            return Response(
                {"error": "Benchmark run not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        completed_answers = benchmark_run.answers.filter(status="completed")

        if not completed_answers.exists():
            return Response(
                {"error": "No completed model answers found for this run."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = evaluate_benchmark_run_task.delay(benchmark_run_id=benchmark_run.id)

        return Response(
            {
                "message": "Judge evaluation started.",
                "task_id": task.id,
                "benchmark_run_id": benchmark_run.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class BenchmarkRunRankingView(APIView):
    """
    Returns ranking from best model to worst for one benchmark run.
    """

    def get(self, request, run_id):
        try:
            benchmark_run = BenchmarkRun.objects.get(id=run_id)
        except BenchmarkRun.DoesNotExist:
            return Response(
                {"error": "Benchmark run not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        answers = (
            ModelAnswer.objects
            .filter(
                benchmark_run=benchmark_run,
                evaluation__isnull=False,
            )
            .select_related("evaluation")
            .order_by("-evaluation__final_score")
        )

        ranking = []

        for index, answer in enumerate(answers, start=1):
            ev = answer.evaluation

            ranking.append(
                {
                    "rank": index,
                    "model_key": answer.model_key,
                    "model_name": answer.model_name,
                    "answer_id": answer.id,
                    "final_score": ev.final_score,
                    "faithfulness": ev.faithfulness,
                    "answer_relevancy": ev.answer_relevancy,
                    "context_precision": ev.context_precision,
                    #"context_recall": ev.context_recall,
                    "context_sufficiency": ev.context_sufficiency,
                    "latency_ms": answer.latency_ms,
                    "answer": answer.answer,
                }
            )

        return Response(
            {
                "benchmark_run_id": benchmark_run.id,
                "question": benchmark_run.question.question,
                "ranking": ranking,
            }
        )
    

class ExportBenchmarkRunJsonView(APIView):
    def get(self, request, run_id):
        try:
            data = build_ranking_data(run_id)
        except BenchmarkRun.DoesNotExist:
            return Response(
                {"error": "Benchmark run not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        response = HttpResponse(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type="application/json",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="benchmark_run_{run_id}.json"'
        )

        return response


class ExportBenchmarkRunCsvView(APIView):
    def get(self, request, run_id):
        try:
            csv_content = build_ranking_csv(run_id)
        except BenchmarkRun.DoesNotExist:
            return Response(
                {"error": "Benchmark run not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        response = HttpResponse(
            csv_content,
            content_type="text/csv",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="benchmark_run_{run_id}.csv"'
        )

        return response
# backend/benchmarks/urls.py

from django.urls import path

from .views import (
    GenerateQuestionsView,
    ProjectQuestionsView,
    SelectQuestionView,
    AvailableGeneratorModelsView,
    GenerateAnswersView,
    ProjectBenchmarkRunsView,
    BenchmarkRunDetailView,
    EvaluateBenchmarkRunView,
    BenchmarkRunRankingView,
    ExportBenchmarkRunJsonView,
    ExportBenchmarkRunCsvView,
)

urlpatterns = [
    # Phase 3
    path(
        "questions/generate/",
        GenerateQuestionsView.as_view(),
        name="generate-questions",
    ),

    path(
        "projects/<int:project_id>/questions/",
        ProjectQuestionsView.as_view(),
        name="project-questions",
    ),

    path(
        "questions/<int:question_id>/select/",
        SelectQuestionView.as_view(),
        name="select-question",
    ),

    # Phase 4
    path(
        "generator-models/",
        AvailableGeneratorModelsView.as_view(),
        name="available-generator-models",
    ),

    path(
        "answers/generate/",
        GenerateAnswersView.as_view(),
        name="generate-answers",
    ),

    path(
        "projects/<int:project_id>/runs/",
        ProjectBenchmarkRunsView.as_view(),
        name="project-benchmark-runs",
    ),

    path(
        "runs/<int:pk>/",
        BenchmarkRunDetailView.as_view(),
        name="benchmark-run-detail",
    ),

    path(
        "runs/<int:run_id>/evaluate/",
        EvaluateBenchmarkRunView.as_view(),
        name="evaluate-benchmark-run",
    ),

    path(
        "runs/<int:run_id>/ranking/",
        BenchmarkRunRankingView.as_view(),
        name="benchmark-run-ranking",
    ),

    path(
    "runs/<int:run_id>/export/json/",
    ExportBenchmarkRunJsonView.as_view(),
    name="export-benchmark-json",
    ),

    path(
    "runs/<int:run_id>/export/csv/",
    ExportBenchmarkRunCsvView.as_view(),
    name="export-benchmark-csv",
    ),
]
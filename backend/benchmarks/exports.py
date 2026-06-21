# backend/benchmarks/exports.py

import csv
import io

from .models import BenchmarkRun, ModelAnswer


def build_ranking_data(run_id: int) -> dict:
    benchmark_run = BenchmarkRun.objects.get(id=run_id)

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
                "final_score": ev.final_score,
                "faithfulness": ev.faithfulness,
                "answer_relevancy": ev.answer_relevancy,
                "context_precision": ev.context_precision,
                #"context_recall": ev.context_recall,
                "context_sufficiency": ev.context_sufficiency,
                "latency_ms": answer.latency_ms,
                "answer": answer.answer,
                "faithfulness_reasoning": ev.faithfulness_reasoning,
                "answer_relevancy_reasoning": ev.answer_relevancy_reasoning,
                "context_precision_reasoning": ev.context_precision_reasoning,
                #"context_recall_reasoning": ev.context_recall_reasoning,
                "context_sufficiency_reasoning": ev.context_sufficiency_reasoning,
            }
        )

    return {
        "benchmark_run_id": benchmark_run.id,
        "project_id": benchmark_run.project_id,
        "project_name": benchmark_run.project.name,
        "question": benchmark_run.question.question,
        "status": benchmark_run.status,
        "created_at": benchmark_run.created_at.isoformat(),
        "completed_at": (
            benchmark_run.completed_at.isoformat()
            if benchmark_run.completed_at
            else None
        ),
        "ranking": ranking,
    }


def build_ranking_csv(run_id: int) -> str:
    data = build_ranking_data(run_id)

    output = io.StringIO()

    fieldnames = [
        "rank",
        "model_key",
        "model_name",
        "final_score",
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        # "context_recall",
        "context_sufficiency",
        "latency_ms",
        "answer",
        "faithfulness_reasoning",
        "answer_relevancy_reasoning",
        "context_precision_reasoning",
        # "context_recall_reasoning",
        "context_sufficiency",
        "context_sufficiency_reasoning",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in data["ranking"]:
        writer.writerow(row)

    return output.getvalue()
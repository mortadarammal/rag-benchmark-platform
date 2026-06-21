\
# backend/benchmarks/ragas_custom/runner.py

from typing import Any

from ragas import EvaluationDataset, evaluate
from ragas.run_config import RunConfig

from .clients import (
    get_embedding_model_name,
    get_judge_embeddings_wrapped,
    get_judge_llm_raw,
    get_judge_model_name,
)
from .formatting import build_single_turn_sample
from .metrics import build_custom_metrics


SCORE_COLUMNS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_sufficiency",
]


def compute_final_score(
    faithfulness: float,
    answer_relevancy: float,
    context_precision: float,
    context_sufficiency: float,
) -> float:
    """
    Same principle as the notebook:
    final score = mean of the 4 custom metric scores.
    """
    scores = [
        float(faithfulness),
        float(answer_relevancy),
        float(context_precision),
        float(context_sufficiency),
    ]

    return sum(scores) / len(scores)


def build_run_config() -> RunConfig:
    """
    Notebook equivalent:
    RunConfig(timeout=600, max_workers=1, max_retries=3)

    max_workers=1 is important because each metric object stores `last_output`
    for the explanation that is later saved in EvaluationResult.
    """
    return RunConfig(
        timeout=600,
        max_workers=1,
        max_retries=3,
    )


def _score_from_result_row(row: Any, metric_name: str, fallback: float) -> float:
    try:
        value = row[metric_name]
        if value is None:
            return float(fallback)
        return float(value)
    except Exception:
        return float(fallback)


def evaluate_answer_with_custom_ragas(
    question: str,
    answer: str,
    retrieved_contexts: list[dict] | list[str] | None,
    max_chunks: int = 5,
    max_chars_per_chunk: int = 1500,
    max_answer_chars: int = 3000,
) -> dict:
    """
    Main fullstack RAGAS evaluator.

    This is the project version of notebook Phase 3:
    - creates SingleTurnSample
    - creates EvaluationDataset
    - creates custom SingleTurnMetric objects
    - calls ragas.evaluate(...)
    - returns the dict expected by benchmarks.tasks.evaluate_benchmark_run_task
    """

    sample = build_single_turn_sample(
        question=question,
        answer=answer,
        retrieved_contexts=retrieved_contexts,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
        max_answer_chars=max_answer_chars,
    )

    dataset = EvaluationDataset(samples=[sample])

    judge_llm = get_judge_llm_raw()

    # This mirrors the notebook embedding setup.
    # The custom metrics do not currently use embeddings, but keeping this
    # initialized makes the integration faithful to the notebook and ready if
    # you later re-enable default RAGAS AnswerRelevancy/ContextPrecision.
    judge_embeddings = get_judge_embeddings_wrapped()

    metrics = build_custom_metrics(
        judge_llm=judge_llm,
        retries=3,
        wait_seconds=30,
    )

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        run_config=build_run_config(),
    )

    result_df = result.to_pandas()
    row = result_df.iloc[0] if len(result_df) else {}

    details = {metric.name: metric.last_output for metric in metrics}

    faithfulness = _score_from_result_row(
        row,
        "faithfulness",
        details["faithfulness"].score,
    )
    answer_relevancy = _score_from_result_row(
        row,
        "answer_relevancy",
        details["answer_relevancy"].score,
    )
    context_precision = _score_from_result_row(
        row,
        "context_precision",
        details["context_precision"].score,
    )
    context_sufficiency = _score_from_result_row(
        row,
        "context_sufficiency",
        details["context_sufficiency"].score,
    )

    final_score = compute_final_score(
        faithfulness=faithfulness,
        answer_relevancy=answer_relevancy,
        context_precision=context_precision,
        context_sufficiency=context_sufficiency,
    )

    return {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_precision": context_precision,
        "context_sufficiency": context_sufficiency,
        "final_score": final_score,

        "faithfulness_reasoning": details["faithfulness"].explanation,
        "answer_relevancy_reasoning": details["answer_relevancy"].explanation,
        "context_precision_reasoning": details["context_precision"].explanation,
        "context_sufficiency_reasoning": details["context_sufficiency"].explanation,

        "raw_judge_output": {
            "ragas_used": True,
            "ragas_metric_type": "custom SingleTurnMetric",
            "uses_ragas_default_metrics": False,
            "judge_model": get_judge_model_name(),
            "embedding_model_initialized": get_embedding_model_name(),
            "embedding_note": (
                "Initialized like the notebook. The 4 custom metrics are direct "
                "LLM-scored SingleTurnMetric metrics, so embeddings are not used "
                "unless default RAGAS metrics are enabled later."
            ),
            "faithfulness": details["faithfulness"].raw,
            "answer_relevancy": details["answer_relevancy"].raw,
            "context_precision": details["context_precision"].raw,
            "context_precision_verdicts": details["context_precision"].verdicts,
            "context_sufficiency": details["context_sufficiency"].raw,
            "ragas_result_row": (
                result_df.to_dict(orient="records")[0]
                if len(result_df)
                else {}
            ),
        },
    }

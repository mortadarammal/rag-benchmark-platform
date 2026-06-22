
import json
import re
import time
from typing import Any

from llms.nvidia_client import get_nvidia_judge_model

from benchmarks.ragas_custom.runner import evaluate_answer_with_custom_ragas


def evaluate_answer_with_judge(
    question: str,
    answer: str,
    retrieved_contexts: list[dict],
) -> dict:
    
    """
    Evaluate one model answer using custom RAGAS SingleTurnMetric classes.

    This DOES use RAGAS:
    - SingleTurnSample
    - EvaluationDataset
    - custom SingleTurnMetric subclasses
    - ragas.evaluate(...)

    This does NOT use RAGAS default metrics:
    - no default AnswerRelevancy
    - no default ContextPrecision
    - no default ContextRecall

    The metric logic is the custom prompt-based logic from notebook Phase 3.
    """
    return evaluate_answer_with_custom_ragas(
        question=question,
        answer=answer,
        retrieved_contexts=retrieved_contexts,
    )
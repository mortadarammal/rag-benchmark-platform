\
# backend/benchmarks/ragas_custom/metrics.py

import asyncio
from dataclasses import dataclass, field
from typing import Any

from ragas.dataset_schema import SingleTurnSample
from ragas.metrics.base import MetricType, SingleTurnMetric

from .formatting import contexts_for_prompt
from .llm_calls import invoke_llm_with_retry
from .parsing import MetricOutput, parse_metric_output
from .prompts import (
    JUDGE_PROMPT_ANSWER_RELEVANCY,
    JUDGE_PROMPT_CONTEXT_PRECISION,
    JUDGE_PROMPT_CONTEXT_SUFFICIENCY,
    JUDGE_PROMPT_FAITHFULNESS,
)


@dataclass
class _BaseCustomJudgeMetric(SingleTurnMetric):
    """
    class for custom RAGAS metrics.

    RAGAS requires the metric to return a float, but your Django model also
    needs explanation/verdict details. Each metric therefore stores its latest
    parsed output in `last_output`.

    """

    llm: Any = None
    retries: int = 3
    wait_seconds: int = 30
    last_output: MetricOutput = field(default_factory=MetricOutput, init=False)

    def init(self, run_config=None):
        pass

    def _score_prompt(self, prompt: str) -> float:
        raw = invoke_llm_with_retry(
            llm=self.llm,
            prompt=prompt,
            retries=self.retries,
            wait_seconds=self.wait_seconds,
        )
        self.last_output = parse_metric_output(raw)
        return self.last_output.score

    def _single_turn_score(
        self,
        sample: SingleTurnSample,
        callbacks=None,
    ) -> float:
        return asyncio.get_event_loop().run_until_complete(
            self._single_turn_ascore(sample, callbacks)
        )


@dataclass
class CustomFaithfulness(_BaseCustomJudgeMetric):
    """
    Faithfulness + correctness from retrieved context.

    Notebook equivalent: CustomFaithfulness(SingleTurnMetric).
    """

    name: str = "faithfulness"
    _required_columns: dict = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {
                "user_input",
                "response",
                "retrieved_contexts",
            }
        }
    )

    async def _single_turn_ascore(
        self,
        sample: SingleTurnSample,
        callbacks=None,
    ) -> float:
        prompt = JUDGE_PROMPT_FAITHFULNESS.format(
            question=sample.user_input,
            contexts=contexts_for_prompt(sample.retrieved_contexts or []),
            answer=sample.response,
        )
        return self._score_prompt(prompt)


@dataclass
class CustomAnswerRelevancy(_BaseCustomJudgeMetric):
    """
    Direct custom answer relevancy.

    """

    name: str = "answer_relevancy"
    _required_columns: dict = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {
                "user_input",
                "response",
            }
        }
    )

    async def _single_turn_ascore(
        self,
        sample: SingleTurnSample,
        callbacks=None,
    ) -> float:
        prompt = JUDGE_PROMPT_ANSWER_RELEVANCY.format(
            question=sample.user_input,
            answer=sample.response,
        )
        return self._score_prompt(prompt)


@dataclass
class CustomContextPrecision(_BaseCustomJudgeMetric):
    """
    Custom context precision.

    """

    name: str = "context_precision"
    _required_columns: dict = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {
                "user_input",
                "retrieved_contexts",
            }
        }
    )

    async def _single_turn_ascore(
        self,
        sample: SingleTurnSample,
        callbacks=None,
    ) -> float:
        prompt = JUDGE_PROMPT_CONTEXT_PRECISION.format(
            question=sample.user_input,
            contexts=contexts_for_prompt(sample.retrieved_contexts or []),
        )
        return self._score_prompt(prompt)


@dataclass
class CustomContextSufficiency(_BaseCustomJudgeMetric):
    """
    Custom context sufficiency.

    """

    name: str = "context_sufficiency"
    _required_columns: dict = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {
                "user_input",
                "retrieved_contexts",
            }
        }
    )

    async def _single_turn_ascore(
        self,
        sample: SingleTurnSample,
        callbacks=None,
    ) -> float:
        prompt = JUDGE_PROMPT_CONTEXT_SUFFICIENCY.format(
            question=sample.user_input,
            contexts=contexts_for_prompt(sample.retrieved_contexts or []),
        )
        return self._score_prompt(prompt)


def build_custom_metrics(
    judge_llm: Any,
    retries: int = 3,
    wait_seconds: int = 30,
) -> list[_BaseCustomJudgeMetric]:
    return [
        CustomFaithfulness(
            llm=judge_llm,
            retries=retries,
            wait_seconds=wait_seconds,
        ),
        CustomAnswerRelevancy(
            llm=judge_llm,
            retries=retries,
            wait_seconds=wait_seconds,
        ),
        CustomContextPrecision(
            llm=judge_llm,
            retries=retries,
            wait_seconds=wait_seconds,
        ),
        CustomContextSufficiency(
            llm=judge_llm,
            retries=retries,
            wait_seconds=wait_seconds,
        ),
    ]

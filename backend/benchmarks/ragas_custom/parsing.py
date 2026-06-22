\
# backend/benchmarks/ragas_custom/parsing.py

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricOutput:
    score: float = 0.0
    explanation: str = ""
    verdicts: list[int] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""


def clamp_score(value: Any) -> float:
    try:
        score = float(value)
    except Exception:
        return 0.0

    return max(0.0, min(1.0, score))


def clean_json_from_llm(text: Any) -> str:
    """
    cleaner copied from the notebook.

    It accepts:
    - fenced JSON
    - text before/after JSON
    - compact JSON
    """
    text = str(text or "").strip()

    text = re.sub(r"```json", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()

    return text


def safe_json_loads(text: Any) -> dict[str, Any]:
    cleaned = clean_json_from_llm(text)
    return json.loads(cleaned)


def _extract_score_with_regex(text: str) -> float | None:
    score_match = re.search(r'"score"\s*:\s*([0-9]*\.?[0-9]+)', text)
    if score_match:
        return clamp_score(score_match.group(1))

    score_match = re.search(r"\bscore\s*[:=]\s*([0-9]*\.?[0-9]+)", text, re.IGNORECASE)
    if score_match:
        return clamp_score(score_match.group(1))

    return None


def parse_metric_output(raw: Any) -> MetricOutput:
    """
    Expected LLM output:
    {
      "score": 0.0,
      "explanation": ""
    }

    Context precision can also return:
    {
      "score": 0.0,
      "verdicts": [1, 0, 1],
      "explanation": ""
    }

    This returns both the numeric score required by RAGAS and the explanation
    needed by your Django EvaluationResult model.
    """
    raw_text = str(raw or "").strip()

    if not raw_text:
        return MetricOutput(
            score=0.0,
            explanation="Judge returned an empty response.",
            raw={"raw": ""},
            raw_text="",
        )

    try:
        data = safe_json_loads(raw_text)

        verdicts = data.get("verdicts", [])
        if not isinstance(verdicts, list):
            verdicts = []

        verdicts = [
            int(v)
            for v in verdicts
            if str(v).strip() in {"0", "1"}
        ]

        return MetricOutput(
            score=clamp_score(data.get("score", 0.0)),
            explanation=str(data.get("explanation", "")),
            verdicts=verdicts,
            raw=data,
            raw_text=raw_text,
        )

    except Exception:
        score = _extract_score_with_regex(raw_text)

        if score is not None:
            return MetricOutput(
                score=score,
                explanation="Score extracted from judge output because JSON parsing failed.",
                verdicts=[],
                raw={"raw": raw_text[:2000]},
                raw_text=raw_text,
            )

        return MetricOutput(
            score=0.0,
            explanation=f"Judge output could not be parsed: {raw_text[:300]}",
            verdicts=[],
            raw={"raw": raw_text[:2000]},
            raw_text=raw_text,
        )

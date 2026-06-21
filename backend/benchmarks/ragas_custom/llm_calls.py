\
# backend/benchmarks/ragas_custom/llm_calls.py

import json
import time
from typing import Any


def invoke_llm_with_retry(
    llm: Any,
    prompt: str,
    retries: int = 3,
    wait_seconds: int = 30,
    backoff_multiplier: float = 2.0,
) -> str:
    """
    Protects the evaluation phase from temporary NVIDIA errors such as:
    - 429 Too Many Requests
    - 504 Gateway Timeout

    The notebook used batch size + sleep. In Django/Celery, every answer is
    evaluated independently, so retry/backoff here is the safest equivalent.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)

        except Exception as exc:
            last_error = str(exc)

            if attempt < retries:
                sleep_for = wait_seconds * (backoff_multiplier ** (attempt - 1))
                time.sleep(sleep_for)

    return json.dumps(
        {
            "score": 0.0,
            "explanation": f"Judge call failed after {retries} attempts: {last_error}",
        }
    )

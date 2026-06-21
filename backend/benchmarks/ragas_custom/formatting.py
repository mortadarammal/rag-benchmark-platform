\
# backend/benchmarks/ragas_custom/formatting.py

from typing import Any

from ragas.dataset_schema import SingleTurnSample


def _context_text(chunk: Any) -> str:
    if isinstance(chunk, str):
        return chunk.strip()

    if isinstance(chunk, dict):
        # Your retrieval code stores dicts with at least "text".
        text = str(chunk.get("text", "")).strip()
        source = chunk.get("source", "unknown")
        score = chunk.get("score", None)

        # Keep metadata because context_precision depends on ranking order,
        # and source/score are useful for debugging the judge result.
        return (
            f"Source: {source}\n"
            f"Retrieval score: {score}\n"
            f"Text:\n{text}"
        ).strip()

    return str(chunk).strip()


def normalize_retrieved_contexts(
    retrieved_contexts: list[Any] | None,
    max_chunks: int = 5,
    max_chars_per_chunk: int = 1500,
) -> list[str]:
    """
    Converts Django's JSON retrieved_contexts into the list[str] expected by
    RAGAS SingleTurnSample.

    The order is preserved because context_precision evaluates ranking.
    """
    contexts: list[str] = []

    for chunk in (retrieved_contexts or [])[:max_chunks]:
        text = _context_text(chunk)

        if len(text) > max_chars_per_chunk:
            text = text[:max_chars_per_chunk] + "..."

        if text:
            contexts.append(text)

    return contexts


def contexts_for_prompt(contexts: list[str]) -> str:
    return "\n\n".join(
        f"Chunk {index + 1}:\n{context}"
        for index, context in enumerate(contexts)
    )


def build_single_turn_sample(
    question: str,
    answer: str,
    retrieved_contexts: list[Any] | None,
    max_chunks: int = 5,
    max_chars_per_chunk: int = 1500,
    max_answer_chars: int = 3000,
) -> SingleTurnSample:
    answer = str(answer or "")

    if len(answer) > max_answer_chars:
        answer = answer[:max_answer_chars] + "..."

    contexts = normalize_retrieved_contexts(
        retrieved_contexts=retrieved_contexts,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )

    return SingleTurnSample(
        user_input=str(question or ""),
        response=answer,
        retrieved_contexts=contexts,
    )

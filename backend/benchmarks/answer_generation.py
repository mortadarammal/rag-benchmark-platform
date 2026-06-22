# backend/benchmarks/answer_generation.py

import time

from langchain_core.prompts import PromptTemplate

from llms.nvidia_client import get_nvidia_chat_model
from rag.config import RAG_CONFIG
from rag.retrieval import (
    retrieve_relevant_chunks,
    build_context_from_retrieved_chunks,
)


RAG_ANSWER_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are an expert assistant answering questions using retrieved document context.

Answer the question based STRICTLY on the retrieved context below.

=== Retrieved Context ===
{context}

=== Question ===
{question}

=== Instructions ===
1. Start with a direct and clear answer.
2. Use only the retrieved context.Support your answer using ALL relevant findings from the retrieved context — do not omit key facts, statistics, or p-values that are relevant.
3. Do not invent facts.
4. If the context is insufficient, say that the context does not provide enough information.
5. Interpret the evidence — do not just describe it. Example: say "X may drive Y" not just "X is associated with Y".
6. Keep the answer concise, clear, and useful.
7. Do not start with "According to the context".

=== Answer ===
""",
)

def generate_answer_with_model(
    question: str,
    project_id: int,
    model_key: str,
    model_name: str,
    top_k: int | None = None,
    retries: int = 3,
    wait_seconds: int = 10,
) -> dict:
    """
     equivalent to the notebook's ask_rag().
    1. Retrieve top-k chunks from Qdrant
    2. Build context
    3. Format RAG answer prompt
    4. Call one NVIDIA generator model
    5. Return answer + context + latency
    """

    if top_k is None:
        top_k = RAG_CONFIG["top_k"]

    retrieved_chunks = retrieve_relevant_chunks(
        question=question,
        project_id=project_id,
        top_k=top_k,
    )

    context = build_context_from_retrieved_chunks(retrieved_chunks)

    final_prompt = RAG_ANSWER_PROMPT.format(
        context=context,
        question=question,
    )

    llm = get_nvidia_chat_model(model_name)

    start_time = time.time()
    generated_answer = ""

    for attempt in range(1, retries + 1):
        try:
            response = llm.invoke(final_prompt)
            generated_answer = response.content.strip()

            if not generated_answer:
                raise ValueError("NVIDIA API returned an empty response.")

            break

        except Exception as e:
            if attempt < retries:
                time.sleep(wait_seconds)
            else:
                generated_answer = f"[ERROR] {str(e)}"

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "model_key": model_key,
        "model_name": model_name,
        "question": question,
        "generated_answer": generated_answer,
        "retrieved_contexts": retrieved_chunks,
        "full_context": context,
        "latency_ms": latency_ms,
    }


def get_default_generator_models() -> dict[str, str]:
    """
    Returns the generator model registry from config.
    """

    return RAG_CONFIG["generator_models"]
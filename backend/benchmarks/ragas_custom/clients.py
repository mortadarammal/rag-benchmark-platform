\
# backend/benchmarks/ragas_custom/clients.py

"""
NVIDIA + RAGAS resource builders.

This mirrors notebook Phase 3:

judge_llm = LangchainLLMWrapper(ChatNVIDIA(...))

judge_embeddings = LangchainEmbeddingsWrapper(
    NVIDIAEmbeddings(model=CONFIG["embedding_model"])
)

"""

import os
from functools import lru_cache
from typing import Any

from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper

from rag.config import RAG_CONFIG


DEFAULT_JUDGE_MODEL = "mistralai/mistral-large-3-675b-instruct-2512"
DEFAULT_EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-1b-v2"


def get_rag_config_value(name: str, default: Any = None) -> Any:
    try:
        return RAG_CONFIG.get(name, default)
    except Exception:
        return default


def get_judge_model_name() -> str:
    return (
        get_rag_config_value("judge_model")
        or os.getenv("NVIDIA_JUDGE_MODEL")
        or DEFAULT_JUDGE_MODEL
    )


def get_embedding_model_name() -> str:
    return (
        get_rag_config_value("embedding_model")
        or get_rag_config_value("nvidia_embedding_model")
        or os.getenv("NVIDIA_EMBEDDING_MODEL")
        or DEFAULT_EMBEDDING_MODEL
    )


@lru_cache(maxsize=1)
def get_judge_llm_raw() -> ChatNVIDIA:
    return ChatNVIDIA(
        model=get_judge_model_name(),
        temperature=float(get_rag_config_value("judge_temperature", 0.0)),
        max_completion_tokens=int(
            get_rag_config_value("judge_max_completion_tokens", 2048)
        ),
    )


@lru_cache(maxsize=1)
def get_judge_llm_wrapped() -> LangchainLLMWrapper:
    return LangchainLLMWrapper(get_judge_llm_raw())


@lru_cache(maxsize=1)
def get_judge_embeddings_wrapped() -> LangchainEmbeddingsWrapper:
    api_key = os.getenv("NVIDIA_API_KEY")

    if api_key:
        embeddings = NVIDIAEmbeddings(
            model=get_embedding_model_name(),
            api_key=api_key,
        )
    else:
        embeddings = NVIDIAEmbeddings(
            model=get_embedding_model_name(),
        )

    return LangchainEmbeddingsWrapper(embeddings)

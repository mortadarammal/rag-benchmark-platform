# backend/llms/nvidia_client.py

import os

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from rag.config import RAG_CONFIG

def require_nvidia_api_key() -> str:
    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        raise ValueError("NVIDIA_API_KEY is missing from environment variables.")

    return api_key


def get_nvidia_llama() -> ChatNVIDIA:
    """
    Creates the NVIDIA-hosted Llama chat model.

    Simplified from your uploaded question generator file,
    where ChatNVIDIA was used for question generation.
    """

    api_key = require_nvidia_api_key()

    return ChatNVIDIA(
        model=RAG_CONFIG["chat_model"],
        api_key=api_key,
        temperature=RAG_CONFIG["temperature"],
        max_completion_tokens=RAG_CONFIG["max_tokens"],
    )


def get_nvidia_chat_model(model_name: str) -> ChatNVIDIA:
    """
    equivalent of the notebook:

        ChatNVIDIA(
            model=CONFIG["generator_models"][MODEL_KEY],
            temperature=CONFIG["temperature"],
            max_completion_tokens=CONFIG["max_completion_tokens"],
        )
    """

    api_key = require_nvidia_api_key()

    return ChatNVIDIA(
        model=model_name,
        api_key=api_key,
        temperature=RAG_CONFIG["temperature"],
        max_completion_tokens=RAG_CONFIG["max_tokens"],
    )


def get_nvidia_judge_model() -> ChatNVIDIA:


    api_key = require_nvidia_api_key()

    return ChatNVIDIA(
        model=RAG_CONFIG["judge_model"],
        api_key=api_key,
        temperature=RAG_CONFIG["judge_temperature"],
        max_completion_tokens=RAG_CONFIG["judge_max_tokens"],
    )
# backend/rag/embeddings.py

import os

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from rag.config import RAG_CONFIG


def get_embedding_model() -> NVIDIAEmbeddings:
    """
    Returns the NVIDIA embedding model.

    This comes from the notebook:

        NVIDIAEmbeddings(
            model=CONFIG["embedding_model"],
            api_key=os.environ["NVIDIA_API_KEY"],
        )
    """

    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        raise ValueError("NVIDIA_API_KEY is missing from environment variables.")

    return NVIDIAEmbeddings(
        model=RAG_CONFIG["embedding_model"],
        api_key=api_key,
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple document chunks.
    Used when storing uploaded document chunks in Qdrant.
    """

    embedding_model = get_embedding_model()
    return embedding_model.embed_documents(texts)


def embed_query(query: str) -> list[float]:
    """
    Embed a user question.
    Used when searching Qdrant.
    """

    embedding_model = get_embedding_model()
    return embedding_model.embed_query(query)
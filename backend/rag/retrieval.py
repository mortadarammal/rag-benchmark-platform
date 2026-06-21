# backend/rag/retrieval.py

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

from rag.config import RAG_CONFIG
from rag.embeddings import embed_query
from rag.vector_store import get_qdrant_client, get_collection_name


def retrieve_relevant_chunks(
    question: str,
    project_id: int,
    top_k: int | None = None,
) -> list[dict]:
    """
    Retrieve top-k chunks from Qdrant for one user question.

    This is the fullstack equivalent of:

        retriever.invoke(question)

    from your notebook.
    """

    if top_k is None:
        top_k = RAG_CONFIG["top_k"]

    client = get_qdrant_client()
    collection_name = get_collection_name()

    query_vector = embed_query(question)

    query_filter = Filter(
        must=[
            FieldCondition(
                key="project_id",
                match=MatchValue(value=project_id),
            )
        ]
    )

    # Newer Qdrant client versions use query_points.
    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    retrieved = []

    for point in result.points:
        payload = point.payload or {}

        retrieved.append(
            {
                "score": point.score,
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "source": payload.get("source"),
                "chunk_index": payload.get("chunk_index"),
                "text": payload.get("text"),
                "metadata": payload.get("metadata", {}),
            }
        )

    return retrieved


def build_context_from_retrieved_chunks(chunks: list[dict]) -> str:
    """
    Same idea as your notebook's build_context_from_docs().
    """

    return "\n\n".join(
        chunk["text"]
        for chunk in chunks
        if chunk.get("text")
    )
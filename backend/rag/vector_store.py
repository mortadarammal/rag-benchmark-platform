# backend/rag/vector_store.py

import os
import uuid
from typing import Iterable

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)

from documents.models import DocumentChunk
from rag.embeddings import embed_texts


def get_qdrant_client() -> QdrantClient:
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url=qdrant_url)


def get_collection_name() -> str:
    return os.getenv("QDRANT_COLLECTION", "rag_benchmark_chunks")


def ensure_collection(vector_size: int) -> None:
    """
    Create the Qdrant collection if it does not exist.

    Qdrant collections require a fixed vector size and a distance metric.
    We use cosine similarity, which is standard for text embeddings.
    """

    client = get_qdrant_client()
    collection_name = get_collection_name()

    existing_collections = client.get_collections().collections
    existing_names = [collection.name for collection in existing_collections]

    if collection_name not in existing_names:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )


def make_qdrant_point_id(chunk_id: int) -> str:
    """
    Qdrant accepts UUID strings as point IDs.
    This creates a stable UUID from the Django chunk ID.
    """

    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"document-chunk-{chunk_id}"))


def store_chunks_in_qdrant(chunks: Iterable[DocumentChunk], batch_size: int = 32) -> int:
    """
    Embed Django DocumentChunk rows and store them in Qdrant.

    Each Qdrant point stores:
    - vector: NVIDIA embedding
    - payload: metadata + chunk text
    """

    chunks = list(chunks)

    if not chunks:
        return 0

    client = get_qdrant_client()
    collection_name = get_collection_name()

    total_stored = 0

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        texts = [chunk.text for chunk in batch]

        vectors = embed_texts(texts)

        if start == 0:
            ensure_collection(vector_size=len(vectors[0]))

        points = []

        for chunk, vector in zip(batch, vectors):
            point_id = make_qdrant_point_id(chunk.id)

            payload = {
                "project_id": chunk.document.project_id,
                "document_id": chunk.document_id,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "source": chunk.document.original_name,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

            chunk.vector_id = point_id

        client.upsert(
            collection_name=collection_name,
            points=points,
        )

        DocumentChunk.objects.bulk_update(batch, ["vector_id"])

        total_stored += len(batch)

    return total_stored
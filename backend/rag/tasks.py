# # backend/rag/tasks.py

# from celery import shared_task
# from django.utils import timezone

# from documents.models import UploadedDocument, DocumentChunk
# from rag.loaders import load_uploaded_file
# from rag.chunking import chunk_uploaded_document


# @shared_task
# def process_uploaded_document(document_id: int):
#     """
#     Phase 1 task.

#     Steps:
#     1. Mark document as processing
#     2. Extract text from uploaded file
#     3. Convert text into LangChain Document
#     4. Chunk using RecursiveCharacterTextSplitter
#     5. Save chunks to PostgreSQL
#     6. Mark document as ready

#     This is the Django/Celery version of your notebook's:
#     - Document preparation
#     - Chunking
#     """

#     document = UploadedDocument.objects.get(id=document_id)

#     try:
#         document.status = "processing"
#         document.error_message = None
#         document.save(update_fields=["status", "error_message"])

#         # 1. Load text from file
#         text = load_uploaded_file(document.file.path)

#         if not text.strip():
#             raise ValueError("No text could be extracted from this file.")

#         # 2. Chunk document using your notebook's splitter logic
#         split_docs = chunk_uploaded_document(
#             text=text,
#             source_name=document.original_name,
#             document_id=document.id,
#         )

#         # 3. Delete old chunks if re-processing
#         DocumentChunk.objects.filter(document=document).delete()

#         # 4. Save chunks into PostgreSQL
#         chunks_to_create = []

#         for index, chunk in enumerate(split_docs):
#             chunks_to_create.append(
#                 DocumentChunk(
#                     document=document,
#                     chunk_index=index,
#                     text=chunk.page_content,
#                     metadata={
#                         **chunk.metadata,
#                         "chunk_index": index,
#                         "chunk_size": len(chunk.page_content),
#                     },
#                 )
#             )

#         DocumentChunk.objects.bulk_create(chunks_to_create)

#         document.status = "ready"
#         document.processed_at = timezone.now()
#         document.save(update_fields=["status", "processed_at"])

#         return {
#             "document_id": document.id,
#             "status": "ready",
#             "chunks_created": len(chunks_to_create),
#         }

#     except Exception as e:
#         document.status = "failed"
#         document.error_message = str(e)
#         document.save(update_fields=["status", "error_message"])

#         raise

# backend/rag/tasks.py

from celery import shared_task
from django.utils import timezone

from documents.models import UploadedDocument, DocumentChunk
from rag.loaders import load_uploaded_file
from rag.chunking import chunk_uploaded_document
from rag.vector_store import store_chunks_in_qdrant


@shared_task
def process_uploaded_document(document_id: int):
    """
    Phase 1 + Phase 2 task.

    Phase 1:
    - extract text
    - chunk document
    - save chunks in PostgreSQL

    Phase 2:
    - embed chunks with NVIDIAEmbeddings
    - store vectors in Qdrant
    - save Qdrant vector IDs in PostgreSQL
    """

    document = UploadedDocument.objects.get(id=document_id)

    try:
        document.status = "processing"
        document.error_message = None
        document.save(update_fields=["status", "error_message"])

        # 1. Load text from uploaded file
        text = load_uploaded_file(document.file.path)

        if not text.strip():
            raise ValueError("No text could be extracted from this file.")

        # 2. Chunk document using your notebook's splitter logic
        split_docs = chunk_uploaded_document(
            text=text,
            source_name=document.original_name,
            document_id=document.id,
        )

        # 3. Delete old chunks if re-processing
        DocumentChunk.objects.filter(document=document).delete()

        # 4. Save chunks in PostgreSQL
        chunks_to_create = []

        for index, chunk in enumerate(split_docs):
            chunks_to_create.append(
                DocumentChunk(
                    document=document,
                    chunk_index=index,
                    text=chunk.page_content,
                    metadata={
                        **chunk.metadata,
                        "chunk_index": index,
                        "chunk_size": len(chunk.page_content),
                    },
                )
            )

        DocumentChunk.objects.bulk_create(chunks_to_create)

        document.status = "chunked"
        document.save(update_fields=["status"])

        # 5. Reload chunks from DB so they have IDs
        saved_chunks = DocumentChunk.objects.filter(
            document=document,
        ).order_by("chunk_index")

        # 6. Embed with NVIDIA and store in Qdrant
        stored_count = store_chunks_in_qdrant(saved_chunks)

        document.status = "ready"
        document.processed_at = timezone.now()
        document.save(update_fields=["status", "processed_at"])

        return {
            "document_id": document.id,
            "status": "ready",
            "chunks_created": len(chunks_to_create),
            "vectors_stored": stored_count,
        }

    except Exception as e:
        document.status = "failed"
        document.error_message = str(e)
        document.save(update_fields=["status", "error_message"])

        raise
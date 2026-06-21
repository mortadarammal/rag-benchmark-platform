# backend/rag/chunking.py

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.config import RAG_CONFIG


def build_langchain_document(
    text: str,
    source_name: str,
    document_id: int,
) -> Document:
    """
    Convert extracted text into a LangChain Document.

    This is adapted from your notebook's Document creation logic.
    In the notebook, metadata came from PubMedQA.
    Here, metadata comes from the uploaded file.
    """

    return Document(
        page_content=text,
        metadata={
            "document_id": document_id,
            "source": source_name,
        },
    )


def chunk_uploaded_document(
    text: str,
    source_name: str,
    document_id: int,
) -> list[Document]:
    """
    Split one uploaded file into chunks.

    This uses the same RecursiveCharacterTextSplitter logic
    from your notebook.
    """

    document = build_langchain_document(
        text=text,
        source_name=source_name,
        document_id=document_id,
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=RAG_CONFIG["chunk_size"],
        chunk_overlap=RAG_CONFIG["chunk_overlap"],
    )

    split_docs = text_splitter.split_documents([document])

    return split_docs
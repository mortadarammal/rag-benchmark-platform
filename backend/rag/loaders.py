# backend/rag/loaders.py

from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument


def load_uploaded_file(file_path: str) -> str:
    """
    Extract text from an uploaded file.

    Supported for Phase 1:
    - .txt
    - .md
    - .pdf
    - .docx
    """

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        return load_pdf(file_path)

    if suffix == ".docx":
        return load_docx(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")


def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)

    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "\n\n".join(pages)


def load_docx(file_path: str) -> str:
    doc = DocxDocument(file_path)

    paragraphs = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text.strip())

    return "\n\n".join(paragraphs)
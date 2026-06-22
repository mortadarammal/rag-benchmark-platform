# backend/benchmarks/question_generation.py

import json
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from llms.nvidia_client import get_nvidia_llama
from rag.config import RAG_CONFIG
from rag.retrieval import retrieve_relevant_chunks


def clean_json_from_llm(text: str) -> str:
    """
    Extract JSON from common LLM responses that may include markdown fences.
    """

    text = text.strip()

    fenced_match = re.search(
        r"```(?:json)?\s*(.*?)```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if fenced_match:
        return fenced_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()

    return text


def safe_json_loads(text: str) -> dict[str, Any]:
    cleaned = clean_json_from_llm(text)
    return json.loads(cleaned)


class SimpleQuestionGenerator:
 

    def __init__(self):
        self.llm = get_nvidia_llama()

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You generate clear, useful questions from document context.

Rules:
- Use only the provided context.
- Generate questions that a user can ask to compare LLM answers.
- Do not generate answers.
- Do not include question type.
- Do not include difficulty.
- Avoid duplicate questions.
- Avoid vague questions like "What is discussed in the document?"
- Return only valid JSON.
- Do not include markdown.
""",
                ),
                (
                    "human",
                    """
Generate {number_of_questions} questions from this context.

Return exactly this JSON format:

{{
  "questions": [
    "question 1",
    "question 2",
    "question 3"
  ]
}}

Context:
\"\"\"{context}\"\"\"
""",
                ),
            ]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_from_context(
        self,
        context: str,
        number_of_questions: int,
    ) -> list[str]:
        raw = self.chain.invoke(
            {
                "context": context,
                "number_of_questions": number_of_questions,
            }
        )

        data = safe_json_loads(raw)
        questions = data.get("questions", [])

        cleaned_questions = []

        for question in questions:
            if not isinstance(question, str):
                continue

            question = question.strip()

            if not question:
                continue

            if not question.endswith("?"):
                question += "?"

            cleaned_questions.append(question)

        return cleaned_questions


def build_context_from_project_chunks(
    project_id: int,
    query: str = "Generate useful questions from this document.",
    top_k: int | None = None,
) -> tuple[str, list[dict]]:
    """
    Uses Phase 2 retrieval to get relevant chunks from Qdrant.
    """

    if top_k is None:
        top_k = RAG_CONFIG["top_k"]

    chunks = retrieve_relevant_chunks(
        question=query,
        project_id=project_id,
        top_k=top_k,
    )

    context = "\n\n".join(
        chunk["text"]
        for chunk in chunks
        if chunk.get("text")
    )

    return context, chunks


def generate_questions_for_project(
    project_id: int,
    number_of_questions: int | None = None,
) -> tuple[list[str], list[dict]]:
    """
    Full Phase 3 generation function.

    Steps:
    1. Retrieve project chunks from Qdrant
    2. Build context
    3. Ask NVIDIA Llama to generate questions
    """

    if number_of_questions is None:
        number_of_questions = RAG_CONFIG["questions_per_generation"]

    context, chunks = build_context_from_project_chunks(
        project_id=project_id,
        top_k=RAG_CONFIG["top_k"],
    )

    if not context.strip():
        raise ValueError(
            "No context found for this project. Upload and process documents first."
        )

    generator = SimpleQuestionGenerator()

    questions = generator.generate_from_context(
        context=context,
        number_of_questions=number_of_questions,
    )

    return questions, chunks
#from django.shortcuts import render

# Create your views here.
# backend/rag/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rag.config import RAG_CONFIG
from rag.retrieval import (
    retrieve_relevant_chunks,
    build_context_from_retrieved_chunks,
)


class RetrievalView(APIView):
    """
    API endpoint for testing retrieval.

    Input:
        {
            "project_id": 1,
            "question": "What is this document about?",
            "top_k": 5
        }

    Output:
        retrieved chunks from Qdrant
    """

    def post(self, request):
        project_id = request.data.get("project_id")
        question = request.data.get("question")
        top_k = request.data.get("top_k", RAG_CONFIG["top_k"])

        if not project_id:
            return Response(
                {"error": "project_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not question:
            return Response(
                {"error": "question is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            top_k = int(top_k)
        except ValueError:
            return Response(
                {"error": "top_k must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chunks = retrieve_relevant_chunks(
            question=question,
            project_id=int(project_id),
            top_k=top_k,
        )

        context = build_context_from_retrieved_chunks(chunks)

        return Response(
            {
                "project_id": int(project_id),
                "question": question,
                "top_k": top_k,
                "chunks": chunks,
                "context": context,
            }
        )
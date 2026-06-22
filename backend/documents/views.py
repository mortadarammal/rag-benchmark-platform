
# backend/documents/views.py

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UploadedDocument, DocumentChunk
from .serializers import UploadedDocumentSerializer, DocumentChunkSerializer
from rag.tasks import process_uploaded_document


class DocumentUploadView(generics.CreateAPIView):
    serializer_class = UploadedDocumentSerializer

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get("file")

        document = serializer.save(
            original_name=uploaded_file.name,
            status="uploaded",
        )

        process_uploaded_document.delay(document.id)


class DocumentListView(generics.ListAPIView):
    serializer_class = UploadedDocumentSerializer

    def get_queryset(self):
        project_id = self.kwargs["project_id"]

        return UploadedDocument.objects.filter(
            project_id=project_id,
        ).order_by("-created_at")


class DocumentStatusView(APIView):
    def get(self, request, document_id):
        document = UploadedDocument.objects.get(id=document_id)

        return Response(
            {
                "id": document.id,
                "original_name": document.original_name,
                "status": document.status,
                "error_message": document.error_message,
                "chunks_count": document.chunks.count(),
                "created_at": document.created_at,
                "processed_at": document.processed_at,
            }
        )


class DocumentChunksView(generics.ListAPIView):
    serializer_class = DocumentChunkSerializer

    def get_queryset(self):
        document_id = self.kwargs["document_id"]

        return DocumentChunk.objects.filter(
            document_id=document_id,
        ).order_by("chunk_index")
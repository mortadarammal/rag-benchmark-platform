# backend/rag/urls.py

from django.urls import path

from .views import RetrievalView

urlpatterns = [
    path("retrieve/", RetrievalView.as_view(), name="rag-retrieve"),
]
"""Embedding provider abstractions and vector store adapter."""

from app.embeddings.factory import get_embedding_provider
from app.embeddings.protocol import EmbeddingProvider, EmbeddingResult
from app.embeddings.store import VectorStore

__all__ = [
    "EmbeddingProvider",
    "EmbeddingResult",
    "VectorStore",
    "get_embedding_provider",
]

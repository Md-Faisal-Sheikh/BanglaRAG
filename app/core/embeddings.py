"""Embedding providers behind a common interface.

The default is BAAI/bge-m3 (open, multilingual, runs locally, strong on Bangla).
Swap to OpenAI by setting EMBEDDING_PROVIDER=openai. The interface is what lets the
evaluation harness compare embedders as one axis of the experiment.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import Settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbeddings(EmbeddingProvider):
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # lazy import (heavy)

        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()


class OpenAIEmbeddings(EmbeddingProvider):
    def __init__(self, model_name: str, api_key: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model_name

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddings(settings.openai_embedding_model, settings.openai_api_key)
    return SentenceTransformerEmbeddings(settings.embedding_model)

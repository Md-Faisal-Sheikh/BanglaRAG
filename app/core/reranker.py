"""Rerankers behind a common interface. Reranking is the with/without research axis.

Default is a multilingual cross-encoder (BAAI/bge-reranker-v2-m3) that pairs with
bge-m3. NoOpReranker keeps the original retrieval order (the 'without rerank' arm).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import Settings
from app.core.vectorstore import RetrievedChunk


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]: ...


class NoOpReranker(Reranker):
    def rerank(self, query, candidates, top_k):
        return candidates[:top_k]


class CrossEncoderReranker(Reranker):
    def __init__(self, model_name: str):
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name)

    def rerank(self, query, candidates, top_k):
        if not candidates:
            return []
        pairs = [(query, c.text) for c in candidates]
        scores = self.model.predict(pairs)
        for c, s in zip(candidates, scores):
            c.score = float(s)
        ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
        return ranked[:top_k]


class CohereReranker(Reranker):
    def __init__(self, model_name: str, api_key: str):
        import cohere

        self.client = cohere.Client(api_key)
        self.model = model_name

    def rerank(self, query, candidates, top_k):
        if not candidates:
            return []
        docs = [c.text for c in candidates]
        res = self.client.rerank(query=query, documents=docs, top_n=top_k, model=self.model)
        out = []
        for r in res.results:
            c = candidates[r.index]
            c.score = float(r.relevance_score)
            out.append(c)
        return out


def get_reranker(settings: Settings) -> Reranker:
    if not settings.use_reranker or settings.reranker_provider == "none":
        return NoOpReranker()
    if settings.reranker_provider == "cohere":
        return CohereReranker("rerank-multilingual-v3.0", settings.cohere_api_key)
    return CrossEncoderReranker(settings.reranker_model)

"""Vector store behind a common interface.

Default is Chroma (persistent, local, zero external services — ideal to get running).
A Qdrant implementation stub is included for the production upgrade path. Each
'collection' is independent, which the eval harness exploits: it builds a fresh
collection per experiment config so indexes never bleed across runs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import Settings


@dataclass
class RetrievedChunk:
    id: str
    text: str
    source: str          # source document (filename / title) — used for hit-rate
    score: float         # similarity (or rerank) score
    metadata: dict


class VectorStore(ABC):
    @abstractmethod
    def add(self, ids, embeddings, documents, metadatas) -> None: ...

    @abstractmethod
    def query(self, query_embedding: list[float], k: int) -> list[RetrievedChunk]: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def count(self) -> int: ...


class ChromaVectorStore(VectorStore):
    def __init__(self, persist_dir: str, collection_name: str):
        import chromadb

        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add(self, ids, embeddings, documents, metadatas) -> None:
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def query(self, query_embedding: list[float], k: int) -> list[RetrievedChunk]:
        res = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        out: list[RetrievedChunk] = []
        ids = res["ids"][0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        for cid, doc, meta, dist in zip(ids, docs, metas, dists):
            out.append(
                RetrievedChunk(
                    id=cid,
                    text=doc,
                    source=meta.get("source", "unknown"),
                    score=1.0 - float(dist),   # cosine distance -> similarity
                    metadata=meta,
                )
            )
        return out

    def reset(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return self.collection.count()


def get_vector_store(settings: Settings, collection_name: str | None = None) -> VectorStore:
    name = collection_name or settings.collection_name
    if settings.vector_store == "qdrant":
        raise NotImplementedError(
            "Qdrant adapter is a stub. See docs/ARCHITECTURE.md for the upgrade path."
        )
    return ChromaVectorStore(settings.chroma_dir, name)

"""Ingestion: takes raw documents -> chunks -> embeddings -> vector store, and records
corpus metadata (with versioning) in the relational DB.

Chunk IDs are deterministic ("{source}::v{version}::{i}") so re-ingesting a document
can replace its old chunks cleanly.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import Settings
from app.core.chunking import get_chunker
from app.core.embeddings import EmbeddingProvider
from app.core.vectorstore import VectorStore
from app.db.models import Document


@dataclass
class RawDoc:
    source: str       # filename or external id
    title: str
    text: str
    lang: str = "bn"


def ingest_documents(
    docs: list[RawDoc],
    embedder: EmbeddingProvider,
    store: VectorStore,
    settings: Settings,
    db: Session | None = None,
) -> int:
    """Index a batch of documents. Returns total chunks indexed."""
    chunker = get_chunker(settings.chunker)
    total_chunks = 0

    for doc in docs:
        version = 1
        if db is not None:
            existing = db.query(Document).filter(Document.source == doc.source).first()
            if existing:
                version = existing.version + 1

        chunks = chunker(doc.text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            continue

        ids = [f"{doc.source}::v{version}::{i}" for i in range(len(chunks))]
        metadatas = [
            {"source": doc.title or doc.source, "doc_id": doc.source,
             "version": version, "lang": doc.lang, "chunk_index": i}
            for i in range(len(chunks))
        ]
        embeddings = embedder.embed_documents(chunks)
        store.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        total_chunks += len(chunks)

        if db is not None:
            if existing:
                existing.version = version
                existing.n_chunks = len(chunks)
                existing.title = doc.title
            else:
                db.add(Document(source=doc.source, title=doc.title, lang=doc.lang,
                                version=version, n_chunks=len(chunks)))
            db.commit()

    return total_chunks

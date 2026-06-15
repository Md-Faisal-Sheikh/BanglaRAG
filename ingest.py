"""Ingest the corpus into the *live* application index (the one the API serves).

    python ingest.py --corpus data/corpus

This populates the vector store and records Document rows, so the running chat API
can answer over these documents. (The evaluation harness builds its own throwaway
indexes and does not touch this one.)
"""
from __future__ import annotations

import argparse
import os

from app.config import get_settings
from app.core.embeddings import get_embedding_provider
from app.core.vectorstore import get_vector_store
from app.db.database import SessionLocal, init_db
from app.services.ingestion import RawDoc, ingest_documents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--reset", action="store_true", help="clear the index first")
    args = ap.parse_args()

    settings = get_settings()
    init_db()

    embedder = get_embedding_provider(settings)
    store = get_vector_store(settings)
    if args.reset:
        store.reset()

    docs = []
    for fn in sorted(os.listdir(args.corpus)):
        if fn.endswith(".txt"):
            stem = os.path.splitext(fn)[0]
            with open(os.path.join(args.corpus, fn), encoding="utf-8") as f:
                docs.append(RawDoc(source=stem, title=stem, text=f.read(), lang="bn"))

    db = SessionLocal()
    try:
        n = ingest_documents(docs, embedder, store, settings, db=db)
    finally:
        db.close()

    print(f"Indexed {len(docs)} documents, {n} chunks into collection "
          f"'{settings.collection_name}' (store={settings.vector_store}).")


if __name__ == "__main__":
    main()

"""Tests for document upload extraction, BM25 lexical retrieval, hybrid (RRF) fusion,
and the corpus-management correctness fixes (no orphaned chunks, delete-by-doc).

These run on the lightweight stack (hash embeddings + memory store) so they need no
model downloads — the same configuration the hosted demo uses."""
from __future__ import annotations

import pytest

from app.config import Settings
from app.core.embeddings import HashEmbeddings
from app.core.lexical import BM25, LexicalIndex, tokenize
from app.core.llm import MockLLM
from app.core.rag_pipeline import RAGConfig, RAGPipeline
from app.core.reranker import NoOpReranker
from app.core.vectorstore import MemoryVectorStore
from app.services.extraction import (
    UnsupportedFileType,
    extract_text,
)
from app.services.ingestion import RawDoc, ingest_documents

PASSPORT = "ই-পাসপোর্টের জন্য অনলাইনে আবেদন করতে হয়। আবেদন ফি ব্যাংকে জমা দিতে হয়।"
NID = "জাতীয় পরিচয়পত্র সংশোধনের জন্য নির্বাচন কমিশনের অফিসে যেতে হয়।"


def _index(store, embedder, settings, *docs):
    ingest_documents(list(docs), embedder=embedder, store=store, settings=settings)


def _settings(**kw) -> Settings:
    return Settings(chunker="recursive", chunk_size=512, chunk_overlap=64, **kw)


# --- extraction ---------------------------------------------------------------

def test_extract_txt_and_md():
    assert extract_text("a.txt", PASSPORT.encode("utf-8")) == PASSPORT
    assert "##" in extract_text("a.md", b"## title\nbody")


def test_extract_unknown_extension_rejected():
    with pytest.raises(UnsupportedFileType):
        extract_text("a.xyz", b"data")


def test_extract_handles_utf16():
    assert extract_text("a.txt", PASSPORT.encode("utf-16")) == PASSPORT


# --- BM25 / lexical -----------------------------------------------------------

def test_tokenize_keeps_bangla_and_digits():
    toks = tokenize("ফি ১০০ টাকা।")
    assert "ফি" in toks and "১০০" in toks and "।" not in toks


def test_bm25_ranks_keyword_match_first():
    bm25 = BM25([tokenize(PASSPORT), tokenize(NID)])
    scores = bm25.scores("পাসপোর্ট আবেদন")
    assert scores[0] > scores[1]  # passport doc wins on the passport query


def test_lexical_index_tracks_store_changes():
    settings, embedder = _settings(), HashEmbeddings()
    store = MemoryVectorStore()
    lex = LexicalIndex(store)
    assert lex.search("পাসপোর্ট", 5) == []      # empty corpus

    _index(store, embedder, settings, RawDoc("passport", "Passport", PASSPORT))
    hits = lex.search("পাসপোর্ট আবেদন", 5)         # index rebuilds on count change
    assert hits and "পাসপোর্ট" in hits[0].text


# --- ingestion correctness ----------------------------------------------------

def test_reingest_replaces_chunks_no_orphans():
    settings, embedder = _settings(), HashEmbeddings()
    store = MemoryVectorStore()
    _index(store, embedder, settings, RawDoc("doc", "Doc", "পুরোনো তথ্য।"))
    first = store.count()
    assert first > 0

    # Re-ingest the same source with new text: old chunks must be gone.
    _index(store, embedder, settings, RawDoc("doc", "Doc", "নতুন হালনাগাদ তথ্য।"))
    texts = [t for _id, t, _m in store.all_documents()]
    assert all("পুরোনো" not in t for t in texts)
    assert all(meta.get("doc_id") == "doc" for _id, _t, meta in store.all_documents())


def test_delete_by_doc_removes_only_that_doc():
    settings, embedder = _settings(), HashEmbeddings()
    store = MemoryVectorStore()
    _index(store, embedder, settings,
           RawDoc("passport", "Passport", PASSPORT),
           RawDoc("nid", "NID", NID))
    store.delete_by_doc("passport")
    remaining = {meta.get("doc_id") for _id, _t, meta in store.all_documents()}
    assert remaining == {"nid"}


# --- hybrid retrieval end-to-end ---------------------------------------------

def _pipeline(store, embedder, mode):
    return RAGPipeline(
        embedder=embedder,
        store=store,
        reranker=NoOpReranker(),
        llm=MockLLM(),
        lexical=LexicalIndex(store) if mode == "hybrid" else None,
        config=RAGConfig(retrieval_mode=mode, top_k=10, rerank_k=3, use_reranker=False),
    )


def test_hybrid_retrieves_keyword_doc():
    settings, embedder = _settings(), HashEmbeddings()
    store = MemoryVectorStore()
    _index(store, embedder, settings,
           RawDoc("passport", "Passport", PASSPORT),
           RawDoc("nid", "NID", NID))
    chunks = _pipeline(store, embedder, "hybrid").retrieve("পাসপোর্ট আবেদন ফি")
    assert chunks
    assert chunks[0].source == "Passport"


def test_dense_mode_still_works_without_lexical():
    settings, embedder = _settings(), HashEmbeddings()
    store = MemoryVectorStore()
    _index(store, embedder, settings, RawDoc("nid", "NID", NID))
    chunks = _pipeline(store, embedder, "dense").retrieve("পরিচয়পত্র")
    assert chunks and chunks[0].source == "NID"

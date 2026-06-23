"""Lexical (sparse) retrieval: a self-contained BM25 index.

Dense vectors (bge-m3 / hash) match on meaning but can miss exact Bangla keywords,
form names, fees, or numbers a user types verbatim. BM25 is the classic lexical
counterweight. The pipeline fuses the two ranked lists with Reciprocal Rank Fusion
(see ``RAGPipeline``), which is the "hybrid retrieval" research axis.

Implemented in pure Python (no extra dependency) so it runs identically in the slim
hosted demo and the full local stack. The index is rebuilt from the vector store's
contents and is cheap to recompute for the corpus sizes this system targets.
"""
from __future__ import annotations

import math
import re

from app.core.vectorstore import RetrievedChunk, VectorStore

# Match a run of Bangla-block characters (U+0980–U+09FF) OR a run of Latin
# letters/digits. The Bangla class is deliberate: ``\w`` excludes Bangla vowel signs
# (matras, category Mn/Mc), which shatters words — "টাকা" -> "ট","ক". Keeping the whole
# block holds words together. Punctuation, whitespace and the danda '।' (U+0964) fall
# outside both classes and are dropped. lower() only affects the embedded Latin text.
_TOKEN_RE = re.compile(r"[ঀ-৿]+|[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25:
    """Okapi BM25 with an inverted index so scoring touches only matching docs."""

    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.n_docs = len(corpus)
        self.doc_len = [len(doc) for doc in corpus]
        self.avgdl = (sum(self.doc_len) / self.n_docs) if self.n_docs else 0.0

        # postings: token -> list of (doc_index, term_frequency)
        self.postings: dict[str, list[tuple[int, int]]] = {}
        for i, doc in enumerate(corpus):
            freqs: dict[str, int] = {}
            for tok in doc:
                freqs[tok] = freqs.get(tok, 0) + 1
            for tok, f in freqs.items():
                self.postings.setdefault(tok, []).append((i, f))

        self.idf: dict[str, float] = {}
        for tok, plist in self.postings.items():
            df = len(plist)
            # BM25+ style idf floor keeps it non-negative even for very common terms.
            self.idf[tok] = math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))

    def scores(self, query: str) -> list[float]:
        scores = [0.0] * self.n_docs
        if not self.n_docs or self.avgdl == 0.0:
            return scores
        for tok in tokenize(query):
            idf = self.idf.get(tok)
            if idf is None:
                continue
            for i, f in self.postings[tok]:
                denom = f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avgdl)
                scores[i] += idf * (f * (self.k1 + 1)) / denom
        return scores


class LexicalIndex:
    """A BM25 view over a :class:`VectorStore`, kept in sync with its contents.

    The store is the single source of truth for which chunks exist; this index is
    rebuilt whenever the store's chunk count changes (i.e. after an admin adds or
    deletes a document), so it never drifts out of date even though the pipeline
    that holds it is cached for the process lifetime.
    """

    def __init__(self, store: VectorStore):
        self._store = store
        self._built_at_count = -1
        self._chunks: list[RetrievedChunk] = []
        self._bm25: BM25 | None = None

    def _ensure_current(self) -> None:
        count = self._store.count()
        if self._bm25 is not None and count == self._built_at_count:
            return
        rows = self._store.all_documents()
        self._chunks = [
            RetrievedChunk(
                id=cid,
                text=text,
                source=(meta or {}).get("source", "unknown"),
                score=0.0,
                metadata=meta or {},
            )
            for cid, text, meta in rows
        ]
        self._bm25 = BM25([tokenize(c.text) for c in self._chunks])
        self._built_at_count = count

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        self._ensure_current()
        if not self._chunks:
            return []
        scores = self._bm25.scores(query)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        out: list[RetrievedChunk] = []
        for i in order[:k]:
            if scores[i] <= 0.0:
                break  # no lexical overlap beyond this point
            c = self._chunks[i]
            out.append(
                RetrievedChunk(id=c.id, text=c.text, source=c.source,
                               score=float(scores[i]), metadata=c.metadata)
            )
        return out

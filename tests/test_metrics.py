"""Tests for evaluation metrics (run with: pytest)."""
import math

from app.core.vectorstore import RetrievedChunk
from evaluation.metrics import abstention_correct, hit_rate_at_k, recall_at_k


def _chunk(doc_id: str) -> RetrievedChunk:
    return RetrievedChunk(id=doc_id, text="x", source=doc_id, score=1.0,
                          metadata={"doc_id": doc_id})


def test_hit_rate_hit():
    chunks = [_chunk("A"), _chunk("B"), _chunk("C")]
    assert hit_rate_at_k(chunks, ["B"], k=3) == 1.0
    assert hit_rate_at_k(chunks, ["B"], k=1) == 0.0  # B not in top-1


def test_hit_rate_miss():
    chunks = [_chunk("A"), _chunk("B")]
    assert hit_rate_at_k(chunks, ["Z"], k=2) == 0.0


def test_recall_partial():
    chunks = [_chunk("A"), _chunk("B")]
    assert recall_at_k(chunks, ["A", "Z"], k=2) == 0.5


def test_unanswerable_returns_nan():
    chunks = [_chunk("A")]
    assert math.isnan(hit_rate_at_k(chunks, [], k=3))


def test_abstention_logic():
    assert abstention_correct(grounded=True, answerable=True) == 1.0
    assert abstention_correct(grounded=False, answerable=False) == 1.0
    assert abstention_correct(grounded=True, answerable=False) == 0.0   # hallucinated
    assert abstention_correct(grounded=False, answerable=True) == 0.0   # over-refused

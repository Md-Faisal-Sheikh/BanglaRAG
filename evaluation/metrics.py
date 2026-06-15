"""Evaluation metrics for the faithfulness study.

Two families:
  1. Deterministic retrieval metrics (no LLM needed): hit-rate@k / recall@k against
     gold source document ids.
  2. LLM-as-judge metrics: faithfulness (is every claim supported by the retrieved
     context?) and answer correctness (does it match the gold answer?). Plus an
     abstention check (did it correctly refuse on unanswerable questions?).

Judge prompts deliberately include the token "JUDGE" so the offline MockLLM returns a
constant — real judges (GPT-4o-mini etc.) follow the rubric.
"""
from __future__ import annotations

import re

from app.core.llm import LLMProvider
from app.core.vectorstore import RetrievedChunk


# ---------- deterministic retrieval metrics ----------
def retrieved_doc_ids(chunks: list[RetrievedChunk]) -> list[str]:
    seen, out = set(), []
    for c in chunks:
        did = c.metadata.get("doc_id", c.source)
        if did not in seen:
            seen.add(did)
            out.append(did)
    return out


def hit_rate_at_k(chunks: list[RetrievedChunk], gold_doc_ids: list[str], k: int) -> float:
    """1.0 if any gold document appears in the top-k retrieved, else 0.0."""
    if not gold_doc_ids:
        return float("nan")  # not meaningful for unanswerable questions
    top = retrieved_doc_ids(chunks)[:k]
    return 1.0 if any(g in top for g in gold_doc_ids) else 0.0


def recall_at_k(chunks: list[RetrievedChunk], gold_doc_ids: list[str], k: int) -> float:
    if not gold_doc_ids:
        return float("nan")
    top = set(retrieved_doc_ids(chunks)[:k])
    hits = sum(1 for g in gold_doc_ids if g in top)
    return hits / len(gold_doc_ids)


# ---------- LLM-as-judge metrics ----------
_FAITH_SYS = (
    "You are a strict JUDGE of factual grounding. You are given CONTEXT and an ANSWER. "
    "Decide whether every factual claim in the ANSWER is directly supported by the CONTEXT. "
    "Reply with a single digit: 1 if fully grounded, 0 if any claim is unsupported or fabricated."
)

_CORRECT_SYS = (
    "You are a JUDGE of answer correctness. Given a QUESTION, a REFERENCE answer, and a "
    "CANDIDATE answer, decide whether the CANDIDATE conveys the same correct information as "
    "the REFERENCE. Reply with a single digit: 1 if correct/equivalent, 0 otherwise."
)


def _parse_binary(text: str) -> int:
    m = re.search(r"[01]", text)
    return int(m.group()) if m else 0


def faithfulness(answer: str, context: str, judge: LLMProvider) -> int:
    user = f"CONTEXT:\n{context}\n\nANSWER:\n{answer}"
    return _parse_binary(judge.generate(_FAITH_SYS, user, temperature=0.0))


def answer_correctness(question: str, candidate: str, reference: str, judge: LLMProvider) -> int:
    user = f"QUESTION: {question}\n\nREFERENCE: {reference}\n\nCANDIDATE: {candidate}"
    return _parse_binary(judge.generate(_CORRECT_SYS, user, temperature=0.0))


def abstention_correct(grounded: bool, answerable: bool) -> float:
    """For answerable questions we want grounded=True; for unanswerable we want the
    model to abstain (grounded=False)."""
    return 1.0 if grounded == answerable else 0.0

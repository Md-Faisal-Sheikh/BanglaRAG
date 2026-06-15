"""Chunking strategies. Chunking is one of the research axes, so each strategy is a
plain function returning a list of chunk strings.

- fixed:       fixed character window with overlap (baseline)
- recursive:   split on paragraph -> sentence -> word boundaries, packing to size
- sentence_bn: Bangla-aware sentence splitting (uses the danda '।' plus . ! ?),
               then packs whole sentences up to the size budget. This matters for
               Bangla because naive character windows cut mid-word/mid-grapheme.
"""
from __future__ import annotations

import re

_BN_SENT_BOUNDARY = re.compile(r"(?<=[।!?\.])\s+")
_PARA_BOUNDARY = re.compile(r"\n\s*\n")


def fixed_chunk(text: str, size: int = 512, overlap: int = 64) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks, start = [], 0
    step = max(1, size - overlap)
    while start < len(text):
        chunks.append(text[start : start + size])
        start += step
    return chunks


def _pack(units: list[str], size: int) -> list[str]:
    chunks, buf = [], ""
    for u in units:
        if not u:
            continue
        if len(buf) + len(u) + 1 <= size:
            buf = f"{buf} {u}".strip()
        else:
            if buf:
                chunks.append(buf)
            # a single oversized unit is hard-split
            buf = u if len(u) <= size else ""
            if len(u) > size:
                chunks.extend(fixed_chunk(u, size, 0))
    if buf:
        chunks.append(buf)
    return chunks


def recursive_chunk(text: str, size: int = 512, overlap: int = 64) -> list[str]:
    paras = _PARA_BOUNDARY.split(text.strip())
    sentences: list[str] = []
    for p in paras:
        sentences.extend(_BN_SENT_BOUNDARY.split(p.strip()))
    return _pack([s.strip() for s in sentences if s.strip()], size)


def sentence_chunk_bn(text: str, size: int = 512, overlap: int = 64) -> list[str]:
    sentences = [s.strip() for s in _BN_SENT_BOUNDARY.split(text.strip()) if s.strip()]
    return _pack(sentences, size)


_CHUNKERS = {
    "fixed": fixed_chunk,
    "recursive": recursive_chunk,
    "sentence_bn": sentence_chunk_bn,
}


def get_chunker(name: str):
    if name not in _CHUNKERS:
        raise ValueError(f"Unknown chunker '{name}'. Options: {list(_CHUNKERS)}")
    return _CHUNKERS[name]

"""Tests for chunking strategies (run with: pytest)."""
from app.core.chunking import fixed_chunk, get_chunker, recursive_chunk, sentence_chunk_bn

BN = ("বাংলাদেশ একটি সুন্দর দেশ। এখানে ছয়টি ঋতু আছে। নদীমাতৃক এই দেশের "
      "প্রকৃতি অপরূপ। রাজধানী ঢাকা একটি ব্যস্ত শহর।")


def test_fixed_chunk_respects_size():
    chunks = fixed_chunk(BN, size=20, overlap=5)
    assert chunks
    assert all(len(c) <= 20 for c in chunks)


def test_sentence_chunk_keeps_sentences_whole():
    # with a large budget everything fits in one chunk
    chunks = sentence_chunk_bn(BN, size=1000)
    assert len(chunks) == 1
    # with a tiny budget we get multiple chunks split on the danda
    chunks = sentence_chunk_bn(BN, size=30)
    assert len(chunks) > 1


def test_recursive_chunk_nonempty():
    assert recursive_chunk(BN, size=40) != []


def test_get_chunker_dispatch():
    assert get_chunker("fixed") is fixed_chunk
    assert get_chunker("sentence_bn") is sentence_chunk_bn


def test_empty_input():
    assert fixed_chunk("", 100, 10) == []

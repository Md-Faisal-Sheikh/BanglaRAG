"""The RAG pipeline: retrieve -> (rerank) -> grounded generation -> citation parsing.

Grounding rules baked into the prompt:
  * answer ONLY from the supplied context,
  * answer in Bangla,
  * cite supporting chunks inline as [1], [2], ...,
  * if the answer is not in the context, abstain with a fixed Bangla phrase.

The abstention behaviour is central to the faithfulness study: a faithful system
should refuse rather than fabricate when the corpus doesn't contain the answer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.embeddings import EmbeddingProvider
from app.core.llm import LLMProvider
from app.core.reranker import Reranker
from app.core.translation import translate
from app.core.vectorstore import RetrievedChunk, VectorStore

ABSTAIN_BN = "দুঃখিত, প্রদত্ত তথ্যসূত্রে এই প্রশ্নের উত্তর পাওয়া যায়নি।"

SYSTEM_PROMPT = (
    "আপনি একজন সহায়ক যিনি শুধুমাত্র নিচে দেওয়া তথ্যসূত্র (context) ব্যবহার করে বাংলায় উত্তর দেন।\n"
    "নিয়মাবলী:\n"
    "১. শুধুমাত্র দেওয়া context থেকে উত্তর দিন; নিজের ধারণা বা বাইরের তথ্য যোগ করবেন না।\n"
    "২. যে অংশ থেকে তথ্য নিয়েছেন তার নম্বর [1], [2] এভাবে উত্তরের ভেতরে উল্লেখ করুন।\n"
    f"৩. উত্তর context-এ না থাকলে ঠিক এই বাক্যটি লিখুন: \"{ABSTAIN_BN}\"\n"
    "৪. সংক্ষিপ্ত ও নির্ভুল উত্তর দিন।"
)

_CITATION_RE = re.compile(r"\[(\d+)\]")


@dataclass
class RAGConfig:
    retrieval_lang: str = "bn"      # "bn" native | "en" pivot
    top_k: int = 20
    rerank_k: int = 5
    use_reranker: bool = True


@dataclass
class RAGAnswer:
    answer: str
    grounded: bool
    citations: list[dict] = field(default_factory=list)
    retrieved: list[RetrievedChunk] = field(default_factory=list)


class RAGPipeline:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        store: VectorStore,
        reranker: Reranker,
        llm: LLMProvider,
        config: RAGConfig,
    ):
        self.embedder = embedder
        self.store = store
        self.reranker = reranker
        self.llm = llm
        self.config = config

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        query = question
        if self.config.retrieval_lang == "en":
            query = translate(question, "en", self.llm)
        q_emb = self.embedder.embed_query(query)
        candidates = self.store.query(q_emb, self.config.top_k)
        if self.config.use_reranker:
            candidates = self.reranker.rerank(question, candidates, self.config.rerank_k)
        else:
            candidates = candidates[: self.config.rerank_k]
        return candidates

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        blocks = []
        for i, c in enumerate(chunks, start=1):
            blocks.append(f"[{i}] (সূত্র: {c.source})\n{c.text}")
        return "\n\n".join(blocks)

    def answer(self, question: str) -> RAGAnswer:
        chunks = self.retrieve(question)
        if not chunks:
            return RAGAnswer(answer=ABSTAIN_BN, grounded=False, retrieved=[])

        context = self._build_context(chunks)
        user_prompt = f"তথ্যসূত্র:\n{context}\n\nপ্রশ্ন: {question}\n\nউত্তর:"
        raw = self.llm.generate(SYSTEM_PROMPT, user_prompt, temperature=0.0)

        grounded = ABSTAIN_BN[:20] not in raw
        citations = []
        for marker in sorted({int(m) for m in _CITATION_RE.findall(raw)}):
            if 1 <= marker <= len(chunks):
                c = chunks[marker - 1]
                citations.append(
                    {"marker": marker, "source": c.source,
                     "snippet": c.text[:300], "score": round(c.score, 4)}
                )
        return RAGAnswer(answer=raw, grounded=grounded, citations=citations, retrieved=chunks)

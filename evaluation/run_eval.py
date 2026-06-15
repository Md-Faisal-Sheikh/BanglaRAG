"""Run the faithfulness experiment matrix end-to-end and write a results table.

Usage:
    python -m evaluation.run_eval \
        --config evaluation/configs.yaml \
        --qa evaluation/qa_dataset.jsonl \
        --corpus data/corpus \
        --out evaluation/results.csv

For each experiment it: builds an isolated index (its own Chroma collection),
ingests the corpus under that config's chunking/language, answers every question,
and scores retrieval hit-rate, faithfulness, correctness, and abstention.

Cost note: the English-pivot arm and the LLM-as-judge make API calls. Translations
are cached in-process across experiments. For large corpora, persist translations to
disk and consider a dedicated MT model (NLLB) instead of prompting the LLM.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings                       # noqa: E402
from app.core.embeddings import get_embedding_provider    # noqa: E402
from app.core.llm import get_llm                           # noqa: E402
from app.core.rag_pipeline import RAGConfig, RAGPipeline   # noqa: E402
from app.core.reranker import get_reranker                 # noqa: E402
from app.core.translation import translate                 # noqa: E402
from app.core.vectorstore import get_vector_store          # noqa: E402
from app.services.ingestion import RawDoc, ingest_documents  # noqa: E402
from evaluation import metrics as M                         # noqa: E402

_TRANSLATION_CACHE: dict[str, str] = {}


def _mean(values: list[float]) -> float:
    vals = [v for v in values if not math.isnan(v)]
    return sum(vals) / len(vals) if vals else float("nan")


def load_corpus(corpus_dir: str) -> list[RawDoc]:
    docs = []
    for fn in sorted(os.listdir(corpus_dir)):
        if not fn.endswith(".txt"):
            continue
        stem = os.path.splitext(fn)[0]
        with open(os.path.join(corpus_dir, fn), encoding="utf-8") as f:
            docs.append(RawDoc(source=stem, title=stem, text=f.read(), lang="bn"))
    return docs


def load_qa(qa_path: str) -> list[dict]:
    with open(qa_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def prepare_docs_for_arm(docs: list[RawDoc], retrieval_lang: str, translator) -> list[RawDoc]:
    if retrieval_lang != "en":
        return docs
    out = []
    for d in docs:
        if d.source not in _TRANSLATION_CACHE:
            _TRANSLATION_CACHE[d.source] = translate(d.text, "en", translator)
        out.append(RawDoc(source=d.source, title=d.title,
                          text=_TRANSLATION_CACHE[d.source], lang="en"))
    return out


def run_experiment(exp: dict, top_cfg: dict, docs: list[RawDoc], qa: list[dict],
                   judge, ks: list[int]) -> dict:
    base = get_settings()
    emb_cfg = exp.get("embedding", top_cfg["embedding"])
    gen_cfg = top_cfg["generation"]

    settings = base.model_copy(update={
        "chunker": exp["chunker"],
        "chunk_size": exp["chunk_size"],
        "chunk_overlap": exp["chunk_overlap"],
        "retrieval_lang": exp["retrieval_lang"],
        "use_reranker": exp["use_reranker"],
        "top_k": exp["top_k"],
        "rerank_k": exp["rerank_k"],
        "embedding_provider": emb_cfg["provider"],
        "embedding_model": emb_cfg["model"],
        "llm_provider": gen_cfg["provider"],
        "llm_model": gen_cfg["model"],
        "collection_name": f"eval_{exp['name']}",
    })

    embedder = get_embedding_provider(settings)
    reranker = get_reranker(settings)
    store = get_vector_store(settings, collection_name=settings.collection_name)
    store.reset()
    gen_llm = get_llm(settings)

    arm_docs = prepare_docs_for_arm(docs, settings.retrieval_lang, gen_llm)
    n_chunks = ingest_documents(arm_docs, embedder, store, settings, db=None)

    pipeline = RAGPipeline(
        embedder=embedder, store=store, reranker=reranker, llm=gen_llm,
        config=RAGConfig(retrieval_lang=settings.retrieval_lang, top_k=settings.top_k,
                         rerank_k=settings.rerank_k, use_reranker=settings.use_reranker),
    )

    hit = {k: [] for k in ks}
    faith, correct, abst = [], [], []

    for item in qa:
        res = pipeline.answer(item["question"])
        abst.append(M.abstention_correct(res.grounded, item["answerable"]))
        if not item["answerable"]:
            continue
        for k in ks:
            hit[k].append(M.hit_rate_at_k(res.retrieved, item["gold_doc_ids"], k))
        context = "\n\n".join(c.text for c in res.retrieved)
        faith.append(M.faithfulness(res.answer, context, judge))
        correct.append(M.answer_correctness(item["question"], res.answer,
                                            item["gold_answer"], judge))

    row = {"experiment": exp["name"], "n_chunks": n_chunks}
    for k in ks:
        row[f"hit@{k}"] = round(_mean(hit[k]), 3)
    faith_mean = _mean(faith)
    row["faithfulness"] = round(faith_mean, 3)
    row["hallucination_rate"] = round(1 - faith_mean, 3) if not math.isnan(faith_mean) else float("nan")
    row["correctness"] = round(_mean(correct), 3)
    row["abstention_acc"] = round(_mean(abst), 3)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="evaluation/configs.yaml")
    ap.add_argument("--qa", default="evaluation/qa_dataset.jsonl")
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--out", default="evaluation/results.csv")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    base = get_settings()
    judge = get_llm(base.model_copy(update={
        "llm_provider": cfg["judge"]["provider"], "llm_model": cfg["judge"]["model"],
    }))
    ks = cfg.get("metrics_k", [1, 3, 5])

    docs = load_corpus(args.corpus)
    qa = load_qa(args.qa)
    print(f"Loaded {len(docs)} documents and {len(qa)} QA items.\n")

    rows = []
    for exp in cfg["experiments"]:
        print(f"  running: {exp['name']} ...")
        rows.append(run_experiment(exp, cfg, docs, qa, judge, ks))

    # write CSV
    fieldnames = list(rows[0].keys())
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # pretty print
    print("\n=== RESULTS ===")
    widths = {k: max(len(k), *(len(str(r[k])) for r in rows)) for k in fieldnames}
    print(" | ".join(k.ljust(widths[k]) for k in fieldnames))
    print("-+-".join("-" * widths[k] for k in fieldnames))
    for r in rows:
        print(" | ".join(str(r[k]).ljust(widths[k]) for k in fieldnames))
    print(f"\nSaved -> {args.out}")


if __name__ == "__main__":
    main()

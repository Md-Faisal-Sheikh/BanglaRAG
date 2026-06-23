# সেবা সহায়ক — BanglaRAG

A Bangla-first, source-grounded RAG assistant for a public-service domain (government
services / legal aid / health navigation), built as **both** a full-stack software
engineering project **and** the platform for a low-resource RAG **faithfulness study**.

- **Product:** ingest a Bangla corpus → ask questions → get answers in Bangla that cite
  their sources, and that *abstain* when the corpus doesn't contain the answer.
- **Research:** a curated Bangla QA test set + an evaluation harness that benchmarks
  retrieval hit-rate, faithfulness, hallucination rate, and abstention across
  **native vs. English-pivot retrieval**, **chunking strategies**, and **±reranking**.

> This is a **runnable scaffold**, not a finished product. The structure, pipeline,
> and eval harness are complete; you supply API keys (or let it download local models)
> and replace the sample corpus with your real one.

---

## What's in the box

```
banglarag/
├── app/                    # FastAPI backend
│   ├── api/                # routes: auth, chat, admin (+ deps)
│   ├── core/               # RAG core — each piece behind an interface
│   │   ├── embeddings.py   #   bge-m3 (local) | OpenAI | hash (demo)
│   │   ├── chunking.py     #   fixed | recursive | sentence_bn (Bangla-aware)
│   │   ├── lexical.py      #   BM25 sparse index (Bangla-aware tokenizer)
│   │   ├── vectorstore.py  #   Chroma (local) | memory (demo) | Qdrant (stub)
│   │   ├── reranker.py     #   cross-encoder | cohere | none
│   │   ├── llm.py          #   OpenAI | Gemini | Groq | Mock (offline)
│   │   ├── translation.py  #   for the English-pivot arm
│   │   └── rag_pipeline.py #   dense + BM25 → RRF → rerank → grounded answer → citations
│   ├── services/           # ingestion, extraction (pdf/docx/txt), auth
│   ├── db/                 # SQLAlchemy models + session
│   ├── config.py           # all knobs (pydantic-settings)
│   └── main.py
├── evaluation/             # the research core
│   ├── qa_dataset.jsonl    #   curated Bangla QA (8 answerable + 2 unanswerable)
│   ├── metrics.py          #   hit-rate / recall / faithfulness / abstention
│   ├── configs.yaml        #   the experiment matrix
│   └── run_eval.py         #   runs every config, writes results.csv
├── data/corpus/            # sample Bangla gov-service docs (replace these)
├── web/                    # React + shadcn/ui frontend source (Vite) — see web/README.md
├── frontend/               # built UI bundle (served by API / Space / Pages)
├── tests/                  # pytest unit tests
├── docs/                   # ARCHITECTURE.md, SRS_outline.md
├── ingest.py               # CLI: load corpus into the live index
├── run.py                  # start API + frontend on :8000
└── requirements.txt
```

---

## Tech stack & why

| Layer | Choice | Why (for this project) |
|---|---|---|
| API | **FastAPI + Uvicorn** | async, typed, auto OpenAPI docs; clean module boundaries for the course |
| Embeddings | **BAAI/bge-m3** | open, multilingual, strong on **Bangla**, runs locally/free; OpenAI as a swap |
| Vector store | **Chroma** (local) | zero external services to get running; Qdrant path for production |
| Reranker | **bge-reranker-v2-m3** | multilingual cross-encoder, pairs with bge-m3; the ±rerank research axis |
| LLM | **swappable** (OpenAI/Gemini/Groq/Mock) | the research needs provider independence; Mock runs offline |
| Relational DB | **SQLAlchemy + SQLite** | users, versioned corpus metadata, chat history with no setup; Postgres swap |
| Auth | **JWT + bcrypt** | real auth surface for the SWE deliverable |
| Frontend | **React + TypeScript + shadcn/ui** (Vite) | Bangla-typeset chat + corpus UI, light/dark, citation chips; built into `frontend/` |

The recurring design decision is that **every model/store sits behind an interface
with a config-keyed factory**. That's good engineering (dependency inversion,
testability) and it's exactly what lets the evaluation harness swap one axis at a time.

---

## Setup

Requires **Python 3.10+**.

```bash
cd banglarag
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then edit .env
```

In `.env`, the fastest path to a *real* run is an OpenAI key:
```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```
Embeddings + reranker (bge-m3 / bge-reranker) download automatically from Hugging Face
on first use and run locally — no key needed. Free alternatives: `LLM_PROVIDER=gemini`
(generous free tier) or `LLM_PROVIDER=groq`.

**No keys at all?** Set `LLM_PROVIDER=mock` to exercise the full pipeline offline
(answers are stubbed — useful for wiring/CI, not for quality).

## Run the app

```bash
python ingest.py --corpus data/corpus --reset     # build the live index
python run.py                                       # http://localhost:8000
```

Open the URL. **The first account you register becomes the admin.** From the "কর্পাস"
tab the admin can paste text **or upload `.txt` / `.md` / `.pdf` / `.docx` files**, and
delete documents (which also removes their chunks from the index). API docs live at
`http://localhost:8000/docs`.

Retrieval is **hybrid by default**: dense vectors and a BM25 lexical index are fused
with Reciprocal Rank Fusion, then reranked. Set `RETRIEVAL_MODE=dense` to disable the
lexical arm.

## Run the tests

```bash
pytest            # chunking + metrics unit tests
```

---

## Run the evaluation (your research)

This is the part that becomes the paper.

```bash
python -m evaluation.run_eval \
  --config evaluation/configs.yaml \
  --qa evaluation/qa_dataset.jsonl \
  --corpus data/corpus \
  --out evaluation/results.csv
```

It builds an **isolated index per configuration**, answers every QA item, and prints +
saves a table like:

```
experiment                | hit@1 | hit@3 | hit@5 | faithfulness | hallucination_rate | correctness | abstention_acc
--------------------------+-------+-------+-------+--------------+--------------------+-------------+----------------
native_recursive_norerank | ...   | ...   | ...   | ...          | ...                | ...         | ...
native_recursive_rerank   | ...   | ...   | ...   | ...          | ...                | ...         | ...
native_sentence_rerank    | ...   | ...   | ...   | ...          | ...                | ...         | ...
native_fixed_rerank       | ...   | ...   | ...   | ...          | ...                | ...         | ...
pivot_recursive_rerank    | ...   | ...   | ...   | ...          | ...                | ...         | ...
```

### Metrics
- **hit-rate@k / recall@k** — does the gold source document appear in the top-k
  retrieved? (deterministic; no LLM needed). *Matching is at the document level in this
  scaffold — see "extend" below for chunk-level.*
- **faithfulness** — is every claim in the answer supported by the retrieved context?
  (LLM-as-judge). **hallucination_rate = 1 − faithfulness.**
- **correctness** — does the answer match the gold answer? (LLM-as-judge).
- **abstention_acc** — does it answer when it should and refuse when it shouldn't?

### The experiment axes (in `configs.yaml`)
1. **Retrieval language** — `bn` native (embed Bangla directly) vs. `en` pivot
   (translate corpus + query to English, then retrieve). Isolates whether multilingual
   embeddings or an English pivot is more faithful for Bangla.
2. **Chunking** — `recursive` vs. `sentence_bn` (Bangla danda-aware) vs. `fixed`.
3. **Reranking** — on vs. off.

Change one axis at a time so each effect is attributable.

## Honest limitations (and how to extend)

- **Sample corpus is illustrative.** The two `.txt` files contain *plausible but
  unverified* figures. Replace them with a real, citable official corpus before any
  claims — and re-check fees/procedures against current sources.
- **Hit-rate is document-level.** For finer retrieval analysis, store chunk-level gold
  spans in the QA set and match on `chunk_index` (the metadata already carries it).
- **LLM-as-judge ≠ ground truth.** Validate the judge against a sample of human ratings
  and report agreement (e.g. Cohen's κ) — reviewers will expect this.
- **Translation in the pivot arm uses the LLM.** For reproducible large runs, swap in a
  dedicated MT model (NLLB) and cache translations to disk.
- **Auth is course-grade.** JWT-in-localStorage is fine for a demo; harden (httpOnly
  cookies, refresh tokens) for production.
- **Qdrant adapter is a stub.** Implement it to demonstrate the production swap.

See `docs/ARCHITECTURE.md` for the layer diagram and request flow, and
`docs/SRS_outline.md` for a head start on the SE report.

# Architecture

## Layered view

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (frontend/index.html)                                │
│  React (CDN) · Bangla-first UI · chat + citations + admin      │
└───────────────┬──────────────────────────────────────────────┘
                │ HTTP/JSON  (Bearer JWT)
┌───────────────▼──────────────────────────────────────────────┐
│  API layer (app/api/)                                          │
│  auth · chat · admin   +   deps (auth guard, cached pipeline)  │
└───────────────┬──────────────────────────────────────────────┘
                │
┌───────────────▼───────────────┐   ┌───────────────────────────┐
│  Services (app/services/)      │   │  Domain DB (SQLAlchemy)    │
│  ingestion · auth              │   │  users · documents ·       │
└───────────────┬───────────────┘   │  conversations · messages  │
                │                    └───────────────────────────┘
┌───────────────▼──────────────────────────────────────────────┐
│  RAG core (app/core/) — every piece behind an interface       │
│  embeddings │ chunking │ vectorstore │ reranker │ llm │        │
│  translation │ rag_pipeline (orchestrator)                     │
└───────────────┬──────────────────────────────────────────────┘
                │
        ┌───────▼────────┐   ┌──────────────┐   ┌──────────────┐
        │ Vector store   │   │ Embedding    │   │ LLM provider │
        │ Chroma/Qdrant  │   │ bge-m3/OpenAI│   │ OpenAI/Gemini│
        └────────────────┘   └──────────────┘   └──────────────┘
```

## Request flow (a chat turn)

1. `POST /api/chat` with `{question}` and a Bearer token.
2. `get_current_user` validates the JWT; `get_pipeline` returns the cached pipeline.
3. `RAGPipeline.retrieve`: embed the query → vector search (top_k) → optional rerank
   (rerank_k). In the English-pivot arm the query is translated to English first.
4. `RAGPipeline.answer`: build a grounded prompt (numbered context + citation + Bangla
   abstention rules) → LLM generates → parse `[n]` markers into citations.
5. The turn (question + answer + citations) is persisted; the response returns answer,
   citations, and a `grounded` flag.

## Why these interfaces

Every external dependency (embedder, vector store, reranker, LLM) sits behind an
abstract base class with a factory keyed on config. This serves two goals at once:

- **Engineering:** swap Chroma→Qdrant or OpenAI→Gemini without touching call sites
  (dependency inversion); makes components unit-testable with mocks.
- **Research:** the evaluation harness reconfigures these same seams per experiment to
  compare native vs. English-pivot retrieval, chunking strategies, and ±reranking.

## Production upgrade path

| Concern        | Scaffold default        | Production swap                          |
|----------------|-------------------------|------------------------------------------|
| Vector store   | Chroma (local file)     | Qdrant (`docker-compose.yml`, impl stub) |
| Relational DB  | SQLite                  | PostgreSQL                               |
| Embeddings     | bge-m3 (local)          | bge-m3 self-hosted / managed API         |
| LLM            | OpenAI gpt-4o-mini      | any provider; add caching + rate limits  |
| Auth           | JWT in localStorage     | httpOnly cookies, refresh tokens         |
| Serving        | uvicorn --reload        | gunicorn+uvicorn workers behind nginx    |
```

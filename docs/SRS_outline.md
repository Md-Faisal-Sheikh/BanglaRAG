# SRS Outline — সেবা সহায়ক (BanglaRAG)

A starting skeleton for your Software Requirements Specification. Fill each section
with project-specific detail; this maps to what the implemented scaffold already does.

## 1. Introduction
- 1.1 Purpose — a Bangla-first, source-grounded Q&A assistant for a public-service
  domain (government services / legal aid / health navigation).
- 1.2 Scope — answers strictly from a curated corpus, with citations; abstains when
  the answer is not in the corpus.
- 1.3 Definitions — RAG, embedding, chunking, reranking, faithfulness, hit-rate.

## 2. Overall description
- 2.1 Product perspective — three tiers: React client, FastAPI service, RAG core +
  data stores.
- 2.2 User classes — (a) citizen/end-user, (b) admin/content manager.
- 2.3 Operating environment — Python 3.10+, modern browser; optional Docker for
  Qdrant/Postgres.
- 2.4 Constraints — low-resource language; single-corpus grounding; provider-agnostic.

## 3. Functional requirements
- FR-1  User registration and login (JWT).
- FR-2  Ask a question and receive a Bangla answer with inline citations.
- FR-3  System abstains when the corpus does not contain the answer.
- FR-4  Conversation history is persisted per user.
- FR-5  Admin can add a document to the corpus (chunk → embed → index).
- FR-6  Admin can view corpus documents with version and chunk count.
- FR-7  Corpus is versioned; re-ingesting a document bumps its version.

## 4. Non-functional requirements
- NFR-1 Faithfulness — answers must be grounded; measured by the evaluation harness.
- NFR-2 Configurability — embedder/LLM/vector store swappable via config.
- NFR-3 Security — passwords hashed (bcrypt); endpoints behind auth; admin-gated.
- NFR-4 Performance — models loaded once (cached pipeline); reranking bounded by k.
- NFR-5 Portability — runs locally with zero external services (Chroma + SQLite).

## 5. Use cases (sketch)
- UC-1 Ask a question → see grounded answer + sources.
- UC-2 Ask an out-of-corpus question → see abstention notice.
- UC-3 Admin ingests a new policy document → it becomes answerable.

## 6. Evaluation / acceptance
- Retrieval hit-rate@k on the curated QA set ≥ target.
- Grounded answer rate (faithfulness) ≥ target; hallucination rate ≤ target.
- Correct abstention on unanswerable questions.

## 7. Suggested UML for the report
- Use-case diagram (citizen, admin).
- Component diagram (client / API / services / RAG core / stores) — see ARCHITECTURE.md.
- Sequence diagram for a chat turn (steps in ARCHITECTURE.md "Request flow").
- ER diagram (User, Document, Conversation, Message).
- Class diagram (the provider interfaces + implementations).

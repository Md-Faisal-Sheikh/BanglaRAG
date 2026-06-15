"""Central configuration. All values can be overridden via a .env file or env vars.

This is the single source of truth for which providers/models the system uses, so
that the same code can be re-pointed at different embedders / LLMs / vector stores
without edits — which is exactly what the research evaluation needs.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "BanglaRAG"
    api_prefix: str = "/api"
    cors_origins: str = "*"

    # --- Auth ---
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # --- Database (users, corpus metadata, conversations) ---
    database_url: str = "sqlite:///./banglarag.db"

    # --- Embeddings ---
    # provider: "sentence_transformers" (local, free) | "openai"
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "BAAI/bge-m3"          # strong multilingual, supports Bangla
    openai_embedding_model: str = "text-embedding-3-large"

    # --- Vector store ---
    vector_store: str = "chroma"                  # "chroma" (local) | "qdrant" (prod)
    chroma_dir: str = "./chroma_db"
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "banglarag"

    # --- Reranker ---
    use_reranker: bool = True
    reranker_provider: str = "cross_encoder"      # "cross_encoder" | "cohere" | "none"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    cohere_api_key: str = ""

    # --- LLM (answer generation + LLM-as-judge) ---
    llm_provider: str = "openai"                  # "openai" | "gemini" | "groq" | "mock"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # --- Retrieval defaults ---
    retrieval_lang: str = "bn"                    # "bn" (native) | "en" (English-pivot)
    top_k: int = 20                               # candidates fetched from vector store
    rerank_k: int = 5                             # kept after reranking
    chunker: str = "recursive"                    # "fixed" | "recursive" | "sentence_bn"
    chunk_size: int = 512
    chunk_overlap: int = 64


@lru_cache
def get_settings() -> Settings:
    return Settings()

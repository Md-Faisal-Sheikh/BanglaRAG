"""Shared FastAPI dependencies.

The RAG pipeline (which loads embedding + reranker models) is built once and cached,
so models aren't reloaded on every request.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.embeddings import get_embedding_provider
from app.core.llm import get_llm
from app.core.rag_pipeline import RAGConfig, RAGPipeline
from app.core.reranker import get_reranker
from app.core.vectorstore import get_vector_store
from app.db.database import get_db
from app.db.models import User
from app.services.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


@lru_cache
def get_pipeline() -> RAGPipeline:
    s = get_settings()
    return RAGPipeline(
        embedder=get_embedding_provider(s),
        store=get_vector_store(s),
        reranker=get_reranker(s),
        llm=get_llm(s),
        config=RAGConfig(
            retrieval_lang=s.retrieval_lang,
            top_k=s.top_k,
            rerank_k=s.rerank_k,
            use_reranker=s.use_reranker,
        ),
    )


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise cred_exc
    email = decode_token(token)
    if not email:
        raise cred_exc
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise cred_exc
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user

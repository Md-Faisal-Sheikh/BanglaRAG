"""Admin endpoints for managing the (versioned) corpus.

Adding a document chunks + embeds + indexes it and bumps its version if it already
exists. This is the 'content management' surface of the system.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_pipeline, require_admin
from app.config import get_settings
from app.core.rag_pipeline import RAGPipeline
from app.db.database import get_db
from app.db.models import Document, User
from app.schemas import DocumentCreate, DocumentOut
from app.services.ingestion import RawDoc, ingest_documents

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.post("/documents", response_model=DocumentOut, status_code=201)
def add_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    settings = get_settings()
    source = payload.title.replace(" ", "_").lower()
    ingest_documents(
        [RawDoc(source=source, title=payload.title, text=payload.text, lang=payload.lang)],
        embedder=pipeline.embedder,
        store=pipeline.store,
        settings=settings,
        db=db,
    )
    return db.query(Document).filter(Document.source == source).first()

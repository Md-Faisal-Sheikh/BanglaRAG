"""Admin endpoints for managing the (versioned) corpus.

Adding a document — pasted as text or uploaded as a file (.txt/.md/.pdf/.docx) —
chunks + embeds + indexes it and bumps its version if it already exists. Deleting a
document removes both its metadata row and its chunks from the vector store. This is
the 'content management' surface of the system.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_pipeline, require_admin
from app.config import get_settings
from app.core.rag_pipeline import RAGPipeline
from app.db.database import get_db
from app.db.models import Document, User
from app.schemas import DocumentCreate, DocumentOut
from app.services.extraction import ExtractionError, UnsupportedFileType, extract_text
from app.services.ingestion import RawDoc, ingest_documents

router = APIRouter(prefix="/admin", tags=["admin"])


def _slugify(title: str) -> str:
    """Stable source id from a title (also the doc_id used for chunk grouping)."""
    return title.strip().replace(" ", "_").lower()


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
    return _ingest_one(payload.title, payload.text, payload.lang, db, pipeline)


@router.post("/documents/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    lang: str = Form("bn"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    settings = get_settings()
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (limit {settings.max_upload_mb} MB).",
        )

    try:
        text = extract_text(file.filename or "", raw)
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the file (it may be scanned images).",
        )

    base = title or os.path.splitext(os.path.basename(file.filename or "document"))[0]
    return _ingest_one(base, text, lang, db, pipeline)


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    pipeline.store.delete_by_doc(doc.source)
    db.delete(doc)
    db.commit()
    return Response(status_code=204)


def _ingest_one(
    title: str, text: str, lang: str, db: Session, pipeline: RAGPipeline
) -> Document:
    title = (title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="A document title is required.")
    source = _slugify(title)
    settings = get_settings()
    ingest_documents(
        [RawDoc(source=source, title=title, text=text, lang=lang)],
        embedder=pipeline.embedder,
        store=pipeline.store,
        settings=settings,
        db=db,
    )
    return db.query(Document).filter(Document.source == source).first()

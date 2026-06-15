"""Chat endpoint: ask a question, get a grounded Bangla answer + citations.

Conversation history is persisted so the UI can show past turns.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_pipeline
from app.core.rag_pipeline import RAGPipeline
from app.db.database import get_db
from app.db.models import Conversation, Message, User
from app.schemas import ChatRequest, ChatResponse, Citation

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    # resolve / create conversation
    conv = None
    if payload.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id,
            Conversation.user_id == user.id,
        ).first()
    if conv is None:
        conv = Conversation(user_id=user.id)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    db.add(Message(conversation_id=conv.id, role="user", content=payload.question))
    db.commit()

    result = pipeline.answer(payload.question)
    citations = [Citation(**c) for c in result.citations]

    db.add(Message(
        conversation_id=conv.id, role="assistant", content=result.answer,
        citations_json=json.dumps(result.citations, ensure_ascii=False),
    ))
    db.commit()

    return ChatResponse(
        answer=result.answer,
        citations=citations,
        conversation_id=conv.id,
        grounded=result.grounded,
    )

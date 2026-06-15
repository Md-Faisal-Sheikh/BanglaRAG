"""SQLAlchemy engine/session. Relational store for users, corpus metadata, chats.

Vectors themselves live in the vector store (Chroma/Qdrant); this DB tracks the
*metadata* (which documents exist, their version, how many chunks) plus auth and
conversation history.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db import models  # noqa: F401  (register models on Base)
    Base.metadata.create_all(bind=engine)

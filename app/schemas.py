"""Pydantic schemas for the API layer (request/response contracts)."""
from datetime import datetime
from pydantic import BaseModel, EmailStr


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Chat ---
class Citation(BaseModel):
    marker: int                 # the [n] used in the answer
    source: str                 # source document title / filename
    snippet: str                # the chunk text the answer drew on
    score: float | None = None  # retrieval / rerank score


class ChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    conversation_id: int | None = None
    grounded: bool              # False => model abstained ("not found in sources")


# --- Admin / corpus ---
class DocumentOut(BaseModel):
    id: int
    source: str
    title: str
    lang: str
    version: int
    n_chunks: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    title: str
    lang: str = "bn"
    text: str

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from db.models import Chunk, Document
from ingestion.embeddings import embed_texts

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=4)
    top_k: int = Field(default=5, ge=1, le=20)


class AskContext(BaseModel):
    url: str
    title: str | None = None
    breadcrumbs: list[str] = []
    preview: str


class AskResponse(BaseModel):
    question: str
    answer: str
    contexts: list[AskContext]


@router.post("", response_model=AskResponse)
def ask_endpoint(payload: AskRequest, session: Session = Depends(get_db_session)) -> AskResponse:
    query_embedding = embed_texts([payload.question])[0]
    stmt = (
        select(Chunk, Document)
        .join(Document, Document.id == Chunk.document_id)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(payload.top_k)
    )

    contexts: list[AskContext] = []
    for chunk, document in session.execute(stmt):
        metadata = chunk.metadata_json or {}
        preview = _build_preview(chunk.chunk_text)
        contexts.append(
            AskContext(
                url=document.url,
                title=document.title or metadata.get("title"),
                breadcrumbs=metadata.get("breadcrumbs", []),
                preview=preview,
            )
        )

    answer = _assemble_answer(payload.question, contexts)
    return AskResponse(question=payload.question, answer=answer, contexts=contexts)


def _build_preview(text: str, limit: int = 280) -> str:
    flattened = " ".join(text.split())
    return flattened[:limit] + ("..." if len(flattened) > limit else "")


def _assemble_answer(question: str, contexts: list[AskContext]) -> str:
    if not contexts:
        return f"Não encontrei contexto relevante para “{question}”."
    lines = [f"Principais referências para “{question}”:"]  # context summary
    for idx, ctx in enumerate(contexts, start=1):
        title = ctx.title or "Documento sem título"
        lines.append(f"{idx}. {title} ({ctx.url})")
    return "\n".join(lines)

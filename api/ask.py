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


class AskResponse(BaseModel):
    question: str
    answer: str
    contexts: list[dict]


@router.post("", response_model=AskResponse)
def ask_endpoint(payload: AskRequest, session: Session = Depends(get_db_session)) -> AskResponse:
    query_embedding = embed_texts([payload.question])[0]
    stmt = (
        select(Chunk, Document)
        .join(Document, Document.id == Chunk.document_id)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(payload.top_k)
    )

    contexts = []
    for chunk, document in session.execute(stmt):
        contexts.append(
            {
                "url": document.url,
                "title": document.title,
                "metadata": chunk.metadata,
                "chunk": chunk.chunk_text,
            }
        )

    answer = _assemble_answer(payload.question, contexts)
    return AskResponse(question=payload.question, answer=answer, contexts=contexts)


def _assemble_answer(question: str, contexts: list[dict]) -> str:
    """
    Placeholder simples que cola os chunks relevantes.
    Pode ser substituído por uma chamada real ao LLM.
    """
    joined = "\n\n".join(f"- {ctx['chunk']}" for ctx in contexts)
    return f"Pergunta: {question}\n\nContexto:\n{joined}"

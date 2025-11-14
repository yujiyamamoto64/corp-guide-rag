from __future__ import annotations

from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from db.models import Chunk, Document


def get_document_by_url(session: Session, url: str) -> Document | None:
    return session.scalars(select(Document).where(Document.url == url)).first()


def save_document(
    session: Session, *, domain: str, url: str, title: str, content: str, content_hash: str
) -> Document:
    document = get_document_by_url(session, url)
    if not document:
        document = Document(domain=domain, url=url)
        session.add(document)
    document.title = title
    document.content = content
    document.content_hash = content_hash
    return document


def replace_chunks(session: Session, document: Document, chunks_data: Iterable[dict]) -> None:
    session.query(Chunk).filter(Chunk.document_id == document.id).delete()
    session.flush()
    for chunk in chunks_data:
        session.add(
            Chunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                chunk_text=chunk["chunk_text"],
                embedding=chunk["embedding"],
                metadata_json=chunk["metadata"],
            )
        )


def delete_domain(session: Session, domain: str) -> int:
    stmt = delete(Document).where(Document.domain == domain)
    result = session.execute(stmt)
    return result.rowcount or 0

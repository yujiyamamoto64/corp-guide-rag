from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy.orm import Session

from db.queries import get_document_by_url, replace_chunks, save_document
from ingestion.chunker import Chunk, chunk_page
from ingestion.documents import build_payload
from ingestion.embeddings import embed_texts
from crawler.extract import PageContent


@dataclass
class IngestionResult:
    url: str
    created: bool
    updated: bool
    chunks: int


def ingest_page(session: Session, page: PageContent) -> IngestionResult:
    payload = build_payload(page)
    existing = get_document_by_url(session, payload.url)
    if existing and existing.content_hash == payload.content_hash:
        return IngestionResult(url=payload.url, created=False, updated=False, chunks=len(existing.chunks))

    chunks = chunk_page(page)
    embeddings = embed_texts(chunk.text for chunk in chunks)
    chunk_entries = _build_chunk_entries(chunks, embeddings)
    document = save_document(
        session,
        domain=payload.domain,
        url=payload.url,
        title=payload.title,
        content=payload.content,
        content_hash=payload.content_hash,
    )
    replace_chunks(session, document, chunk_entries)
    session.commit()

    return IngestionResult(
        url=payload.url,
        created=existing is None,
        updated=existing is not None,
        chunks=len(chunk_entries),
    )


def _build_chunk_entries(chunks: Sequence[Chunk], embeddings: Sequence[list[float]]) -> list[dict]:
    payload = []
    for chunk, embedding in zip(chunks, embeddings):
        payload.append(
            {
                "chunk_index": chunk.index,
                "chunk_text": chunk.text,
                "embedding": embedding,
                "metadata": chunk.metadata,
            }
        )
    return payload

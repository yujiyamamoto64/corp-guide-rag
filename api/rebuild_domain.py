from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from crawler.crawl import Crawler, CrawlerConfig
from db.queries import delete_domain
from ingestion.updater import ingest_page

router = APIRouter(prefix="/rebuild-domain", tags=["rebuild"])


class RebuildRequest(BaseModel):
    base_url: HttpUrl


class RebuildResponse(BaseModel):
    domain: str
    pages: int
    chunks: int
    deleted_documents: int
    message: str


@router.post("", response_model=RebuildResponse)
def rebuild_domain_endpoint(
    payload: RebuildRequest, session: Session = Depends(get_db_session)
) -> RebuildResponse:
    base_url = str(payload.base_url)
    domain = payload.base_url.host
    deleted = delete_domain(session, domain)
    session.commit()

    crawler = Crawler(CrawlerConfig(max_pages=2000))
    pages_processed = 0
    total_chunks = 0

    for page in crawler.crawl(base_url):
        result = ingest_page(session, page)
        pages_processed += 1
        total_chunks += result.chunks

    return RebuildResponse(
        domain=domain,
        pages=pages_processed,
        chunks=total_chunks,
        deleted_documents=deleted,
        message=f"Reconstrução concluída ({pages_processed} páginas, {total_chunks} chunks)",
    )

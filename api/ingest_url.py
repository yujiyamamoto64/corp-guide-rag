from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from crawler.crawl import Crawler, CrawlerConfig
from ingestion.updater import ingest_page

router = APIRouter(prefix="/ingest-url", tags=["ingest"])


class IngestRequest(BaseModel):
    url: HttpUrl


class IngestResponse(BaseModel):
    url: str
    created: bool
    updated: bool
    chunks: int
    message: str


@router.post("", response_model=IngestResponse)
def ingest_url_endpoint(
    payload: IngestRequest, session: Session = Depends(get_db_session)
) -> IngestResponse:
    crawler = Crawler(CrawlerConfig(max_pages=1))
    target_url = str(payload.url)
    try:
        page = next(iter(crawler.crawl(target_url)))
    except StopIteration:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")

    result = ingest_page(session, page)
    message = "Sem mudanças" if not result.created and not result.updated else "Documento processado"
    return IngestResponse(
        url=result.url,
        created=result.created,
        updated=result.updated,
        chunks=result.chunks,
        message=message,
    )

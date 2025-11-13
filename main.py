from __future__ import annotations

from fastapi import FastAPI
from dotenv import load_dotenv

from api.ask import router as ask_router
from api.ingest_url import router as ingest_router
from api.rebuild_domain import router as rebuild_router

load_dotenv()

app = FastAPI(title="Corp Guide RAG")

app.include_router(ingest_router)
app.include_router(rebuild_router)
app.include_router(ask_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

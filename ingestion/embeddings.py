from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterable, List

import tiktoken
from openai import OpenAI

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def embed_texts(texts: Iterable[str]) -> List[list[float]]:
    """Gera embeddings preservando a ordem dos textos."""
    client = get_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=list(texts))
    return [item.embedding for item in response.data]


@lru_cache
def _encoding():
    try:
        return tiktoken.encoding_for_model(EMBEDDING_MODEL)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Conta tokens para chunking. Fallback simples caso tiktoken falhe."""
    try:
        return len(_encoding().encode(text))
    except Exception:
        return max(1, len(text.split()))

from __future__ import annotations

import hashlib
import logging
from collections import deque
from dataclasses import dataclass
from typing import Iterable

import requests
from requests import Response

from crawler.extract import PageContent, parse_page
from crawler.normalize_urls import canonicalize, is_internal

logger = logging.getLogger(__name__)


@dataclass
class CrawlerConfig:
    max_pages: int = 200
    timeout: int = 20
    user_agent: str = "CorpGuideCrawler/0.1"
    same_domain_only: bool = True


class Crawler:
    """Crawler simples baseado em requests, com fila BFS e deduplicação."""

    def __init__(self, config: CrawlerConfig | None = None) -> None:
        self.config = config or CrawlerConfig()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})

    def crawl(self, start_url: str) -> Iterable[PageContent]:
        base_url = canonicalize(start_url)
        base_domain = canonicalize(start_url).split("://", 1)[1].split("/", 1)[0]
        visited: set[str] = set()
        queue = deque([base_url])

        while queue and len(visited) < self.config.max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            if self.config.same_domain_only and not is_internal(url, base_domain):
                continue
            try:
                response = self._fetch(url)
            except requests.RequestException as exc:
                logger.warning("Falha ao baixar %s: %s", url, exc)
                continue

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                logger.info("Ignorando %s (content-type: %s)", url, content_type)
                visited.add(url)
                continue

            visited.add(url)
            page = parse_page(url, response.text)
            yield page

            for link in page.links:
                if link not in visited and link not in queue:
                    if not self.config.same_domain_only or is_internal(link, base_domain):
                        queue.append(link)

    def _fetch(self, url: str) -> Response:
        response = self.session.get(url, timeout=self.config.timeout)
        response.raise_for_status()
        return response


def content_hash(content: str) -> str:
    """Hash sha256 usado para detecção de mudanças."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

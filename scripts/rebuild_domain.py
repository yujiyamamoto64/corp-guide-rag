from __future__ import annotations

import argparse

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawler.crawl import Crawler, CrawlerConfig
from db.connection import get_session
from db.queries import delete_domain
from ingestion.updater import ingest_page


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild all documents for a domain.")
    parser.add_argument("base_url", help="URL base para iniciar o crawl (ex.: http://site/)")
    parser.add_argument("--max-pages", type=int, default=2000)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/") + "/"
    domain = base_url.split("://", 1)[1].split("/", 1)[0]

    session = get_session()
    removed = delete_domain(session, domain)
    session.commit()
    print(f"Removed {removed} documentos antigos de {domain}")

    crawler = Crawler(CrawlerConfig(max_pages=args.max_pages))
    pages = chunks = 0
    for page in crawler.crawl(base_url):
        result = ingest_page(session, page)
        pages += 1
        chunks += result.chunks
        status = "novo" if result.created else "atualizado"
        print(f"{status:10} | {page.url} -> {result.chunks} chunks")
    print(f"Resumo: {pages} páginas, {chunks} chunks gerados.")


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass

from crawler.clean_html import clean_text, extract_main
from crawler.crawl import content_hash
from crawler.extract import PageContent


@dataclass
class DocumentPayload:
    url: str
    domain: str
    title: str
    content: str
    content_hash: str


def build_payload(page: PageContent) -> DocumentPayload:
    """Transforma PageContent em documento limpo pronto para salvar."""
    main = extract_main(page.raw_html)
    text_content = clean_text(main)
    return DocumentPayload(
        url=page.url,
        domain=page.url.split("://", 1)[-1].split("/", 1)[0],
        title=page.title,
        content=text_content,
        content_hash=content_hash(text_content),
    )

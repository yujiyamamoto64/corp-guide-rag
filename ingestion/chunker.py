from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as html_to_md
from ftfy import fix_text

from crawler.clean_html import extract_main
from ingestion.embeddings import count_tokens
from crawler.extract import PageContent

HEADING_TAGS = ("h1", "h2", "h3", "h4")


@dataclass
class Chunk:
    index: int
    text: str
    metadata: dict


def chunk_page(page: PageContent, max_tokens: int = 1000) -> List[Chunk]:
    """
    Cria chunks baseados em headings preservando contexto hierárquico.
    """
    main = extract_main(page.raw_html)
    sections = list(_split_sections(main, page))

    chunks: List[Chunk] = []
    for idx, section in enumerate(sections):
        text = fix_text(section["text"].strip())
        if not text:
            continue

        chunk_tokens = count_tokens(text)
        if chunk_tokens <= max_tokens:
            chunks.append(
                Chunk(
                    index=len(chunks),
                    text=text,
                    metadata=_base_metadata(section, idx),
                )
            )
        else:
            chunks.extend(
                _split_large_chunk(section, max_tokens=max_tokens, base_index=len(chunks))
            )
    return chunks


def _base_metadata(section: dict, chunk_index: int) -> dict:
    return {
        "title": fix_text(section["title"]),
        "depth": section["depth"],
        "breadcrumbs": section["breadcrumbs"],
        "chunk_index": chunk_index,
        "url": section["url"],
        "domain": section["domain"],
    }


def _split_sections(root: Tag, page: PageContent) -> Iterable[dict]:
    hierarchy: list[str] = []
    current = {
        "title": page.title,
        "depth": 1,
        "parts": [],
        "breadcrumbs": [],
        "url": page.url,
        "domain": page.url.split("://", 1)[-1].split("/", 1)[0],
    }

    for node in root.children:
        if isinstance(node, Tag) and node.name in HEADING_TAGS:
            if current["parts"]:
                yield {
                    "title": current["title"],
                    "text": "\n\n".join(current["parts"]),
                    "depth": current["depth"],
                    "breadcrumbs": list(current["breadcrumbs"]),
                    "url": current["url"],
                    "domain": current["domain"],
                }
                current["parts"] = []
            text = fix_text(node.get_text(strip=True))
            depth = int(node.name[1])
            hierarchy = hierarchy[: depth - 1]
            hierarchy.append(text)
            current.update(
                {
                    "title": text or page.title,
                    "depth": depth,
                    "breadcrumbs": list(hierarchy),
                    "url": page.url,
                    "domain": page.url.split("://", 1)[-1].split("/", 1)[0],
                }
            )
        else:
            markdown = html_to_md(str(node), strip=[])
            current["parts"].append(fix_text(markdown))

    if current["parts"]:
        yield {
            "title": current["title"],
            "text": "\n\n".join(current["parts"]),
            "depth": current["depth"],
            "breadcrumbs": list(current["breadcrumbs"]),
            "url": current["url"],
            "domain": current["domain"],
        }


def _split_large_chunk(section: dict, max_tokens: int, base_index: int) -> List[Chunk]:
    text = section["text"]
    sentences = text.split("\n")
    buffer: list[str] = []
    chunks: List[Chunk] = []

    def flush():
        if not buffer:
            return
        chunk_text = "\n".join(buffer).strip()
        if not chunk_text:
            buffer.clear()
            return
        chunks.append(
            Chunk(
                index=base_index + len(chunks),
                text=chunk_text,
                metadata=_base_metadata(section, base_index + len(chunks)),
            )
        )
        buffer.clear()

    for sentence in sentences:
        candidate = buffer + [sentence]
        if count_tokens("\n".join(candidate)) > max_tokens:
            flush()
        buffer.append(sentence)

    flush()
    return chunks

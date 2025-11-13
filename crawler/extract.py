from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as html_to_md

from crawler.clean_html import clean_text, extract_main
from crawler.normalize_urls import resolve


@dataclass
class HeadingNode:
    tag: str
    text: str
    depth: int


@dataclass
class PageContent:
    url: str
    title: str
    raw_html: str
    markdown: str
    headings: list[HeadingNode] = field(default_factory=list)
    nav_hierarchy: list[dict] = field(default_factory=list)
    breadcrumbs: list[str] = field(default_factory=list)
    links: set[str] = field(default_factory=set)


def parse_page(url: str, html: str) -> PageContent:
    """Extrai todos os dados estruturados necessários para a ingestão."""
    soup = BeautifulSoup(html, "html.parser")
    main = extract_main(html)

    title = (soup.title.string.strip() if soup.title else "") or _first_heading(main)
    headings = list(_extract_headings(main))
    nav_hierarchy = list(_extract_nav_tree(soup, base_url=url))
    breadcrumbs = _extract_breadcrumbs(soup)
    links = {
        link
        for href in _extract_links(main)
        if (link := resolve(url, href)) is not None
    }

    markdown = html_to_md(str(main), strip=["style", "script"])
    return PageContent(
        url=url,
        title=title,
        raw_html=html,
        markdown=markdown,
        headings=headings,
        nav_hierarchy=nav_hierarchy,
        breadcrumbs=breadcrumbs,
        links=links,
    )


def _extract_links(root: Tag) -> Iterable[str]:
    for a in root.find_all("a", href=True):
        yield a["href"]


def _extract_headings(root: Tag) -> Iterable[HeadingNode]:
    for tag in root.find_all(["h1", "h2", "h3", "h4"]):
        name = tag.name or "h2"
        yield HeadingNode(tag=name, text=clean_text(tag), depth=int(name[1]))


def _extract_nav_tree(soup: BeautifulSoup, base_url: str) -> Iterable[dict]:
    nav = soup.find("nav")
    if not nav:
        return []

    queue = deque([(nav, 0, [])])
    while queue:
        node, depth, parents = queue.popleft()
        for li in node.find_all("li", recursive=False):
            anchor = li.find("a", href=True)
            text = clean_text(anchor) if anchor else clean_text(li)
            href = anchor["href"] if anchor else None
            resolved = resolve(base_url, href) if href else None
            current = parents + [text]
            yield {
                "title": text,
                "url": resolved,
                "breadcrumbs": current,
                "depth": depth,
            }
            for child_ul in li.find_all("ul", recursive=False):
                queue.append((child_ul, depth + 1, current))


def _extract_breadcrumbs(soup: BeautifulSoup) -> list[str]:
    crumbs = soup.select(".breadcrumb li, nav.breadcrumb li, .breadcrumbs li")
    if not crumbs:
        return []
    return [clean_text(li) for li in crumbs if clean_text(li)]


def _first_heading(root: Tag) -> str:
    for tag in root.find_all(["h1", "h2", "h3"]):
        text = clean_text(tag)
        if text:
            return text
    return ""

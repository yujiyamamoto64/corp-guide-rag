from __future__ import annotations

from bs4 import BeautifulSoup, Tag

NOISE_SELECTORS = [
    "header",
    "footer",
    "nav",
    "aside",
    "script",
    "style",
    "[role=banner]",
    "[role=contentinfo]",
    ".sidebar",
    ".menu",
    ".breadcrumbs",  # breadcrumbs tratados separadamente
]


def extract_main(html: str) -> BeautifulSoup:
    """
    Remove elementos de navegação/ruído e devolve apenas <main> ou <article>.
    """
    soup = BeautifulSoup(html, "html.parser")

    for selector in NOISE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()

    main = soup.find("main") or soup.find("article")
    return main or soup


def clean_text(node: Tag) -> str:
    """Retorna texto limpo preservando quebras mínimas."""
    for code in node.find_all(["code", "pre"]):
        code.replace_with(code.get_text("\n"))

    text = node.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)

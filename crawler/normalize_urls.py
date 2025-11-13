from __future__ import annotations

from urllib.parse import urljoin, urlparse, urlunparse


def canonicalize(url: str) -> str:
    """Normaliza esquemas, remove fragmentos e barras duplicadas."""
    parsed = urlparse(url)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    normalized = parsed._replace(
        scheme=scheme,
        netloc=netloc,
        path=_collapse_slashes(path),
        params="",
        query=parsed.query,
        fragment="",
    )
    return urlunparse(normalized)


def resolve(base_url: str, href: str | None) -> str | None:
    """Resolve links relativos retornando URL canônica."""
    if not href:
        return None
    return canonicalize(urljoin(base_url, href))


def is_internal(target_url: str, base_domain: str) -> bool:
    """Confere se o link pertence ao mesmo domínio (subdomínios incluídos)."""
    parsed = urlparse(target_url)
    domain = parsed.netloc.lower()
    base_domain = base_domain.lower()
    return domain == base_domain or domain.endswith(f".{base_domain}")


def _collapse_slashes(path: str) -> str:
    while "//" in path:
        path = path.replace("//", "/")
    if not path.startswith("/"):
        path = f"/{path}"
    return path

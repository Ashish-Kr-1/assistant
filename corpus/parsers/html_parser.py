"""
corpus/parsers/html_parser.py — HTML statute page → structured text chunks.

Handles:
  - Fetching HTML from India Code, IP India, NBA, AYUSH pages
  - Stripping nav/header/footer boilerplate
  - Detecting section/article headings from <h2>/<h3>/<strong> tags
  - Splitting into overlapping chunks with section metadata
"""

import re
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

_CHUNK_SIZE = 1800
_CHUNK_OVERLAP = 250

# Tags that carry meaningful section headings
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "strong", "b"}

# Section identifier pattern (same as pdf_parser)
_SECTION_RE = re.compile(
    r"^(?:section|sec\.|art(?:icle)?\.?|chapter|rule|schedule|part)\s+[\dIVXA-Za-z().\-]+",
    re.IGNORECASE,
)

# Boilerplate selectors to strip before parsing
_STRIP_SELECTORS = [
    "nav", "header", "footer", "script", "style", "noscript",
    ".navbar", ".breadcrumb", ".sidebar", ".footer", "#menu",
    ".search-box", ".site-header", ".site-footer",
]


@dataclass
class TextChunk:
    text: str
    section_id: str = ""
    url: str = ""
    char_offset: int = 0
    metadata: dict = field(default_factory=dict)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")[:60]


def _split_into_chunks(text: str, section_id: str, url: str) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunk_text = text[start:end]
        if chunk_text.strip():
            chunks.append(TextChunk(
                text=chunk_text.strip(),
                section_id=section_id,
                url=url,
                char_offset=start,
            ))
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


def parse_html(html: str, url: str = "", source_name: str = "") -> list[TextChunk]:
    """
    Parse statute HTML into TextChunks. Strips boilerplate, detects section
    headings, and splits text into overlapping chunks.
    """
    soup = BeautifulSoup(html, "lxml")

    # Strip boilerplate
    for selector in _STRIP_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    # Walk all elements in document order
    all_chunks: list[TextChunk] = []
    current_section = "preamble"
    buffer: list[str] = []

    for el in soup.find_all(True):
        tag = el.name.lower() if el.name else ""

        # Detect heading → flush buffer → new section
        if tag in _HEADING_TAGS:
            text = el.get_text(" ", strip=True)
            if _SECTION_RE.match(text):
                if buffer:
                    block = " ".join(buffer)
                    all_chunks.extend(_split_into_chunks(block, current_section, url))
                    buffer = []
                current_section = _slugify(text)
                continue

        # Paragraph / list-item / div text
        if tag in {"p", "li", "td", "div", "span"}:
            text = el.get_text(" ", strip=True)
            if text and len(text) > 20:   # skip trivial strings
                buffer.append(text)

    # Flush remaining buffer
    if buffer:
        block = " ".join(buffer)
        all_chunks.extend(_split_into_chunks(block, current_section, url))

    # Deduplicate: remove chunks whose text is a subset of an adjacent chunk
    seen: set[str] = set()
    deduped: list[TextChunk] = []
    for chunk in all_chunks:
        key = chunk.text[:120]   # fingerprint by first 120 chars
        if key not in seen:
            seen.add(key)
            chunk.metadata["source_name"] = source_name
            chunk.metadata["parser"] = "html"
            chunk.metadata["url"] = url
            deduped.append(chunk)

    return deduped


def fetch_and_parse_html(url: str, source_name: str = "", timeout: int = 30) -> list[TextChunk]:
    """Fetch an HTML page and parse into TextChunks."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; CharakIP-CorpusBot/1.0; "
            "+https://github.com/charak-ip) — legal corpus indexer"
        )
    }
    resp = httpx.get(url, timeout=timeout, follow_redirects=True, headers=headers)
    resp.raise_for_status()
    return parse_html(resp.text, url=url, source_name=source_name)

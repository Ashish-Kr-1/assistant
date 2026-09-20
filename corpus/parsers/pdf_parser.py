"""
corpus/parsers/pdf_parser.py — PDF → structured text chunks with section detection.

Handles:
  - Extracting raw text from PDF files using pypdf
  - Detecting section/chapter headings (e.g. "Section 3", "Chapter IV-A", "Article 27")
  - Splitting into semantically coherent chunks (target: 512 tokens, 64-token overlap)
  - Attaching section metadata to each chunk for retrieval filtering
"""

import io
import re
from dataclasses import dataclass, field

import httpx
from pypdf import PdfReader

# ── Section heading patterns ────────────────────────────────────────────────────
# Matches: "Section 3", "SECTION 3.", "Art. 27", "Article 27.3(b)", "Chapter IV-A"
_SECTION_RE = re.compile(
    r"^(?:section|sec\.|art(?:icle)?\.?|chapter|rule|schedule|part)\s+[\dIVXA-Za-z().\-]+",
    re.IGNORECASE | re.MULTILINE,
)

# Target chunk size in characters (≈ 512 tokens at ~3.5 chars/token)
_CHUNK_SIZE = 1800
_CHUNK_OVERLAP = 250


@dataclass
class TextChunk:
    text: str
    section_id: str = ""          # e.g. "section_3p", "article_27_3b"
    page_number: int = 0
    char_offset: int = 0
    metadata: dict = field(default_factory=dict)


def _slugify_section(heading: str) -> str:
    """Convert a heading like 'Section 3(p)' → 'section_3p'."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", heading.lower()).strip("_")
    return slug[:60]


def _split_into_chunks(text: str, current_section: str, page: int) -> list[TextChunk]:
    """Split a block of text into overlapping chunks of _CHUNK_SIZE chars."""
    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunk_text = text[start:end]
        if chunk_text.strip():
            chunks.append(TextChunk(
                text=chunk_text.strip(),
                section_id=current_section,
                page_number=page,
                char_offset=start,
            ))
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


def parse_pdf_bytes(pdf_bytes: bytes, source_name: str = "") -> list[TextChunk]:
    """
    Parse a PDF from raw bytes. Returns a list of TextChunk objects, each tagged
    with the section/article heading it belongs to.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    all_chunks: list[TextChunk] = []
    current_section = "preamble"

    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        lines = raw_text.split("\n")
        buffer = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Detect section headings and flush the current buffer
            if _SECTION_RE.match(stripped):
                # Flush accumulated buffer as chunks under previous section
                if buffer:
                    block = " ".join(buffer)
                    all_chunks.extend(_split_into_chunks(block, current_section, page_num))
                    buffer = []
                current_section = _slugify_section(stripped)

            buffer.append(stripped)

        # Flush remaining buffer
        if buffer:
            block = " ".join(buffer)
            all_chunks.extend(_split_into_chunks(block, current_section, page_num))

    # Attach source metadata to every chunk
    for chunk in all_chunks:
        chunk.metadata["source_name"] = source_name
        chunk.metadata["parser"] = "pdf"

    return all_chunks


def fetch_and_parse_pdf(url: str, source_name: str = "", timeout: int = 30) -> list[TextChunk]:
    """Download a PDF from a URL and parse it into TextChunks."""
    resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return parse_pdf_bytes(resp.content, source_name=source_name)

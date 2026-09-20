"""
corpus/store.py — ChromaDB vector store wrapper for the Charaka IP legal corpus.

Provides:
  - upsert_chunks(): persist TextChunks with full metadata
  - similarity_search(): dense vector retrieval with metadata filters
  - get_collection(): access the raw Chroma collection for BM25 index building

The store lives at CHROMA_PERSIST_DIR (default: ./chroma_db).
Each chunk is stored with metadata fields that can be filtered at query time:
  source_name, jurisdiction, ip_types (comma-separated), section_id, source_url,
  fetched_at, version_hash.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

import chromadb
from chromadb.config import Settings

from corpus.embeddings import embed_query, embed_texts
from corpus.parsers.html_parser import TextChunk as HtmlChunk
from corpus.parsers.pdf_parser import TextChunk as PdfChunk

# Union type for TextChunk from either parser
TextChunk = HtmlChunk | PdfChunk

_COLLECTION_NAME = "charak_ip_corpus"
_DEFAULT_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")


def _get_client(persist_dir: str | None = None) -> chromadb.PersistentClient:
    path = persist_dir or os.getenv("CHROMA_PERSIST_DIR", _DEFAULT_PERSIST_DIR)
    return chromadb.PersistentClient(
        path=path,
        settings=Settings(anonymized_telemetry=False),
    )


def _get_collection(client: chromadb.PersistentClient):
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _chunk_id(chunk: TextChunk, source_name: str) -> str:
    """Stable document ID: sha256 of source_name + section_id + text prefix."""
    key = f"{source_name}::{chunk.section_id}::{chunk.text[:100]}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


def _version_hash(chunk: TextChunk) -> str:
    return hashlib.sha256(chunk.text.encode()).hexdigest()[:16]


def upsert_chunks(
    chunks: list[TextChunk],
    source_name: str,
    source_url: str,
    jurisdiction: str,           # "IN" or "INTL"
    ip_types: list[str],         # ["patent", "ayush", ...]
    persist_dir: str | None = None,
) -> int:
    """
    Embed and upsert a list of TextChunks into the vector store.
    Returns the number of new/updated chunks written.
    """
    if not chunks:
        return 0

    client = _get_client(persist_dir)
    collection = _get_collection(client)

    texts = [c.text for c in chunks]
    ids = [_chunk_id(c, source_name) for c in chunks]
    embeddings = embed_texts(texts)
    fetched_at = datetime.now(timezone.utc).isoformat()

    metadatas: list[dict[str, Any]] = []
    for chunk in chunks:
        meta: dict[str, Any] = {
            "source_name": source_name,
            "source_url": source_url,
            "jurisdiction": jurisdiction,
            "ip_types": ",".join(ip_types),       # Chroma only supports scalar metadata
            "section_id": chunk.section_id or "",
            "fetched_at": fetched_at,
            "version_hash": _version_hash(chunk),
        }
        meta.update(chunk.metadata)
        # Chroma metadata values must be str/int/float/bool — sanitize
        metadatas.append({k: str(v) for k, v in meta.items()})

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    return len(chunks)


def similarity_search(
    query: str,
    n_results: int = 8,
    jurisdiction: str | None = None,   # "IN", "INTL", or None (both)
    ip_type: str | None = None,        # "patent", "trademark", etc. or None
    persist_dir: str | None = None,
) -> list[dict]:
    """
    Retrieve the top-n most semantically similar chunks for a query.

    Optional filters:
      - jurisdiction: restrict to "IN" or "INTL" sources
      - ip_type: restrict to chunks whose ip_types contains this value

    Returns a list of dicts:
      {text, source_name, source_url, section_id, jurisdiction, ip_types, distance}
    """
    client = _get_client(persist_dir)
    collection = _get_collection(client)

    if collection.count() == 0:
        return []

    query_vec = embed_query(query)

    # Build Chroma where-clause
    where: dict | None = None
    conditions = []
    if jurisdiction:
        conditions.append({"jurisdiction": {"$eq": jurisdiction}})
    if ip_type:
        conditions.append({"ip_types": {"$contains": ip_type}})

    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}

    kwargs: dict[str, Any] = {
        "query_embeddings": [query_vec],
        "n_results": min(n_results, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for text, meta, dist in zip(docs, metas, distances):
        output.append({
            "text": text,
            "source_name": meta.get("source_name", ""),
            "source_url": meta.get("source_url", ""),
            "section_id": meta.get("section_id", ""),
            "jurisdiction": meta.get("jurisdiction", ""),
            "ip_types": meta.get("ip_types", ""),
            "distance": dist,
        })

    return output


def corpus_count(persist_dir: str | None = None) -> int:
    """Return the total number of chunks currently in the vector store."""
    client = _get_client(persist_dir)
    collection = _get_collection(client)
    return collection.count()

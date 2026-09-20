"""
corpus/embeddings.py — Embedding wrapper for the Charaka IP corpus.

Uses `intfloat/multilingual-e5-large` — a strong multilingual model that handles:
  - English statutory text
  - Hindi (Devanagari) legal text
  - Mixed Hinglish
  - All 22 scheduled Indian languages (for Phase 5 Bhashini compatibility)

The model runs locally via sentence-transformers — zero API cost, no rate limits.

Usage:
    from corpus.embeddings import embed_texts, embed_query

    doc_vecs = embed_texts(["Section 3(p) of Patents Act...", "Under BDA 2002..."])
    query_vec = embed_query("Can I patent a traditional Ayurvedic formulation?")
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

# multilingual-e5-large: 560M params, 1024-dim embeddings, excellent Hindi support.
# Falls back to all-MiniLM-L6-v2 (English-only) if EMBEDDING_MODEL env var overrides.
_DEFAULT_MODEL = "intfloat/multilingual-e5-large"

# E5 models require a task prefix for optimal performance:
# "query: " for search queries, "passage: " for documents.
_QUERY_PREFIX = "query: "
_DOC_PREFIX = "passage: "


@lru_cache(maxsize=1)
def _get_model(model_name: str = _DEFAULT_MODEL) -> SentenceTransformer:
    """Load the embedding model once and cache it for the process lifetime."""
    import os
    name = os.getenv("EMBEDDING_MODEL", model_name)
    return SentenceTransformer(name)


def embed_texts(texts: list[str], model_name: str = _DEFAULT_MODEL) -> list[list[float]]:
    """
    Embed a list of document passages. Adds the 'passage: ' prefix required by E5.
    Returns a list of float vectors (one per input text).
    """
    model = _get_model(model_name)
    prefixed = [_DOC_PREFIX + t for t in texts]
    embeddings = model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str, model_name: str = _DEFAULT_MODEL) -> list[float]:
    """
    Embed a single search query. Adds the 'query: ' prefix required by E5.
    Returns a single float vector.
    """
    model = _get_model(model_name)
    prefixed = _QUERY_PREFIX + query
    embedding = model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False)
    return embedding.tolist()


def embedding_dim(model_name: str = _DEFAULT_MODEL) -> int:
    """Return the embedding dimension for the configured model."""
    model = _get_model(model_name)
    return model.get_sentence_embedding_dimension()

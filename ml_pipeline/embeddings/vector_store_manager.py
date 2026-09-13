"""
Vector Store Manager for CRAG (IP-SAKTI Sahayak PS045)
Integrates with Qdrant for metadata-filtered hybrid retrieval enforcing rules R4, R7, and R10.

Embedding Strategy (priority order):
  1. Cohere embed-multilingual-v3.0  — API-based, 1024-dim, multilingual (default when COHERE_API_KEY set)
  2. Hash-based pseudo-embedding     — Deterministic, offline, for tests without API keys (384-dim)
"""

import os
import re
import hashlib
import logging
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from ml_pipeline.crag.schema import LegalChunk, JurisdictionType, ProvenanceStatus, IPType

logger = logging.getLogger("vector_store_manager")


class EmbeddingProvider:
    """
    Pluggable embedding provider.
    Auto-selects Cohere embed-multilingual-v3.0 when COHERE_API_KEY is available,
    falling back to a deterministic hash-based embedding for offline / test usage.
    """

    # Cohere embed-multilingual-v3.0 produces 1024-dim vectors
    COHERE_DIM = 1024
    # Hash-based fallback dimension
    HASH_DIM = 384

    def __init__(self):
        self._cohere_client = None
        self._model = None
        self._dim = self.HASH_DIM
        self._init_cohere()

    def _init_cohere(self):
        """Attempts to initialize Cohere embed client."""
        cohere_key = os.getenv("COHERE_API_KEY")
        if not cohere_key:
            logger.info(
                "COHERE_API_KEY not set. Using hash-based offline embedding (tests/dev only). "
                "Set COHERE_API_KEY to activate semantic embeddings."
            )
            return

        try:
            import cohere
            self._cohere_client = cohere.Client(api_key=cohere_key)
            self._model = os.getenv("COHERE_EMBED_MODEL", "embed-multilingual-v3.0")
            self._dim = self.COHERE_DIM
            logger.info(f"Cohere embedding model initialized: {self._model} (dim={self._dim})")
        except ImportError:
            logger.warning("cohere package not installed. Run: uv pip install cohere")

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def using_semantic(self) -> bool:
        return self._cohere_client is not None

    def embed_texts(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """
        Embeds a batch of texts.
        - input_type='search_document'  for indexing chunks
        - input_type='search_query'     for embedding user queries
        """
        if self._cohere_client:
            return self._embed_cohere(texts, input_type)
        return [self._hash_embed(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Embeds a single user query with query-optimized representation."""
        results = self.embed_texts([query], input_type="search_query")
        return results[0]

    def _embed_cohere(self, texts: List[str], input_type: str) -> List[List[float]]:
        """Calls Cohere Embed v3 API in batches of 96 (API limit is 96 texts/request)."""
        all_embeddings: List[List[float]] = []
        batch_size = 96

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self._cohere_client.embed(
                    texts=batch,
                    model=self._model,
                    input_type=input_type,
                    embedding_types=["float"]
                )
                all_embeddings.extend(response.embeddings.float_)
            except Exception as e:
                logger.error(f"Cohere embed API error: {e}. Falling back to hash embedding for this batch.")
                all_embeddings.extend([self._hash_embed(t) for t in batch])

        return all_embeddings

    def _hash_embed(self, text: str) -> List[float]:
        """
        Offline hash-based pseudo-embedding (deterministic, for tests/dev).
        Produces a normalized HASH_DIM-dimensional float vector.
        """
        vector = [0.0] * self.HASH_DIM
        words = text.lower().split()
        if not words:
            return vector
        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            vector[h % self.HASH_DIM] += 1.0
        norm = sum(x * x for x in vector) ** 0.5
        return [x / norm for x in vector] if norm > 0 else vector


class VectorStoreManager:
    """
    Qdrant vector store manager with Cohere semantic embeddings and strict legal metadata filtering.
    """

    COLLECTION_NAME = "ayurveda_ip_corpus"

    def __init__(self, location: Optional[str] = None, collection_name: Optional[str] = None):
        self.collection_name = collection_name or self.COLLECTION_NAME
        self.embedder = EmbeddingProvider()

        qdrant_url = os.getenv("QDRANT_URL")
        if location:
            self.client = QdrantClient(location=location)
        elif qdrant_url:
            self.client = QdrantClient(url=qdrant_url)
        else:
            self.client = QdrantClient(":memory:")

        self._ensure_collection()

    def _ensure_collection(self):
        """Creates collection with correct vector dimension, recreating if dim changed."""
        existing = {c.name: c for c in self.client.get_collections().collections}

        if self.collection_name in existing:
            # Check if dimension matches current embedder (may have changed from hash → Cohere)
            info = self.client.get_collection(self.collection_name)
            existing_dim = info.config.params.vectors.size
            if existing_dim != self.embedder.dim:
                logger.warning(
                    f"Embedding dimension changed ({existing_dim} → {self.embedder.dim}). "
                    "Recreating collection. You will need to re-index all chunks."
                )
                self.client.delete_collection(self.collection_name)
            else:
                return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=qmodels.VectorParams(
                size=self.embedder.dim,
                distance=qmodels.Distance.COSINE
            )
        )
        for field in ["jurisdiction", "status", "ip_type", "act_name"]:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field,
                field_schema=qmodels.PayloadSchemaType.KEYWORD
            )

        mode = "Cohere embed-multilingual-v3.0" if self.embedder.using_semantic else "hash-fallback (offline)"
        logger.info(f"Collection '{self.collection_name}' created | Embedding: {mode} | dim={self.embedder.dim}")

    def index_chunks(self, chunks: List[LegalChunk]) -> int:
        """
        Indexes a batch of LegalChunks using Cohere embed (or hash fallback).
        Embeds in a single batched API call for efficiency.
        """
        if not chunks:
            return 0

        texts = [f"{c.act_name} {c.section_id} {c.text}" for c in chunks]
        embeddings = self.embedder.embed_texts(texts, input_type="search_document")

        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                qmodels.PointStruct(
                    id=idx + 1,
                    vector=embedding,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "source": chunk.source,
                        "act_name": chunk.act_name,
                        "section_id": chunk.section_id,
                        "jurisdiction": chunk.jurisdiction.value,
                        "effective_date": chunk.effective_date,
                        "ip_type": chunk.ip_type.value,
                        "status": chunk.status.value,
                        "official_url": chunk.official_url,
                        "text": chunk.text
                    }
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Indexed {len(points)} chunks using {'Cohere' if self.embedder.using_semantic else 'hash'} embeddings.")
        return len(points)

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    @classmethod
    def _compute_mmr(
        cls,
        candidate_payloads: List[dict],
        candidate_vectors: List[List[float]],
        candidate_scores: List[float],
        top_k: int = 5,
        mmr_lambda: float = 0.7
    ) -> List[dict]:
        """
        Maximal Marginal Relevance (MMR) re-ranking.
        Balances query relevance with diversity across candidate embeddings to avoid
        returning redundant, near-duplicate statutory clauses.

        Formula:
            MMR(d) = argmax_{d in U} [ lambda * Relevance(d) - (1 - lambda) * max_{s in S} Sim(d, s) ]
        """
        n = len(candidate_payloads)
        if n == 0:
            return []
        if n <= top_k and n <= 1:
            return candidate_payloads

        target_k = min(top_k, n)

        # Normalize relevance/hybrid scores to [0, 1] range for parity with cosine similarity
        min_score = min(candidate_scores)
        max_score = max(candidate_scores)
        score_range = max_score - min_score
        if score_range > 1e-6:
            norm_scores = [(s - min_score) / score_range for s in candidate_scores]
        else:
            norm_scores = [1.0] * n

        selected_indices: List[int] = []
        unselected_indices = list(range(n))

        # First selection: chunk with highest individual relevance/hybrid score
        first_idx = max(unselected_indices, key=lambda i: candidate_scores[i])
        selected_indices.append(first_idx)
        unselected_indices.remove(first_idx)

        # Iteratively select candidates that maximize marginal relevance
        while len(selected_indices) < target_k and unselected_indices:
            best_idx = -1
            best_mmr_score = float("-inf")

            for idx in unselected_indices:
                relevance = norm_scores[idx]
                # Max similarity to any already selected chunk
                max_sim_to_selected = max(
                    cls._cosine_similarity(candidate_vectors[idx], candidate_vectors[s])
                    for s in selected_indices
                )
                mmr_val = mmr_lambda * relevance - (1.0 - mmr_lambda) * max_sim_to_selected

                if mmr_val > best_mmr_score:
                    best_mmr_score = mmr_val
                    best_idx = idx

            if best_idx != -1:
                selected_indices.append(best_idx)
                unselected_indices.remove(best_idx)
            else:
                break

        return [candidate_payloads[i] for i in selected_indices]

    def search(
        self,
        query: str,
        jurisdiction: Optional[JurisdictionType] = None,
        ip_type: Optional[IPType] = None,
        top_k: int = 5,
        exclude_mock: bool = True,
        use_mmr: Optional[bool] = None,
        mmr_lambda: Optional[float] = None
    ) -> List[LegalChunk]:
        """
        Hybrid search: Cohere/hash semantic embedding + BM25 keyword boost + MMR diversification.
        Enforces Rule R4 (jurisdiction filter) and Rule R7 (mock chunk exclusion).

        Args:
            query: User query text.
            jurisdiction: Optional jurisdiction filter (Rule R4).
            ip_type: Optional IP sub-type filter.
            top_k: Number of final diverse chunks to return.
            exclude_mock: Whether to exclude illustrative mock chunks (Rule R7).
            use_mmr: Whether to apply Maximal Marginal Relevance diversification (defaults to env USE_MMR or True).
            mmr_lambda: Trade-off between relevance (1.0) and diversity (0.0). Defaults to env MMR_LAMBDA or 0.7.
        """
        if use_mmr is None:
            use_mmr = os.getenv("USE_MMR", "true").lower() in ("true", "1", "yes")
        if mmr_lambda is None:
            mmr_lambda = float(os.getenv("MMR_LAMBDA", "0.7"))

        query_vector = self.embedder.embed_query(query)

        must_conditions = []
        must_not_conditions = []

        # Rule R4: Jurisdiction isolation
        if jurisdiction and jurisdiction != JurisdictionType.BOTH:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="jurisdiction",
                    match=qmodels.MatchValue(value=jurisdiction.value)
                )
            )

        # Rule R7: Exclude mock/illustrative chunks from authoritative results
        if exclude_mock:
            must_not_conditions.append(
                qmodels.FieldCondition(
                    key="status",
                    match=qmodels.MatchValue(value=ProvenanceStatus.MOCK_PENDING_ACCESS.value)
                )
            )

        if ip_type and ip_type != IPType.GENERAL:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="ip_type",
                    match=qmodels.MatchValue(value=ip_type.value)
                )
            )

        query_filter = qmodels.Filter(
            must=must_conditions if must_conditions else None,
            must_not=must_not_conditions if must_not_conditions else None
        )

        # Fetch a broader candidate pool for MMR diversity selection
        candidate_pool_size = max(top_k * 4, 15)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=candidate_pool_size,
            with_vectors=True
        ).points

        if not results:
            return []

        # BM25-style keyword boost (works on top of either semantic or hash vectors)
        STOPWORDS = {"what", "where", "when", "which", "under", "from", "with", "this", "that", "have", "about"}
        query_terms = set(w for w in re.findall(r"\w{3,}", query.lower()) if w not in STOPWORDS)

        candidate_payloads = []
        candidate_vectors = []
        candidate_scores = []

        for res in results:
            p = res.payload
            doc_text = f"{p['act_name']} {p['section_id']} {p['text']}".lower()
            doc_terms = set(re.findall(r"\w{3,}", doc_text))
            overlap = query_terms.intersection(doc_terms)

            # Statutory abbreviation boosts
            abbr_boost = 0.0
            if "bda" in query_terms and "biological diversity" in doc_text:
                abbr_boost += 3.0
            if "tkdl" in query_terms and "traditional knowledge" in doc_text:
                abbr_boost += 3.0
            if "gratk" in query_terms and "wipo" in doc_text:
                abbr_boost += 3.0

            hybrid_score = res.score + (len(overlap) * 0.5) + abbr_boost

            candidate_payloads.append(p)
            candidate_vectors.append(res.vector if isinstance(res.vector, list) else query_vector)
            candidate_scores.append(hybrid_score)

        # Apply MMR re-ranking or pure hybrid sort
        if use_mmr and len(candidate_payloads) > 1:
            selected_payloads = self._compute_mmr(
                candidate_payloads=candidate_payloads,
                candidate_vectors=candidate_vectors,
                candidate_scores=candidate_scores,
                top_k=top_k,
                mmr_lambda=mmr_lambda
            )
        else:
            sorted_pairs = sorted(zip(candidate_scores, candidate_payloads), key=lambda x: x[0], reverse=True)
            selected_payloads = [p for _, p in sorted_pairs[:top_k]]

        chunks: List[LegalChunk] = []
        for p in selected_payloads:
            chunks.append(
                LegalChunk(
                    chunk_id=p["chunk_id"],
                    source=p["source"],
                    act_name=p["act_name"],
                    section_id=p["section_id"],
                    jurisdiction=JurisdictionType(p["jurisdiction"]),
                    effective_date=p["effective_date"],
                    ip_type=IPType(p["ip_type"]),
                    status=ProvenanceStatus(p["status"]),
                    official_url=p.get("official_url"),
                    text=p["text"]
                )
            )

        return chunks

"""
backend/app/services/cache_service.py — Redis Query Caching Service.

Provides sub-5ms caching for repeated legal, patentability, and regulatory queries in Charaka IP.
Includes:
- Deterministic query normalization (whitespace, casing, punctuation).
- Rule R4 compliance (strict jurisdiction isolation in cache keys).
- Seamless thread-safe in-memory fallback if Redis is unreachable or unconfigured.
- Observability metadata (source: redis/memory, cache latency).
"""

import re
import json
import time
import hashlib
import logging
import threading
from typing import Any, Dict, Optional, Tuple

import redis
from app.core.config import settings

logger = logging.getLogger("cache_service")


class QueryCacheService:
    """High-performance Redis cache with in-memory fallback for Charaka IP queries."""

    _redis_client: Optional[redis.Redis] = None
    _redis_available: Optional[bool] = None
    _lock = threading.Lock()

    # In-memory fallback store: key -> (expires_at, data_dict)
    _mem_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
    _MAX_MEM_ITEMS = 1000

    @classmethod
    def _get_redis(cls) -> Optional[redis.Redis]:
        """Returns a connected Redis client, or None if disabled/unreachable."""
        if not settings.REDIS_ENABLED:
            return None

        if cls._redis_client is not None and cls._redis_available is True:
            return cls._redis_client

        with cls._lock:
            if cls._redis_client is not None and cls._redis_available is True:
                return cls._redis_client

            try:
                client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                    decode_responses=True,
                )
                client.ping()
                cls._redis_client = client
                cls._redis_available = True
                logger.info("Connected to Redis at %s:%s (db=%s)", settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB)
                return cls._redis_client
            except Exception as exc:
                cls._redis_available = False
                cls._redis_client = None
                logger.warning("Redis unavailable (%s); falling back to in-memory query cache.", exc)
                return None

    @classmethod
    def normalize_query(cls, query: str) -> str:
        """
        Normalizes query text to eliminate superficial differences (whitespace, casing, punctuation).
        e.g., "  Can I patent Ashwagandha?! " -> "can i patent ashwagandha"
        """
        text = query.lower().strip()
        # Strip trailing & leading punctuation
        text = re.sub(r"^[^\w]+|[^\w]+$", "", text)
        # Collapse multi-spaces and newlines into single spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def generate_key(cls, query: str, jurisdiction: str, language: str = "en") -> str:
        """
        Generates a deterministic, collision-resistant cache key complying with Rule R4 (jurisdiction isolation).
        """
        norm_query = cls.normalize_query(query)
        norm_jur = (jurisdiction or "national").lower().strip()
        norm_lang = (language or "en").lower().strip()

        # SHA-256 digest of normalized text
        h = hashlib.sha256(norm_query.encode("utf-8")).hexdigest()[:16]
        return f"charaka:query:{norm_jur}:{norm_lang}:{h}"

    @classmethod
    def get(cls, query: str, jurisdiction: str, language: str = "en") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Retrieves a cached response for the query.
        Returns (cached_dict, cache_source) where cache_source is 'redis' or 'memory', or (None, None).
        """
        key = cls.generate_key(query, jurisdiction, language)

        # 1. Try Redis first
        r = cls._get_redis()
        if r is not None:
            try:
                cached_json = r.get(key)
                if cached_json:
                    data = json.loads(cached_json)
                    return data, "redis"
            except Exception as exc:
                logger.warning("Redis GET failed for key %s: %s", key, exc)

        # 2. Fallback to in-memory store
        now = time.time()
        with cls._lock:
            entry = cls._mem_cache.get(key)
            if entry:
                expires_at, data = entry
                if expires_at > now:
                    return data, "memory"
                else:
                    cls._mem_cache.pop(key, None)

        return None, None

    @classmethod
    def set(
        cls,
        query: str,
        jurisdiction: str,
        response_data: Dict[str, Any],
        language: str = "en",
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Stores query response in cache.
        Returns True if stored successfully in either Redis or memory.
        """
        key = cls.generate_key(query, jurisdiction, language)
        ttl = ttl or settings.REDIS_CACHE_TTL
        serialized = json.dumps(response_data)
        stored_somewhere = False

        # 1. Store in Redis if available
        r = cls._get_redis()
        if r is not None:
            try:
                r.set(key, serialized, ex=ttl)
                stored_somewhere = True
            except Exception as exc:
                logger.warning("Redis SET failed for key %s: %s", key, exc)

        # 2. Also keep in in-memory LRU fallback
        now = time.time()
        with cls._lock:
            if len(cls._mem_cache) >= cls._MAX_MEM_ITEMS:
                # Evict oldest 20%
                keys_to_evict = list(cls._mem_cache.keys())[: cls._MAX_MEM_ITEMS // 5]
                for k in keys_to_evict:
                    cls._mem_cache.pop(k, None)
            cls._mem_cache[key] = (now + ttl, response_data)
            stored_somewhere = True

        return stored_somewhere

    @classmethod
    def clear_all(cls) -> None:
        """Clears all Charaka query cache entries (useful for testing or cache refresh)."""
        r = cls._get_redis()
        if r is not None:
            try:
                keys = r.keys("charaka:query:*")
                if keys:
                    r.delete(*keys)
            except Exception as exc:
                logger.warning("Redis delete keys failed: %s", exc)

        with cls._lock:
            cls._mem_cache.clear()

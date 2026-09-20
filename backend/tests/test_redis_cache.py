"""
backend/tests/test_redis_cache.py — Unit & Integration Tests for Redis Query Caching.

Verifies:
1. Exact & normalized query matching (whitespace, casing, punctuation).
2. Rule R4 jurisdiction isolation (national vs international keys never collide).
3. Thread-safe in-memory fallback when Redis is unreachable.
4. FastAPI /api/v1/query integration (cache hit returns immediately with execution log).
5. Deep Research mode bypass (case intake turns are never cached).
"""

import pytest
from starlette.testclient import TestClient
from app.main import app
from app.services.cache_service import QueryCacheService


@pytest.fixture(autouse=True)
def clean_cache():
    """Ensure clean cache before and after each test."""
    QueryCacheService.clear_all()
    yield
    QueryCacheService.clear_all()


def test_cache_service_set_and_get():
    """Verifies basic set and get in QueryCacheService."""
    query = "What is Section 3(p) of the Patents Act?"
    sample_data = {
        "answer": "Section 3(p) bars patenting of traditional knowledge.",
        "confidence_level": "HIGH",
        "citations": [{"section": "3(p)", "statute": "Patents Act 1970"}],
    }

    # Cache miss
    data, src = QueryCacheService.get(query, jurisdiction="national", language="en")
    assert data is None
    assert src is None

    # Set in cache
    success = QueryCacheService.set(query, jurisdiction="national", response_data=sample_data, language="en")
    assert success is True

    # Cache hit
    data, src = QueryCacheService.get(query, jurisdiction="national", language="en")
    assert data is not None
    assert src in ["redis", "memory"]
    assert data["answer"] == sample_data["answer"]
    assert len(data["citations"]) == 1


def test_query_normalization():
    """Verifies that whitespace, punctuation, and casing variations resolve to the exact same cache entry."""
    canonical = "Can I patent Ashwagandha formulation?"
    variations = [
        "  can i patent ashwagandha formulation?  ",
        "CAN I PATENT ASHWAGANDHA FORMULATION!?",
        "can   i   patent    ashwagandha   formulation",
        "Can I patent Ashwagandha formulation...",
    ]

    sample_data = {"answer": "Classical Ashwagandha is barred under 3(p)."}
    QueryCacheService.set(canonical, jurisdiction="national", response_data=sample_data, language="en")

    for var in variations:
        cached, _ = QueryCacheService.get(var, jurisdiction="national", language="en")
        assert cached is not None, f"Failed cache lookup for variation: {var!r}"
        assert cached["answer"] == sample_data["answer"]


def test_jurisdiction_isolation_rule_r4():
    """Verifies Rule R4: National and International queries never share cache entries."""
    query = "What are the disclosure requirements for genetic resources?"
    nat_data = {"answer": "India National: Form 3 under NBA Biological Diversity Act 2023."}
    intl_data = {"answer": "International: Mandatory disclosure under WIPO GRATK Treaty 2024."}

    QueryCacheService.set(query, jurisdiction="national", response_data=nat_data, language="en")
    QueryCacheService.set(query, jurisdiction="international", response_data=intl_data, language="en")

    res_nat, _ = QueryCacheService.get(query, jurisdiction="national", language="en")
    res_intl, _ = QueryCacheService.get(query, jurisdiction="international", language="en")

    assert res_nat is not None
    assert res_intl is not None
    assert "India National" in res_nat["answer"]
    assert "WIPO GRATK Treaty" in res_intl["answer"]


def test_in_memory_fallback(monkeypatch):
    """Verifies seamless fallback to in-memory store when Redis is completely unavailable."""
    # Force Redis to None
    monkeypatch.setattr(QueryCacheService, "_get_redis", classmethod(lambda cls: None))

    query = "Is neem extract patentable?"
    sample_data = {"answer": "Neem extract is traditional knowledge."}

    # Set with Redis mocked out
    stored = QueryCacheService.set(query, jurisdiction="national", response_data=sample_data, language="en")
    assert stored is True

    # Retrieve from in-memory fallback
    data, src = QueryCacheService.get(query, jurisdiction="national", language="en")
    assert data is not None
    assert src == "memory"
    assert data["answer"] == sample_data["answer"]


def test_query_api_cache_hit_integration():
    """Verifies that calling /api/v1/query twice with the same question hits the cache on the second call."""
    client = TestClient(app)

    payload = {
        "query": "Is a classical Ayurvedic Churna patentable in India?",
        "jurisdiction": "national",
        "mode": "query",
        "language": "en",
        "dpdp_consent": True,
    }

    # 1. First call: CACHE MISS, executes CRAG
    resp1 = client.post("/api/v1/query", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["answer"] != ""

    # 2. Second call: CACHE HIT, returns immediately
    resp2 = client.post("/api/v1/query", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data2["answer"] == data1["answer"]
    # Check that execution logs contain CACHE HIT
    has_cache_hit_log = any("CACHE HIT" in log for log in data2.get("execution_logs", []))
    assert has_cache_hit_log, f"Expected CACHE HIT log in execution_logs, got: {data2.get('execution_logs')}"


def test_deep_research_mode_bypasses_cache():
    """Verifies that multi-turn Innovation Intake queries in Deep Research mode are never cached."""
    client = TestClient(app)

    intake_payload = {
        "query": "I want to patent an Ayurvedic formulation called AyurHeal Topical Gel",
        "jurisdiction": "national",
        "mode": "deep_research",
        "conversation_id": "test-session-cache-bypass",
        "dpdp_consent": True,
    }

    resp = client.post("/api/v1/query", json=intake_payload)
    assert resp.status_code == 200

    # Ensure no cache entry was stored for this query
    cached, _ = QueryCacheService.get(intake_payload["query"], jurisdiction="national", language="en")
    assert cached is None

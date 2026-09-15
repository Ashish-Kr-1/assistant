"""
Tests for the multilingual detection + live web research fallback wired into
POST /api/v1/query (backend/app/api/v1/endpoints/query.py), ported from the "Charak IP"
prototype via ml_pipeline/agents/web_research_agent.py.

The repo-root conftest.py strips all LLM/search API keys for the test session, so these tests
exercise the offline-heuristic and unavailable-search degrade paths — deterministic, free, and
network-free, consistent with the rest of this suite.
"""

from fastapi.testclient import TestClient
from app.main import app
import app.api.v1.endpoints.query as query_module

client = TestClient(app)


def test_devanagari_query_detected_and_answered_without_crashing():
    response = client.post(
        "/api/v1/query",
        json={
            "query": "क्या मैं पारंपरिक आयुर्वेदिक फॉर्मूलेशन का पेटेंट करा सकता हूँ?",
            "jurisdiction": "national",
            "dpdp_consent": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_language"] is not None
    assert "Hindi" in data["detected_language"]
    # No LLM configured in the test session -> honest degrade, not a fake translation.
    assert data["used_web_search"] is False
    assert isinstance(data["answer"], str) and len(data["answer"]) > 0


def test_english_query_unaffected_by_language_detection():
    response = client.post(
        "/api/v1/query",
        json={
            "query": "Can I patent traditional knowledge or classical Ayurvedic formulations under Section 3(p)?",
            "jurisdiction": "national",
            "dpdp_consent": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_language"] == "English"
    assert data["english_query"] is None
    assert data["used_web_search"] is False
    assert len(data["citations"]) >= 1
    assert all(c["source_type"] == "statutory" for c in data["citations"])


def test_weak_local_result_triggers_web_search_fallback(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key-for-test")

    class _FakePipeline:
        def run(self, **kwargs):
            return {
                "query": kwargs.get("query"),
                "jurisdiction": kwargs.get("jurisdiction", "national"),
                "is_abstained": False,
                "answer": "### National (India) Legal Regime\n\nNo strong local match.",
                "citations": [],
                "confidence_score": 0.2,
                "confidence_level": "LOW",
                "escalate_to_human": True,
                "abs_guidance": None,
                "disclaimer": "This is informational guidance, not legal advice.",
            }

    def _fake_run_web_research(query, jurisdiction="national", llm=None):
        return {
            "answer": "Live web research found relevant guidance [1].",
            "citations": [{"number": 1, "title": "Example Source", "url": "https://example.gov.in/doc", "jurisdiction": "national"}],
            "detected_language": "English",
            "english_query": query,
            "used_web_search": True,
        }

    monkeypatch.setattr(query_module, "get_crag_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(query_module, "run_web_research", _fake_run_web_research)

    response = client.post(
        "/api/v1/query",
        json={
            "query": "What patent protection applies to this obscure cross-border scenario with no local corpus match?",
            "jurisdiction": "national",
            "dpdp_consent": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["used_web_search"] is True
    web_citations = [c for c in data["citations"] if c["source_type"] == "web"]
    assert len(web_citations) == 1
    assert web_citations[0]["official_url"] == "https://example.gov.in/doc"
    assert "Live Web Research" in data["answer"]


def test_web_search_skipped_when_local_result_weak_but_no_tavily_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    class _FakePipeline:
        def run(self, **kwargs):
            return {
                "query": kwargs.get("query"),
                "jurisdiction": kwargs.get("jurisdiction", "national"),
                "is_abstained": False,
                "answer": "### National (India) Legal Regime\n\nNo strong local match.",
                "citations": [],
                "confidence_score": 0.2,
                "confidence_level": "LOW",
                "escalate_to_human": True,
                "abs_guidance": None,
                "disclaimer": "This is informational guidance, not legal advice.",
            }

    monkeypatch.setattr(query_module, "get_crag_pipeline", lambda: _FakePipeline())

    response = client.post(
        "/api/v1/query",
        json={
            "query": "What patent protection applies to this obscure cross-border scenario with no local corpus match?",
            "jurisdiction": "national",
            "dpdp_consent": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["used_web_search"] is False
    assert "Live Web Research" not in data["answer"]

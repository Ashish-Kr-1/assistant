"""
Tests for Rule R6 (Paid-Source Consent Guard).

The live statutory corpus (scripts/seed_corpus.py) currently contains zero
sources tagged ProvenanceStatus.VERIFIED_PAID — every ingested chunk is either
VERIFIED_PUBLIC (Indian Kanoon bare acts, WTO/CBD/WIPO treaty PDFs) or
MOCK_PENDING_ACCESS (the illustrative TKDL entry). That means the R6 branch in
app/api/v1/endpoints/query.py is dormant today: it exists for when Phase 3
paid-source ingestion (e.g. Manupatra case law) is added, per the project
roadmap. These tests exercise that dormant path directly so it's proven to
work rather than sitting untested.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.core.r6_consent_guard import R6ConsentGuard
import app.api.v1.endpoints.query as query_module

client = TestClient(app)


# ── Unit tests: R6ConsentGuard in isolation ──────────────────────────────────

def test_requires_paid_source_true_for_verified_paid():
    assert R6ConsentGuard.requires_paid_source("verified_paid") is True


def test_requires_paid_source_false_for_verified_public():
    assert R6ConsentGuard.requires_paid_source("verified_public") is False


def test_build_consent_prompt_known_source_mentions_name_and_url():
    prompt = R6ConsentGuard.build_consent_prompt("manupatra")
    assert prompt is not None
    assert "Manupatra" in prompt
    assert "manupatra.com" in prompt


def test_build_consent_prompt_unknown_source_returns_none():
    assert R6ConsentGuard.build_consent_prompt("not_a_real_source") is None


def test_enforce_consent_granted_allows_access():
    access_granted, record = R6ConsentGuard.enforce(
        query="Section 3(p) prior art for Triphala",
        source_key="tkdl_mou",
        user_ref="user123",
        paid_source_consent=True,
    )
    assert access_granted is True
    assert record.consent_given is True
    assert record.consent_scope == "single_query"


def test_enforce_consent_denied_blocks_access():
    access_granted, record = R6ConsentGuard.enforce(
        query="Section 3(p) prior art for Triphala",
        source_key="tkdl_mou",
        user_ref="user123",
        paid_source_consent=False,
    )
    assert access_granted is False
    assert record.consent_given is False


def test_consent_record_hashes_query_not_raw_text():
    """DPDP compliance: the logged record must never contain the raw query text."""
    query_text = "my very specific unhashed query about ashwagandha patents"
    _, record = R6ConsentGuard.enforce(
        query=query_text,
        source_key="indiakanoon",
        user_ref="user123",
        paid_source_consent=True,
    )
    assert query_text not in record.anonymized_query_hash
    assert len(record.anonymized_query_hash) == 20


# ── Integration test: query.py's R6 branch fires on a paid citation ─────────

class _StubPipeline:
    """Stand-in CRAGPipeline that returns one VERIFIED_PAID citation, so the
    R6 branch in the /query endpoint has something to gate — proving the
    wiring works even though the real corpus never produces this today."""

    def run(self, **kwargs):
        return {
            "answer": "Test answer citing a paid source [paid_chunk_1].",
            "answers_by_regime": {"national": "Test answer [paid_chunk_1]."},
            "citations": [
                {
                    "chunk_id": "paid_chunk_1",
                    "act_name": "Manupatra Annotated Statute",
                    "section_id": "Section 1",
                    "jurisdiction": "national",
                    "effective_date": "2024-01-01",
                    "official_url": "https://manupatra.com/doc/1",
                    "status": "verified_paid",
                    "source_key": "manupatra",
                }
            ],
            "confidence_score": 0.9,
            "confidence_level": "HIGH",
            "is_abstained": False,
            "escalate_to_human": False,
            "abs_guidance": None,
            "disclaimer": "This is informational guidance, not legal advice. Consult a qualified IP professional for advice specific to your case.",
        }


def test_r6_strips_paid_citation_and_prompts_consent_when_denied(monkeypatch):
    monkeypatch.setattr(query_module, "get_crag_pipeline", lambda: _StubPipeline())

    response = client.post(
        "/api/v1/query",
        json={
            "query": "What does Manupatra say about this?",
            "jurisdiction": "national",
            "dpdp_consent": True,
            "paid_source_consent": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["citations"] == []
    assert "Paid Source Access Requested (Rule R6)" in data["answer"]


def test_r6_keeps_paid_citation_when_consent_granted(monkeypatch):
    monkeypatch.setattr(query_module, "get_crag_pipeline", lambda: _StubPipeline())

    response = client.post(
        "/api/v1/query",
        json={
            "query": "What does Manupatra say about this?",
            "jurisdiction": "national",
            "dpdp_consent": True,
            "paid_source_consent": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["citations"]) == 1
    assert data["citations"][0]["chunk_id"] == "paid_chunk_1"

"""
API Tests for Phase 1 Intent + Entity Classification Endpoints.
Tests:
- POST /api/v1/classify (Phase 1 intent messages and formulation wizard backwards compatibility)
- POST /api/v1/query (Phase 1 routing: CHAT bypass, CLARIFICATION, OUT_OF_SCOPE, and INNOVATION_INTAKE)
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── 1. POST /api/v1/classify Endpoint Tests ───────────────────────────────────

def test_api_classify_ip_protection_message():
    response = client.post(
        "/api/v1/classify",
        json={"message": "I want to patent my Ayurvedic formulation"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "IP_PROTECTION"
    assert data["route"] == "INNOVATION_INTAKE"
    assert data["requires_case"] is True
    assert data["confidence"] >= 0.85
    assert data["entities"]["domain"] == "AYURVEDA"


def test_api_classify_legal_qa_message():
    response = client.post(
        "/api/v1/classify",
        json={"message": "What is a patent?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "LEGAL_QA"
    assert data["route"] in ["CRAG", "RESEARCH"]
    assert data["requires_case"] is False


def test_api_classify_chat_greeting_message():
    response = client.post(
        "/api/v1/classify",
        json={"message": "hello"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "CHAT"
    assert data["route"] == "CHAT"
    assert data["requires_case"] is False


def test_api_classify_ambiguous_message():
    response = client.post(
        "/api/v1/classify",
        json={"message": "I have a new product."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "UNKNOWN"
    assert data["route"] == "CLARIFICATION"
    assert data["needs_clarification"] is True
    assert data["clarification_question"] is not None


def test_api_classify_formulation_wizard_backwards_compatibility():
    """Verifies that structured formulation wizard still works on /api/v1/classify."""
    response = client.post(
        "/api/v1/classify",
        json={
            "is_in_first_schedule": True,
            "uses_modified_ratio_or_novel_combo": False,
            "is_standardized_extract": False,
            "intended_for_food": False,
            "intended_for_cosmetic": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category_code"] == "CLASSICAL_MEDICINE"
    assert "Section 3(p)" in data["ip_posture"]


def test_api_classify_empty_payload_fails():
    response = client.post("/api/v1/classify", json={})
    assert response.status_code == 400


# ── 2. POST /api/v1/query Phase 1 Integration Tests ───────────────────────────

def test_api_query_greeting_bypasses_crag():
    """Verifies that greetings never invoke CRAG/Qdrant and return immediate CHAT response."""
    response = client.post(
        "/api/v1/query",
        json={"query": "hi", "jurisdiction": "national", "dpdp_consent": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "CHAT"
    assert data["intent"] == "CHAT"
    assert "Namaste" in data["answer"]
    assert len(data["citations"]) == 0
    assert data["is_abstained"] is False


def test_api_query_ambiguous_returns_clarification():
    response = client.post(
        "/api/v1/query",
        json={"query": "I have a new product.", "jurisdiction": "national", "dpdp_consent": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "CLARIFICATION"
    assert data["intent"] == "UNKNOWN"
    assert data["needs_clarification"] is True


def test_api_query_out_of_scope_rejects():
    response = client.post(
        "/api/v1/query",
        json={"query": "recipe for chocolate cake", "jurisdiction": "national", "dpdp_consent": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "OUT_OF_SCOPE"
    assert data["intent"] == "OUT_OF_SCOPE"
    assert data["is_abstained"] is True

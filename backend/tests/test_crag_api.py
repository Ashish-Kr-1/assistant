from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_query_national_sec_3p():
    response = client.post(
        "/api/v1/query",
        json={
            "query": "Can I patent traditional knowledge or classical Ayurvedic formulations under Section 3(p)?",
            "jurisdiction": "national",
            "dpdp_consent": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_abstained"] is False
    assert len(data["citations"]) >= 1
    assert any("3(p)" in c["section"] for c in data["citations"])
    assert "This is informational guidance, not legal advice" in data["disclaimer"]


def test_api_query_international_wipo():
    response = client.post(
        "/api/v1/query",
        json={
            "query": "What are the mandatory disclosure requirements for genetic resources under WIPO treaty?",
            "jurisdiction": "international",
            "dpdp_consent": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_abstained"] is False
    assert any("WIPO" in c["statute"] for c in data["citations"])


def test_api_query_safe_abstention_r1():
    response = client.post(
        "/api/v1/query",
        json={
            "query": "Quantum gravity teleportation warp drive reactor under ancient Egyptian law",
            "jurisdiction": "national",
            "dpdp_consent": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_abstained"] is True
    assert "Charaka IP" in data["answer"]


def test_api_query_r9_classification_gate():
    response = client.post(
        "/api/v1/query",
        json={
            "query": "I want to file a patent for my herbal extract formulation",
            "jurisdiction": "national",
            "dpdp_consent": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_abstained"] is False
    assert "patent" in data["answer"].lower()
    assert "Formulation Classification Required (Rule R9)" not in data["answer"]

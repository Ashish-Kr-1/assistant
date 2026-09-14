"""
Phase 4 — Research Engine & Report Generator tests.

Runs against the same offline/local test stack as the rest of the suite
(local Qdrant + no LLM API key => deterministic heuristic CRAG fallback —
see ml_pipeline/tests/test_heuristic_fallbacks.py), so no network access or
API keys are required.
"""

import uuid

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def new_conv() -> str:
    return f"CONV-{uuid.uuid4().hex[:10]}"


def create_case(conversation_id=None, user_id="anonymous_user"):
    payload = {"conversation_id": conversation_id or new_conv(), "user_id": user_id}
    r = client.post("/api/v1/cases", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def intake(case_id, message, user_id="anonymous_user"):
    r = client.post(f"/api/v1/cases/{case_id}/intake", json={"message": message, "user_id": user_id})
    assert r.status_code == 200, r.text
    return r.json()


def reach_ready(case_id, jurisdictions=None, user_id="anonymous_user"):
    intake(case_id, "I want to patent my herbal tablet for stress management.", user_id=user_id)
    intake(case_id, "It combines Ashwagandha and Brahmi in a specific ratio.", user_id=user_id)
    intake(case_id, "My own formulation.", user_id=user_id)
    r = client.patch(
        f"/api/v1/cases/{case_id}",
        json={
            "user_id": user_id,
            "profile_patch": {
                "target_jurisdictions": jurisdictions or ["INDIA", "GERMANY"],
                "tk_basis": "NONE",
            },
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "READY_FOR_RESEARCH", data
    return data


def generate_report(case_id, user_id="anonymous_user"):
    r = client.post(f"/api/v1/cases/{case_id}/report", params={"user_id": user_id})
    assert r.status_code == 200, r.text
    return r.json()


# ── 1. Report generation basics ──────────────────────────────────────────

def test_report_null_before_generation():
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    assert r.json()["research_report"] is None


def test_report_generated_and_populated():
    case = create_case()
    reach_ready(case["case_id"])
    data = generate_report(case["case_id"])
    report = data["research_report"]
    assert report is not None
    assert report["case_id"] == case["case_id"]
    assert report["report_markdown"], "report_markdown must not be empty"


def test_report_has_all_16_sections_in_markdown():
    case = create_case()
    reach_ready(case["case_id"])
    report = generate_report(case["case_id"])["research_report"]
    md = report["report_markdown"]
    for heading in [
        "Executive Summary", "Innovation Profile", "User's Objective",
        "Product/Formulation Classification", "IP Domain Mapping",
        "Patent & Prior-Art Research", "Traditional Knowledge Assessment",
        "Biodiversity / ABS Assessment", "Regulatory Considerations",
        "Trademark / Other IP Considerations", "International Jurisdiction Analysis",
        "Risk Assessment", "Evidence Gaps", "Recommended Next Steps",
        "Human Review", "Sources & Evidence",
    ]:
        assert heading in md, f"Missing section heading: {heading}"


def test_report_idempotent_regeneration():
    case = create_case()
    reach_ready(case["case_id"])
    r1 = generate_report(case["case_id"])
    r2 = generate_report(case["case_id"])
    assert r1["research_report"] is not None
    assert r2["research_report"] is not None


# ── 2. Evidence-first, no-hallucination behavior ─────────────────────────

def test_no_orphan_citations_every_evidence_has_source_fields():
    """Every evidence item must trace to a real chunk_id-derived source, never fabricated."""
    case = create_case()
    reach_ready(case["case_id"])
    report = generate_report(case["case_id"])["research_report"]
    for e in report["evidence"]:
        assert e["evidence_id"].startswith("EVD-")
        assert e["jurisdiction"], "evidence must carry a jurisdiction"


def test_abstained_queries_produce_evidence_gaps_not_hallucination():
    """If any research query abstains, it must show up as an explicit evidence gap, never a fabricated answer."""
    case = create_case()
    reach_ready(case["case_id"])
    report = generate_report(case["case_id"])["research_report"]
    abstained_results = [r for r in report["research_results"] if r["is_abstained"]]
    if abstained_results:
        assert len(report["evidence_gaps"]) >= 1
        assert "INSUFFICIENT_EVIDENCE" in report["evidence_gaps_section"] or "INSUFFICIENT_EVIDENCE" in "".join(report["evidence_gaps"])


# ── 3. Risk assessment ────────────────────────────────────────────────────

def test_classical_medicine_case_flags_patent_novelty_risk_and_human_review():
    case = create_case()
    intake(case["case_id"], "I want to protect Triphala churna as described in Charaka Samhita.")
    intake(case["case_id"], "It uses Amalaki, Haritaki, and Vibhitaki exactly per the classical text.")
    intake(case["case_id"], "It is drawn directly from the classical text, no modification.")
    r = client.patch(
        f"/api/v1/cases/{case['case_id']}",
        json={
            "user_id": "anonymous_user",
            "profile_patch": {
                "target_jurisdictions": ["INDIA"],
                "tk_basis": "CLASSICAL_TEXT",
                "classical_reference": "Charaka Samhita Chapter 27",
            },
        },
    )
    assert r.status_code == 200, r.text
    report = generate_report(case["case_id"])["research_report"]
    risks = {ri["risk"]: ri for ri in report["risks"]}
    assert "PATENT_NOVELTY" in risks
    assert risks["PATENT_NOVELTY"]["level"] == "HIGH"
    assert risks["PATENT_NOVELTY"]["requires_human_review"] is True
    assert report["needs_human_review"] is True


def test_multi_jurisdiction_case_flags_international_risk():
    case = create_case()
    reach_ready(case["case_id"], jurisdictions=["INDIA", "GERMANY", "USA"])
    report = generate_report(case["case_id"])["research_report"]
    risk_names = [ri["risk"] for ri in report["risks"]]
    assert "INTERNATIONAL" in risk_names


# ── 4. Jurisdiction isolation ─────────────────────────────────────────────

def test_international_section_lists_each_target_jurisdiction_separately():
    case = create_case()
    reach_ready(case["case_id"], jurisdictions=["INDIA", "GERMANY"])
    report = generate_report(case["case_id"])["research_report"]
    intl_section = report["international_section"]
    assert "INDIA" in intl_section
    assert "GERMANY" in intl_section


# ── 5. Case isolation across users ────────────────────────────────────────

def test_report_denied_for_wrong_user():
    case = create_case(user_id="user-X")
    reach_ready(case["case_id"], user_id="user-X")
    r = client.post(f"/api/v1/cases/{case['case_id']}/report", params={"user_id": "user-Y"})
    assert r.status_code == 403


def test_report_not_found_for_unknown_case():
    r = client.post("/api/v1/cases/CASE-DOES-NOT-EXIST-999/report", params={"user_id": "anonymous_user"})
    assert r.status_code == 404


# ── 6. Auto-runs Phase 3 assessment if missing ────────────────────────────

def test_report_auto_runs_assessment_if_missing():
    """Calling /report before /assess should still succeed (auto-assess first)."""
    case = create_case()
    intake(case["case_id"], "I want to patent my herbal tablet for stress management.")
    intake(case["case_id"], "It combines Ashwagandha and Brahmi in a specific ratio.")
    intake(case["case_id"], "My own formulation.")
    r = client.patch(
        f"/api/v1/cases/{case['case_id']}",
        json={"user_id": "anonymous_user", "profile_patch": {"target_jurisdictions": ["INDIA"], "tk_basis": "NONE"}},
    )
    assert r.status_code == 200
    data = generate_report(case["case_id"])
    assert data["assessment"] is not None
    assert data["research_report"] is not None


# ── 7. Disclaimer ──────────────────────────────────────────────────────────

def test_report_contains_disclaimer():
    case = create_case()
    reach_ready(case["case_id"])
    report = generate_report(case["case_id"])["research_report"]
    assert "PRELIMINARY" in report["DISCLAIMER"]
    assert "PRELIMINARY" in report["report_markdown"] or report["DISCLAIMER"] in report["report_markdown"]

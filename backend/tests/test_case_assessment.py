"""
Phase 3 — Innovation Classification & Legal Domain Mapping tests.

Tests cover the CaseAssessmentAgent directly and also the new
POST /cases/{case_id}/assess API endpoint (auto-trigger via intake + explicit).

All tests are deterministic (no LLM, no Qdrant).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def new_conv() -> str:
    return f"CONV-{uuid.uuid4().hex[:10]}"


def create_case(conversation_id=None, user_id="anonymous_user", title=None):
    payload = {"conversation_id": conversation_id or new_conv(), "user_id": user_id}
    if title:
        payload["title"] = title
    r = client.post("/api/v1/cases", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def intake(case_id, message, user_id="anonymous_user"):
    r = client.post(f"/api/v1/cases/{case_id}/intake", json={"message": message, "user_id": user_id})
    assert r.status_code == 200, r.text
    return r.json()


def reach_ready(case_id):
    """
    Bring a case to READY_FOR_RESEARCH via the deterministic PATCH approach.
    This mirrors test_patch_updates_merge_and_reach_ready in the intake tests.
    """
    intake(case_id, "I want to patent my herbal tablet for stress management.")
    intake(case_id, "It combines Ashwagandha and Brahmi in a specific ratio.")
    intake(case_id, "My own formulation.")
    r = client.patch(
        f"/api/v1/cases/{case_id}",
        json={
            "user_id": "anonymous_user",
            "profile_patch": {"target_jurisdictions": ["INDIA", "GERMANY"], "tk_basis": "NONE"},
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "READY_FOR_RESEARCH", (
        f"Case not ready after PATCH: {data['status']}, missing: {data.get('intake_state', {}).get('missing_information')}"
    )
    return data


# ── 1. Auto-assessment on READY ──────────────────────────────────────────

def test_assessment_auto_triggered_on_ready():
    """When intake reaches READY_FOR_RESEARCH, assessment must be populated."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    data = r.json()
    assert data["status"] == "READY_FOR_RESEARCH"
    assert data["assessment"] is not None, "assessment must be populated after READY"
    assert data["assessment"]["assessment_status"] == "COMPLETED"


def test_assessment_has_all_5_subparts():
    """Completed assessment must contain all 5 Phase 3 subparts."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    a = r.json()["assessment"]
    assert a["normalized"] is not None, "3.1 normalized missing"
    assert a["product_classification"] is not None, "3.2 product_classification missing"
    assert a["ip_domain"] is not None, "3.3 ip_domain missing"
    assert a["regulatory_mapping"] is not None, "3.4 regulatory_mapping missing"
    assert a["research_plan"] is not None, "3.5 research_plan missing"


# ── 2. Product classification accuracy ────────────────────────────────────

def test_proprietary_formulation_classified_correctly():
    """Novel combination + no classical text → PROPRIETARY_MEDICINE."""
    case = create_case()
    intake(case["case_id"], "I want to patent my novel herbal tablet for stress relief.")
    intake(case["case_id"], "It combines Ashwagandha and Brahmi in a novel synergistic ratio.")
    intake(case["case_id"], "My own proprietary formulation, not based on any classical text.")
    r = client.patch(
        f"/api/v1/cases/{case['case_id']}",
        json={"user_id": "anonymous_user", "profile_patch": {"target_jurisdictions": ["INDIA"], "tk_basis": "NONE"}},
    )
    a = r.json()["assessment"]
    assert a is not None
    cls = a["product_classification"]
    assert cls["category"] == "PROPRIETARY_MEDICINE"
    assert cls["confidence"] >= 0.7


def test_patent_via_explicit_assess_endpoint():
    """POST /cases/{id}/assess must run Phase 3 and return assessment."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.post(f"/api/v1/cases/{case['case_id']}/assess", params={"user_id": "anonymous_user"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["assessment"] is not None
    assert data["assessment"]["assessment_status"] == "COMPLETED"


def test_assess_endpoint_is_idempotent():
    """Calling assess twice should not raise errors and should update assessment."""
    case = create_case()
    reach_ready(case["case_id"])
    r1 = client.post(f"/api/v1/cases/{case['case_id']}/assess", params={"user_id": "anonymous_user"})
    r2 = client.post(f"/api/v1/cases/{case['case_id']}/assess", params={"user_id": "anonymous_user"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["assessment"]["assessment_status"] == "COMPLETED"


# ── 3. IP Domain and Section 3(p) ─────────────────────────────────────────

def test_ip_domain_contains_patent_relevant_domains():
    """For a patent-seeking proprietary formulation, patent domains must be present."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    ip_domain = r.json()["assessment"]["ip_domain"]
    assert "PATENT" in ip_domain["ip_domains_applicable"] or "PATENT_POSSIBLE" in ip_domain["primary_ip_domain"]


def test_tkdl_relevance_set_for_formulation():
    """TKDL relevance should be True for Ayurvedic formulation types."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    ip_domain = r.json()["assessment"]["ip_domain"]
    assert ip_domain["tkdl_relevance"] is True


# ── 4. Regulatory Mapping ─────────────────────────────────────────────────

def test_regulatory_mapping_includes_india():
    """India must be in the jurisdiction maps for an India-targeted case."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    jur_maps = r.json()["assessment"]["regulatory_mapping"]["jurisdiction_maps"]
    jurisdictions = [j["jurisdiction"] for j in jur_maps]
    assert "INDIA" in jurisdictions


def test_regulatory_mapping_includes_germany():
    """Germany must appear in the regulatory map since it was stated in the target jurisdictions."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    jur_maps = r.json()["assessment"]["regulatory_mapping"]["jurisdiction_maps"]
    jurisdictions = [j["jurisdiction"] for j in jur_maps]
    assert "GERMANY" in jurisdictions


def test_abs_flagged_for_india():
    """India must have ABS applicability flagged (Biological Diversity Act)."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    jur_maps = r.json()["assessment"]["regulatory_mapping"]["jurisdiction_maps"]
    india_map = next(j for j in jur_maps if j["jurisdiction"] == "INDIA")
    assert india_map["abs_applicable"] is True


# ── 5. Research Plan ──────────────────────────────────────────────────────

def test_research_plan_has_tasks():
    """Research plan must have at least 2 tasks."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    plan = r.json()["assessment"]["research_plan"]
    assert len(plan["research_tasks"]) >= 2


def test_research_plan_has_high_priority_task():
    """At least one HIGH priority task must exist."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    tasks = r.json()["assessment"]["research_plan"]["research_tasks"]
    priorities = [t["priority"] for t in tasks]
    assert "HIGH" in priorities, f"No HIGH priority tasks found. Priorities: {priorities}"


def test_research_plan_has_crag_queries():
    """Recommended CRAG queries must be generated for the Phase 4 engine."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    plan = r.json()["assessment"]["research_plan"]
    assert len(plan["recommended_crag_queries"]) >= 1


# ── 6. Normalized case (3.1) ──────────────────────────────────────────────

def test_normalized_case_contains_ingredients():
    """Normalized case should include the ingredients from the intake profile."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    normalized = r.json()["assessment"]["normalized"]
    assert "Ashwagandha" in normalized["ingredients_summary"]
    assert "Brahmi" in normalized["ingredients_summary"]


def test_normalized_case_target_jurisdictions():
    """Normalized case must reflect both INDIA and GERMANY."""
    case = create_case()
    reach_ready(case["case_id"])
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    normalized = r.json()["assessment"]["normalized"]
    assert "INDIA" in normalized["target_jurisdictions"]
    assert "GERMANY" in normalized["target_jurisdictions"]


# ── 7. Assessment isolation ────────────────────────────────────────────────

def test_assessment_not_present_during_intake():
    """During active intake, assessment must be null."""
    case = create_case()
    intake(case["case_id"], "I want to patent my Ayurvedic formulation.")
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    data = r.json()
    assert data["status"] == "INTAKE_IN_PROGRESS"
    assert data["assessment"] is None, "assessment must be null while intake is in progress"


def test_two_separate_cases_have_independent_assessments():
    """Two separate cases must never share assessment state."""
    case_a = create_case()
    case_b = create_case()
    reach_ready(case_a["case_id"])
    r_a = client.get(f"/api/v1/cases/{case_a['case_id']}", params={"user_id": "anonymous_user"})
    r_b = client.get(f"/api/v1/cases/{case_b['case_id']}", params={"user_id": "anonymous_user"})
    assert r_a.json()["assessment"] is not None
    assert r_b.json()["assessment"] is None  # case B hasn't reached READY


# ── 8. Ownership enforcement ──────────────────────────────────────────────

def test_assess_endpoint_denied_for_wrong_user():
    """POST /assess must return 403 for a different user_id."""
    case = create_case(user_id="user-X")
    r = client.post(f"/api/v1/cases/{case['case_id']}/assess", params={"user_id": "user-Y"})
    assert r.status_code == 403


def test_assess_endpoint_not_found_for_unknown_case():
    """POST /assess must return 404 for a non-existent case_id."""
    r = client.post("/api/v1/cases/CASE-DOES-NOT-EXIST-999/assess", params={"user_id": "anonymous_user"})
    assert r.status_code == 404


# ── 9. Agent unit tests ────────────────────────────────────────────────────

def test_agent_direct_proprietary_profile():
    """Unit test: CaseAssessmentAgent.assess() directly with a proprietary profile."""
    from ml_pipeline.agents.case_assessment_agent import CaseAssessmentAgent
    from ml_pipeline.schemas.case_schema import (
        InnovationProfile, IPObjective, TKBasis,
    )
    from ml_pipeline.schemas.assessment_schema import AssessmentStatus, FormulationCategory

    profile = InnovationProfile(
        short_description="A novel herbal tablet for stress management.",
        ingredients=["Ashwagandha", "Brahmi", "Shankhpushpi"],
        claimed_novelty="Proprietary synergistic ratio not documented in any classical text.",
        primary_ip_objective=IPObjective.PATENT,
        ip_objectives=[IPObjective.PATENT, IPObjective.TRADEMARK],
        tk_basis=TKBasis.NONE,
        target_jurisdictions=["INDIA", "USA"],
        novel_combination=True,
    )
    assessment = CaseAssessmentAgent.assess("CASE-TEST-001", profile)
    assert assessment.assessment_status == AssessmentStatus.COMPLETED
    assert assessment.product_classification is not None
    assert assessment.product_classification.category == FormulationCategory.PROPRIETARY_MEDICINE
    assert assessment.ip_domain is not None
    assert assessment.regulatory_mapping is not None
    assert len(assessment.regulatory_mapping.jurisdiction_maps) == 2  # INDIA + USA
    assert assessment.research_plan is not None
    assert len(assessment.research_plan.research_tasks) >= 2


def test_agent_classical_profile_sets_3p_bar():
    """Unit test: Classical TK basis must trigger Section 3(p) bar."""
    from ml_pipeline.agents.case_assessment_agent import CaseAssessmentAgent
    from ml_pipeline.schemas.case_schema import (
        InnovationProfile, IPObjective, TKBasis,
    )
    from ml_pipeline.schemas.assessment_schema import FormulationCategory

    profile = InnovationProfile(
        short_description="Triphala churna as described in Charaka Samhita.",
        ingredients=["Amalaki", "Haritaki", "Vibhitaki"],
        primary_ip_objective=IPObjective.PATENT,
        ip_objectives=[IPObjective.PATENT],
        tk_basis=TKBasis.CLASSICAL_TEXT,
        target_jurisdictions=["INDIA"],
        classical_reference="Charaka Samhita Chapter 27",
    )
    assessment = CaseAssessmentAgent.assess("CASE-TEST-002", profile)
    assert assessment.product_classification.category == FormulationCategory.CLASSICAL_MEDICINE
    assert assessment.ip_domain.section_3p_analysis.bar_likely is True


def test_agent_phytopharmaceutical_profile():
    """Unit test: Standardized extract must classify as PHYTOPHARMACEUTICAL."""
    from ml_pipeline.agents.case_assessment_agent import CaseAssessmentAgent
    from ml_pipeline.schemas.case_schema import (
        InnovationProfile, IPObjective, TKBasis,
    )
    from ml_pipeline.schemas.assessment_schema import FormulationCategory

    profile = InnovationProfile(
        short_description="A standardized Ashwagandha extract with defined withanolide markers.",
        ingredients=["Withania somnifera (standardized extract)"],
        claimed_novelty="Novel extraction process yielding 7% withanolides — four bioactive markers defined.",
        primary_ip_objective=IPObjective.PATENT,
        ip_objectives=[IPObjective.PATENT],
        tk_basis=TKBasis.NONE,
        target_jurisdictions=["INDIA", "EU"],
        standardization="7% Withanolides",
        bioactive_markers=["Withaferin A", "Withanolide B", "Withanolide D", "Withanone"],
    )
    assessment = CaseAssessmentAgent.assess("CASE-TEST-003", profile)
    assert assessment.product_classification.category == FormulationCategory.PHYTOPHARMACEUTICAL
    assert assessment.ip_domain.section_3p_analysis.bar_likely is False


def test_agent_empty_profile_does_not_crash():
    """Unit test: Even a mostly-empty profile must return a valid (partial) assessment."""
    from ml_pipeline.agents.case_assessment_agent import CaseAssessmentAgent
    from ml_pipeline.schemas.case_schema import InnovationProfile
    from ml_pipeline.schemas.assessment_schema import AssessmentStatus

    profile = InnovationProfile()
    assessment = CaseAssessmentAgent.assess("CASE-TEST-EMPTY", profile)
    assert assessment.assessment_status == AssessmentStatus.COMPLETED
    assert assessment.normalized is not None
    assert assessment.research_plan is not None

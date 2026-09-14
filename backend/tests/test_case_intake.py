"""
Phase 2 — Innovation Intake + Case Creation tests.

These hit /api/v1/cases directly (not /api/v1/query) for the bulk of scenarios,
since that path never touches Phase 1 or any LLM — it's the fast, fully
deterministic surface, consistent with this project's existing convention of
not depending on a live LLM/API key for correctness in tests (see
ml_pipeline/tests/test_heuristic_fallbacks.py). A couple of tests exercise the
/api/v1/query integration explicitly.

Each test uses a fresh uuid4 conversation_id so tests are independent even
though the (sqlite-backed, see backend/app/db/session.py) case store persists
across the whole test session.
"""

import uuid

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


# ── 1. New case creation ──────────────────────────────────────────────────

def test_new_case_creation():
    case = create_case()
    assert case["case_id"].startswith("CASE-")
    assert case["status"] == "INTAKE_IN_PROGRESS"
    assert case["profile"]["short_description"] is None
    assert case["intake_state"]["status"] == "IN_PROGRESS"


# ── 2. Existing case retrieval ────────────────────────────────────────────

def test_existing_case_retrieval():
    case = create_case()
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "anonymous_user"})
    assert r.status_code == 200
    assert r.json()["case_id"] == case["case_id"]


def test_case_retrieval_not_found():
    r = client.get("/api/v1/cases/CASE-DOES-NOT-EXIST", params={"user_id": "anonymous_user"})
    assert r.status_code == 404


# ── 3. Active case detection ──────────────────────────────────────────────

def test_active_case_detection():
    conv = new_conv()
    case = create_case(conversation_id=conv)
    r = client.get("/api/v1/cases/active", params={"conversation_id": conv, "user_id": "anonymous_user"})
    assert r.status_code == 200
    assert r.json()["case_id"] == case["case_id"]


def test_active_case_none_when_no_case_exists():
    r = client.get("/api/v1/cases/active", params={"conversation_id": new_conv(), "user_id": "anonymous_user"})
    assert r.status_code == 200
    assert r.json() is None


# ── 4 & 5. Conversation isolation ─────────────────────────────────────────

def test_same_conversation_same_case_via_query():
    conv = new_conv()
    r1 = client.post("/api/v1/query", json={
        "query": "I want to patent my Ayurvedic formulation.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    r2 = client.post("/api/v1/query", json={
        "query": "It is a herbal capsule for better sleep.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["case_id"] == r2.json()["case_id"]


def test_different_conversation_isolated_case():
    conv_a = new_conv()
    conv_b = new_conv()
    case_a = create_case(conversation_id=conv_a)
    case_b = create_case(conversation_id=conv_b)
    assert case_a["case_id"] != case_b["case_id"]

    intake(case_a["case_id"], "It combines Ashwagandha in a novel extract.")
    case_b_fresh = client.get(f"/api/v1/cases/{case_b['case_id']}", params={"user_id": "anonymous_user"}).json()
    assert case_b_fresh["profile"]["ingredients"] == []  # no leakage from case A


# ── 6. User information extraction ────────────────────────────────────────

def test_information_extraction_from_free_text():
    case = create_case()
    intake(case["case_id"], "I want help with a patent.")
    result = intake(case["case_id"], "It combines Ashwagandha and Brahmi in a specific ratio.")
    assert "Ashwagandha" in result["profile"]["ingredients"]
    assert "Brahmi" in result["profile"]["ingredients"]


def test_extraction_never_invents_fields():
    case = create_case()
    result = intake(case["case_id"], "My product is a new herbal tablet.")
    # Only what was said: "tablet" keyword yes, but no ingredients were named.
    assert result["profile"]["ingredients"] == []


# ── 7. Missing information detection ──────────────────────────────────────

def test_missing_information_detection():
    case = create_case()
    assert "short_description" in case["intake_state"]["missing_information"]
    assert "primary_ip_objective" in case["intake_state"]["missing_information"]


# ── 8. Progressive questioning (critical sequence) ────────────────────────

def test_progressive_questioning_full_sequence():
    case = create_case()
    case_id = case["case_id"]

    r = intake(case_id, "I want to patent my Ayurvedic formulation.")
    assert "help with" in r["next_question"] or r["next_question"] is not None

    r = intake(case_id, "It is a herbal tablet intended for stress management.")
    assert "novel" in r["next_question"]

    r = intake(case_id, "It combines Ashwagandha and Brahmi in a specific ratio.")
    assert "classical" in r["next_question"] or "traditional" in r["next_question"]
    assert r["profile"]["ingredients"] == ["Ashwagandha", "Brahmi"]

    r = intake(case_id, "My own formulation, not based on any classical text.")
    assert "countries" in r["next_question"] or "markets" in r["next_question"]
    assert r["profile"]["tk_basis"] == "NONE"

    r = intake(case_id, "India and Germany.")
    assert r["ready_for_research"] is True
    assert r["status"] == "READY_FOR_RESEARCH"
    assert set(r["profile"]["target_jurisdictions"]) == {"INDIA", "GERMANY"}


# ── 9, 11, 12. Case update / ingredient accumulation & dedup ─────────────

def test_case_update_accumulates_ingredients_without_erasing():
    case = create_case()
    case_id = case["case_id"]
    r1 = intake(case_id, "It contains Ashwagandha.")
    assert r1["profile"]["ingredients"] == ["Ashwagandha"]

    r2 = intake(case_id, "It also contains Brahmi.")
    assert r2["profile"]["ingredients"] == ["Ashwagandha", "Brahmi"]  # preserved + appended, not replaced


def test_duplicate_ingredient_handling():
    case = create_case()
    case_id = case["case_id"]
    intake(case_id, "It contains Ashwagandha.")
    r = intake(case_id, "Yes, definitely Ashwagandha is the key ingredient.")
    assert r["profile"]["ingredients"].count("Ashwagandha") == 1


# ── 10. Adding IP objectives ──────────────────────────────────────────────

def test_adding_secondary_ip_objective_preserves_primary():
    case = create_case()
    case_id = case["case_id"]
    r1 = intake(case_id, "I want to patent my formulation.")
    assert r1["profile"]["primary_ip_objective"] == "PATENT"

    r2 = intake(case_id, "I also want trademark protection.")
    assert r2["profile"]["primary_ip_objective"] == "PATENT"  # unchanged
    assert "TRADEMARK" in r2["profile"]["secondary_ip_objectives"]
    assert set(r2["profile"]["ip_objectives"]) == {"PATENT", "TRADEMARK"}


# ── 13. Jurisdiction normalization ────────────────────────────────────────

def test_jurisdiction_normalization():
    case = create_case()
    r = intake(case["case_id"], "I'm considering india and germany for this.")
    assert set(r["profile"]["target_jurisdictions"]) == {"INDIA", "GERMANY"}


# ── 14. New case confirmation (§12) ───────────────────────────────────────

def test_new_case_requires_confirmation_via_query():
    conv = new_conv()
    r1 = client.post("/api/v1/query", json={
        "query": "I want to patent my Ayurvedic formulation.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    first_case_id = r1.json()["case_id"]

    r2 = client.post("/api/v1/query", json={
        "query": "It is a herbal tablet for stress management.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    assert r2.json()["case_id"] == first_case_id

    # Announcing an unrelated second invention must NOT silently merge into case 1.
    r3 = client.post("/api/v1/query", json={
        "query": "I have another invention I'd like to protect too.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    assert r3.json()["case_id"] == first_case_id  # still on the original case
    assert "new case" in r3.json()["answer"].lower()

    # Confirming creates a genuinely new case.
    r4 = client.post("/api/v1/query", json={
        "query": "Yes, please create a new case.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    assert r4.json()["case_id"] != first_case_id


def test_declining_new_case_keeps_existing_case():
    conv = new_conv()
    r1 = client.post("/api/v1/query", json={
        "query": "I want to patent my Ayurvedic formulation.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    first_case_id = r1.json()["case_id"]
    client.post("/api/v1/query", json={
        "query": "It is a herbal tablet for stress management.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    client.post("/api/v1/query", json={
        "query": "I have another invention as well.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    # Decline; this message should be applied to the existing case instead.
    r = client.post("/api/v1/query", json={
        "query": "No, just add it to the current one — it combines Ashwagandha and Brahmi.",
        "jurisdiction": "national", "dpdp_consent": True, "conversation_id": conv,
    })
    assert r.json()["case_id"] == first_case_id


# ── 15. Case ownership validation ─────────────────────────────────────────

def test_case_ownership_denied_for_other_user():
    case = create_case(user_id="user-A")
    r = client.get(f"/api/v1/cases/{case['case_id']}", params={"user_id": "user-B"})
    assert r.status_code == 403

    r = client.post(
        f"/api/v1/cases/{case['case_id']}/intake",
        json={"message": "trying to read someone else's case", "user_id": "user-B"},
    )
    assert r.status_code == 403


# ── 16, 17. Empty / ambiguous input ───────────────────────────────────────

def test_empty_intake_message_rejected():
    case = create_case()
    r = client.post(f"/api/v1/cases/{case['case_id']}/intake", json={"message": "   "})
    assert r.status_code == 400


def test_ambiguous_input_does_not_crash_and_keeps_asking():
    case = create_case()
    r = intake(case["case_id"], "hmm not sure")
    assert r["status"] == "INTAKE_IN_PROGRESS"
    assert r["next_question"] is not None


# ── 18, 19. Malformed / failing extraction paths are safe ────────────────

def test_patch_with_malformed_enum_value_rejected_not_crashing():
    case = create_case()
    r = client.patch(
        f"/api/v1/cases/{case['case_id']}",
        json={"user_id": "anonymous_user", "profile_patch": {"primary_ip_objective": "NOT_A_REAL_OBJECTIVE"}},
    )
    # Must not 500 — invalid enum values are rejected, not silently accepted or crashing.
    assert r.status_code in (400, 422)


def test_intake_survives_when_llm_unavailable(monkeypatch):
    from ml_pipeline.crag import llm_factory
    monkeypatch.setattr(llm_factory, "get_llm", lambda *a, **kw: None)
    case = create_case()
    r = intake(case["case_id"], "It combines Ashwagandha and Brahmi.")
    assert r["profile"]["ingredients"] == ["Ashwagandha", "Brahmi"]


# ── 20. User-stated information overrides inference ──────────────────────

def test_user_stated_ip_objective_marked_in_provenance():
    case = create_case()
    r = intake(case["case_id"], "I want to patent my formulation.")
    assert r["profile"]["field_provenance"].get("primary_ip_objective") == "USER_STATED"


# ── 21. READY state via direct PATCH ──────────────────────────────────────

def test_patch_updates_merge_and_reach_ready():
    case = create_case()
    case_id = case["case_id"]
    intake(case_id, "I want to patent my herbal tablet for stress management.")
    intake(case_id, "It combines Ashwagandha and Brahmi.")
    intake(case_id, "My own formulation.")
    r = client.patch(
        f"/api/v1/cases/{case_id}",
        json={
            "user_id": "anonymous_user",
            "profile_patch": {"target_jurisdictions": ["INDIA"], "tk_basis": "NONE"},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "READY_FOR_RESEARCH"
    assert "Ashwagandha" in data["profile"]["ingredients"]  # prior fields preserved through PATCH

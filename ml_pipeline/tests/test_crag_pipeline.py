"""
Unit & Integration Tests for CRAG Pipeline (Rules R1-R10).
"""

import pytest
from ml_pipeline.crag.graph import CRAGPipeline
from ml_pipeline.crag.schema import JurisdictionType, ProvenanceStatus
from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager
from scripts.seed_corpus import get_foundational_corpus


@pytest.fixture(scope="module")
def seeded_pipeline():
    """Initializes and seeds an in-memory vector store for testing."""
    manager = VectorStoreManager()
    corpus = get_foundational_corpus()
    manager.index_chunks(corpus)
    pipeline = CRAGPipeline(vector_store=manager)
    return pipeline


def test_national_sec_3p_retrieval_and_answer(seeded_pipeline):
    """Verifies that classical Ayurvedic patent query retrieves Section 3(p) and cites it."""
    result = seeded_pipeline.run(
        query="Can I patent traditional knowledge or classical Ayurvedic formulations under Section 3(p)?",
        jurisdiction="national"
    )

    assert result["is_abstained"] is False
    assert result["confidence_level"] in ["HIGH", "MEDIUM"]
    assert len(result["citations"]) >= 1
    # Check Section 3(p) is in citations
    cited_sections = [c["section_id"] for c in result["citations"]]
    assert any("3(p)" in s for s in cited_sections)
    # Check Rule R5 disclaimer
    assert "This is informational guidance, not legal advice" in result["disclaimer"]


def test_international_wipo_disclosure(seeded_pipeline):
    """Verifies international regime queries retrieve WIPO GRATK Treaty."""
    result = seeded_pipeline.run(
        query="What are the mandatory disclosure requirements for genetic resources under WIPO treaty?",
        jurisdiction="international"
    )

    assert result["is_abstained"] is False
    cited_acts = [c["act_name"] for c in result["citations"]]
    assert any("WIPO Treaty" in a for a in cited_acts)


def test_safe_abstention_rule_r1(seeded_pipeline):
    """Verifies Rule R1: Query with no matching legal basis triggers safe abstention."""
    result = seeded_pipeline.run(
        query="Quantum gravity teleportation warp drive reactor under ancient Egyptian law",
        jurisdiction="national"
    )

    assert result["is_abstained"] is True
    assert "zero-hallucination protocols" in result["answer"]
    assert result["confidence_score"] == 0.0
    assert result["escalate_to_human"] is True


def test_rule_r9_classification_gate(seeded_pipeline):
    """Verifies Rule R9: Generic patent query triggers formulation clarification question."""
    result = seeded_pipeline.run(
        query="I want to file a patent for my herbal extract formulation",
        jurisdiction="national"
    )

    assert result.get("needs_classification_clarification") is True
    assert "Formulation Classification Required (Rule R9)" in result["answer"]


def test_abs_pointer_trigger(seeded_pipeline):
    """Verifies Biological Diversity Act ABS obligation pointer triggers on botanical mention."""
    result = seeded_pipeline.run(
        query="What are the compliance steps for commercial sale of Ashwagandha products under BDA?",
        jurisdiction="national"
    )

    assert result["is_abstained"] is False
    assert result["abs_guidance"] is not None
    assert "Ashwagandha (Withania somnifera)" in result["abs_guidance"]["botanical_name"]
    assert "Biological Diversity (Amendment) Act, 2023" in result["abs_guidance"]["statutory_basis"]


def test_mock_chunk_exclusion_rule_r7(seeded_pipeline):
    """Verifies Rule R7: Mock chunks (like illustrative TKDL) are excluded from authoritative retrieval."""
    results = seeded_pipeline.vector_store.search(
        query="Triphala Churna Charaka Samhita Chikitsasthana",
        jurisdiction=JurisdictionType.NATIONAL,
        exclude_mock=True
    )

    for chunk in results:
        assert chunk.status != ProvenanceStatus.MOCK_PENDING_ACCESS


def test_database_level_jurisdiction_filtering(seeded_pipeline):
    """
    Verifies Rule R4: Jurisdiction filtering is strictly enforced at the database level.
    No international chunks are returned when querying National/India,
    and no Indian chunks are returned when querying International.
    """
    # 1. National search
    nat_results = seeded_pipeline.vector_store.search(
        query="disclosure requirements for genetic resources and patent application",
        jurisdiction=JurisdictionType.NATIONAL,
        top_k=5,
        exclude_mock=True
    )
    assert len(nat_results) > 0
    for chunk in nat_results:
        assert chunk.jurisdiction in (JurisdictionType.NATIONAL, JurisdictionType.INDIA)
        assert chunk.jurisdiction != JurisdictionType.INTERNATIONAL

    # 2. International search
    intl_results = seeded_pipeline.vector_store.search(
        query="disclosure requirements for genetic resources and patent application",
        jurisdiction=JurisdictionType.INTERNATIONAL,
        top_k=5,
        exclude_mock=True
    )
    assert len(intl_results) > 0
    for chunk in intl_results:
        assert chunk.jurisdiction == JurisdictionType.INTERNATIONAL
        assert chunk.jurisdiction not in (JurisdictionType.NATIONAL, JurisdictionType.INDIA)


def test_cross_jurisdiction_dual_pipeline_calls(seeded_pipeline):
    """
    Verifies Rule R4: For cross-jurisdiction ('both') queries, two independent retrieval
    and answer generation calls are executed, producing two unblended, labeled sections.
    """
    result = seeded_pipeline.run(
        query="What are the disclosure requirements for traditional genetic resources under Indian law and international treaties?",
        jurisdiction="both",
        skip_classification_gate=True
    )

    assert result["is_abstained"] is False
    assert "### National (India) Legal Regime" in result["answer"]
    assert "### International Legal Regime" in result["answer"]

    # Verify citations from both regimes are present
    cited_jurisdictions = {c.get("jurisdiction") for c in result["citations"]}
    assert "national" in cited_jurisdictions
    assert "international" in cited_jurisdictions

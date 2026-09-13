"""
Unit tests for Maximal Marginal Relevance (MMR) in VectorStoreManager.
Verifies diversity selection, redundancy penalization, and search integration.
"""

import pytest
from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager
from ml_pipeline.crag.schema import LegalChunk, JurisdictionType, ProvenanceStatus, IPType


def test_mmr_diversification_penalizes_redundancy():
    """
    Candidate 1 and Candidate 2 have near-identical embeddings (redundant).
    Candidate 3 is slightly less relevant but orthogonal/distinct (diverse).
    MMR should select Candidate 1 first, then prefer diverse Candidate 3 over redundant Candidate 2.
    """
    # Vector 1: Highly aligned with query [1.0, 0.0]
    # Vector 2: Almost identical to Vector 1 [0.99, 0.05] (duplicate clause)
    # Vector 3: Orthogonal vector [0.0, 1.0] (different statutory topic)
    candidate_payloads = [
        {"chunk_id": "chunk_1", "text": "patents act sec 3p duplicate a"},
        {"chunk_id": "chunk_2", "text": "patents act sec 3p duplicate b"},
        {"chunk_id": "chunk_3", "text": "biological diversity act sec 3 abs"},
    ]
    candidate_vectors = [
        [1.0, 0.0],
        [0.99, 0.05],
        [0.0, 1.0],
    ]
    # Raw relevance scores: chunk_1 (10.0), chunk_2 (9.8), chunk_3 (7.0)
    candidate_scores = [10.0, 9.8, 7.0]

    # With MMR (lambda=0.5), chunk_3 should be picked second instead of the redundant chunk_2
    selected_mmr = VectorStoreManager._compute_mmr(
        candidate_payloads=candidate_payloads,
        candidate_vectors=candidate_vectors,
        candidate_scores=candidate_scores,
        top_k=2,
        mmr_lambda=0.5
    )

    selected_ids = [c["chunk_id"] for c in selected_mmr]
    assert selected_ids[0] == "chunk_1"
    assert selected_ids[1] == "chunk_3"  # Diverse chunk selected over redundant chunk_2!


def test_mmr_pure_relevance_when_lambda_one():
    """When mmr_lambda=1.0, MMR behaves like standard top-k score ranking."""
    candidate_payloads = [
        {"chunk_id": "chunk_1", "text": "clause 1"},
        {"chunk_id": "chunk_2", "text": "clause 2"},
        {"chunk_id": "chunk_3", "text": "clause 3"},
    ]
    candidate_vectors = [
        [1.0, 0.0],
        [0.99, 0.05],
        [0.0, 1.0],
    ]
    candidate_scores = [10.0, 9.8, 7.0]

    selected_mmr = VectorStoreManager._compute_mmr(
        candidate_payloads=candidate_payloads,
        candidate_vectors=candidate_vectors,
        candidate_scores=candidate_scores,
        top_k=2,
        mmr_lambda=1.0  # Pure relevance
    )

    selected_ids = [c["chunk_id"] for c in selected_mmr]
    assert selected_ids == ["chunk_1", "chunk_2"]


def test_vector_store_search_with_mmr_flag():
    """Verifies that search() runs with use_mmr=True and use_mmr=False seamlessly."""
    manager = VectorStoreManager()
    test_chunks = [
        LegalChunk(
            chunk_id="chk_sec3p",
            source="Patents Act, 1970",
            act_name="The Patents Act, 1970",
            section_id="Section 3(p)",
            jurisdiction=JurisdictionType.NATIONAL,
            effective_date="1970-09-19",
            ip_type=IPType.PATENT,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            text="An invention which in effect is traditional knowledge is not patentable."
        ),
        LegalChunk(
            chunk_id="chk_bda",
            source="Biological Diversity Act, 2002",
            act_name="Biological Diversity Act, 2002",
            section_id="Section 6",
            jurisdiction=JurisdictionType.NATIONAL,
            effective_date="2003-02-05",
            ip_type=IPType.BIODIVERSITY_ABS,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            text="No person shall apply for any intellectual property right without approval of NBA."
        ),
    ]
    manager.index_chunks(test_chunks)

    # Search with MMR enabled
    results_mmr = manager.search(
        query="patent traditional knowledge biodiversity",
        jurisdiction=JurisdictionType.NATIONAL,
        top_k=2,
        use_mmr=True,
        mmr_lambda=0.7
    )
    assert len(results_mmr) == 2

    # Search with MMR disabled (pure hybrid score)
    results_pure = manager.search(
        query="patent traditional knowledge biodiversity",
        jurisdiction=JurisdictionType.NATIONAL,
        top_k=2,
        use_mmr=False
    )
    assert len(results_pure) == 2

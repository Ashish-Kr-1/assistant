"""
Direct tests for the offline heuristic fallbacks in grader.py and verifier.py —
the code paths that run when no LLM is configured (Rule R3 has no NLI model to
fall back on in that case). These had zero dedicated test coverage before:
in an environment with COHERE_API_KEY set, the real Cohere LLM path is used
instead and the heuristics are never exercised, so a loose threshold here
could silently rubber-stamp weak matches with nobody noticing. These tests
force the heuristic path directly (self.llm = None) regardless of environment.
"""

from ml_pipeline.crag.grader import RelevanceGrader
from ml_pipeline.crag.verifier import CitationVerifier
from ml_pipeline.crag.schema import (
    GradingOutcome,
    EntailmentResult,
    LegalChunk,
    JurisdictionType,
    IPType,
    ProvenanceStatus,
)


def _make_grader() -> RelevanceGrader:
    g = RelevanceGrader()
    g.llm = None  # force heuristic path
    return g


def _make_verifier() -> CitationVerifier:
    v = CitationVerifier()
    v.llm = None  # force heuristic path
    return v


def _make_chunk(text: str, act_name="Trade Marks Act, 1999", section_id="Section 9") -> LegalChunk:
    return LegalChunk(
        chunk_id="test_chunk",
        source="test",
        act_name=act_name,
        section_id=section_id,
        jurisdiction=JurisdictionType.NATIONAL,
        effective_date="1999-01-01",
        ip_type=IPType.TRADEMARK_GI,
        status=ProvenanceStatus.VERIFIED_PUBLIC,
        text=text,
    )


CHUNK_TEXT = (
    "Trade marks capable of distinguishing goods must not be descriptive or "
    "generic terms used in ordinary commerce for similar goods."
)


# ── Grader heuristic ─────────────────────────────────────────────────────────

def test_heuristic_grade_correct_requires_substantial_overlap():
    grader = _make_grader()
    chunk = _make_chunk(CHUNK_TEXT)
    graded = grader.grade_chunk(
        "descriptive generic goods commerce distinguishing marks", chunk
    )
    assert graded.outcome == GradingOutcome.CORRECT


def test_heuristic_grade_ambiguous_on_weak_overlap():
    grader = _make_grader()
    chunk = _make_chunk(CHUNK_TEXT)
    graded = grader.grade_chunk("goods commerce unrelated pricing structures", chunk)
    assert graded.outcome == GradingOutcome.AMBIGUOUS


def test_heuristic_grade_incorrect_on_no_overlap():
    grader = _make_grader()
    chunk = _make_chunk(CHUNK_TEXT)
    graded = grader.grade_chunk("unrelated pricing structures nothing shared", chunk)
    assert graded.outcome == GradingOutcome.INCORRECT


def test_heuristic_grade_generic_legal_boilerplate_does_not_inflate_overlap():
    """Words like 'section', 'act', 'government', 'application' appear in nearly
    every statutory chunk — they must not, by themselves, count toward a CORRECT
    grade for an otherwise unrelated query."""
    grader = _make_grader()
    chunk = _make_chunk(CHUNK_TEXT)
    graded = grader.grade_chunk(
        "What does the section of this act say about government application requirements?",
        chunk,
    )
    assert graded.outcome == GradingOutcome.INCORRECT


# ── Verifier heuristic ───────────────────────────────────────────────────────

ENTAILMENT_CHUNK_TEXT = (
    "The quick brown fox jumps over the lazy dog near the river bank every morning."
)


def test_heuristic_entailment_yes_requires_section_match_and_majority_overlap():
    verifier = _make_verifier()
    chunk = _make_chunk(ENTAILMENT_CHUNK_TEXT, section_id="Section 5")
    result = verifier._heuristic_entailment(
        "Under Section 5 the quick brown fox jumps over the lazy dog.", chunk
    )
    assert result.entailment == EntailmentResult.YES


def test_heuristic_entailment_partial_when_section_matches_but_overlap_weak():
    verifier = _make_verifier()
    chunk = _make_chunk(ENTAILMENT_CHUNK_TEXT, section_id="Section 5")
    result = verifier._heuristic_entailment(
        "Under Section 5 the brown jumps happen daily near unrelated locations elsewhere.",
        chunk,
    )
    assert result.entailment == EntailmentResult.PARTIAL


def test_heuristic_entailment_partial_when_overlap_strong_but_no_section_match():
    verifier = _make_verifier()
    chunk = _make_chunk(ENTAILMENT_CHUNK_TEXT, section_id="Section 5")
    result = verifier._heuristic_entailment(
        "The quick brown fox jumps over the lazy dog daily.", chunk
    )
    assert result.entailment == EntailmentResult.PARTIAL


def test_heuristic_entailment_no_when_unrelated():
    verifier = _make_verifier()
    chunk = _make_chunk(ENTAILMENT_CHUNK_TEXT, section_id="Section 5")
    result = verifier._heuristic_entailment(
        "Completely unrelated legal provisions about foreign trademark opposition procedures.",
        chunk,
    )
    assert result.entailment == EntailmentResult.NO

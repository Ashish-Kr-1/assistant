"""
orchestration/verifier.py — Node 5: Citation audit + confidence scoring.

Checks the drafter's answer for:
  1. Citation validity: every [n] marker must correspond to a real entry in the source catalog.
  2. Hallucination guard: every factual claim must be grounded in the cited snippet.
  3. Missing citations: factual sentences without any [n] marker.

Outputs:
  - is_verified: bool
  - verification_feedback: str | None (critique for the drafter retry loop)
  - confidence: ConfidenceInfo (level, score, reason)
  - escalation_recommended: bool
  - escalation_reason: str | None
"""

import re
from pydantic import BaseModel, Field

from orchestration.state import OrchestratorState, ConfidenceInfo, SourceItem

# Matches [1], [2][3], [1,2], [12]
_CITATION_RE = re.compile(r"\[(\d+)\]")

_MAX_SNIPPET_CHARS = 400


class VerificationResult(BaseModel):
    is_verified: bool = Field(description="True if all citations are valid and claims are grounded.")
    invalid_citation_numbers: list[int] = Field(
        default_factory=list,
        description="List of [n] numbers present in the draft that don't exist in the source catalog.",
    )
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="List of factual sentences that appear unsupported by their cited snippet.",
    )
    uncited_factual_sentences: list[str] = Field(
        default_factory=list,
        description="List of factual sentences that have no [n] citation marker at all.",
    )
    confidence_level: str = Field(
        description="Overall confidence: 'HIGH', 'MEDIUM', 'LOW', or 'UNCERTAIN'."
    )
    confidence_score: float = Field(description="Numeric confidence 0.0–1.0.")
    confidence_reason: str = Field(description="Brief explanation of the confidence level.")
    escalation_recommended: bool = Field(
        default=False,
        description="True if this question requires a human IP professional due to complexity or low confidence.",
    )
    escalation_reason: str | None = Field(
        default=None,
        description="Why escalation is recommended (if applicable).",
    )


_VERIFIER_SYSTEM = """\
You are a citation auditor for a legal research assistant. You will be given:
  1. A numbered source catalog (title + snippet for each source).
  2. A draft legal answer that should cite those sources using [n] markers.

Your tasks:
1. Find any [n] numbers in the draft that don't appear in the catalog (invalid citations).
2. For each factual sentence with a [n] citation, verify that the cited snippet actually
   supports the claim. Flag sentences where the citation doesn't match the claim.
3. Find factual sentences in the draft that have NO [n] citation at all.
4. Assign an overall confidence level:
   HIGH      — All citations valid, all factual claims grounded in snippets, comprehensive coverage.
   MEDIUM    — Minor gaps or 1 uncertain citation; answer is generally reliable.
   LOW       — Multiple unsupported claims, or significant gaps in source coverage.
   UNCERTAIN — Draft is based on no sources, or fundamental statutory questions unanswered.
5. Recommend escalation if: confidence is LOW or UNCERTAIN, or the question involves
   complex multi-jurisdiction analysis, patent prosecution strategy, or regulatory filings.

Be strict but fair. A sentence that is a general legal principle is acceptable without
citation. Only flag concrete factual assertions that need grounding.
"""


def _build_verification_prompt(draft: str, catalog: dict[int, SourceItem]) -> str:
    sources_block = "\n\n".join(
        f"[{n}] {item['title']}\n    {item['content'][:_MAX_SNIPPET_CHARS]}"
        for n, item in catalog.items()
    )
    return (
        f"Source Catalog:\n{sources_block}\n\n"
        f"Draft Answer to Verify:\n{draft}"
    )


def _extract_cited_numbers(text: str) -> set[int]:
    return {int(m) for m in _CITATION_RE.findall(text)}


def verifier_node(state: OrchestratorState, model) -> OrchestratorState:
    """
    LangGraph node. Audits the draft for citation validity and grounding.
    Returns verification result and confidence score.
    """
    draft = state.get("draft_answer", "")
    catalog = state.get("source_catalog", {})
    retry_count = state.get("retry_count", 0)

    # Fast-path: if no sources at all, mark as UNCERTAIN
    if not catalog:
        return {
            "is_verified": False,
            "verification_feedback": "No source catalog available. Cannot verify citations.",
            "confidence": ConfidenceInfo(
                level="UNCERTAIN",
                score=0.0,
                reason="No authoritative sources were retrieved for this query.",
            ),
            "escalation_recommended": True,
            "escalation_reason": "No corpus sources found. Human expert review required.",
            "retry_count": retry_count,
        }

    # Step 1: structural check — cited numbers that don't exist in catalog
    cited_numbers = _extract_cited_numbers(draft)
    catalog_numbers = set(catalog.keys())
    invalid_numbers = cited_numbers - catalog_numbers

    # If trivially invalid, skip LLM verification and fail fast
    if invalid_numbers and retry_count >= 1:
        feedback = (
            f"The draft contains citation numbers {sorted(invalid_numbers)} "
            f"which do not exist in the source catalog (valid: {sorted(catalog_numbers)}). "
            f"Remove or correct these citations."
        )
        return {
            "is_verified": False,
            "verification_feedback": feedback,
            "confidence": ConfidenceInfo(level="LOW", score=0.2, reason=feedback),
            "escalation_recommended": True,
            "escalation_reason": "Citation verification failed after retry.",
            "retry_count": retry_count,
        }

    # Step 2: LLM semantic verification
    verifier = model.with_structured_output(VerificationResult)
    prompt = _build_verification_prompt(draft, catalog)
    result: VerificationResult = verifier.invoke([
        {"role": "system", "content": _VERIFIER_SYSTEM},
        {"role": "user", "content": prompt},
    ])

    # Combine structural and LLM-detected invalid citations
    all_invalid = sorted(set(result.invalid_citation_numbers) | invalid_numbers)
    is_verified = bool(result.is_verified and not all_invalid)

    # Build feedback string for drafter retry
    feedback_parts = []
    if all_invalid:
        feedback_parts.append(
            f"Invalid citation numbers (not in source catalog): {all_invalid}. "
            f"Valid numbers: {sorted(catalog_numbers)}."
        )
    if result.unsupported_claims:
        feedback_parts.append(
            "The following claims appear unsupported by their cited snippets:\n"
            + "\n".join(f"  - {c}" for c in result.unsupported_claims)
        )
    if result.uncited_factual_sentences:
        feedback_parts.append(
            "The following factual sentences have no citation:\n"
            + "\n".join(f"  - {s}" for s in result.uncited_factual_sentences[:3])
        )

    feedback = "\n\n".join(feedback_parts) if feedback_parts else None

    # Adjust confidence if verification failed
    conf_level = result.confidence_level
    conf_score = result.confidence_score
    if not is_verified:
        if conf_level == "HIGH":
            conf_level = "MEDIUM"
            conf_score = min(conf_score, 0.6)
        if all_invalid and retry_count >= 1:
            conf_level = "LOW"
            conf_score = min(conf_score, 0.3)

    return {
        "is_verified": is_verified,
        "verification_feedback": feedback,
        "confidence": ConfidenceInfo(
            level=conf_level,
            score=conf_score,
            reason=result.confidence_reason,
        ),
        "escalation_recommended": result.escalation_recommended or (not is_verified and retry_count >= 1),
        "escalation_reason": result.escalation_reason or ("Citation verification failed after retry." if not is_verified and retry_count >= 1 else None),
        "retry_count": retry_count,
    }

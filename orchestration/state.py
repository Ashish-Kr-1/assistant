"""
orchestration/state.py — Shared state schema for the Charaka IP LangGraph pipeline.

All nodes read from and write back to OrchestratorState. LangGraph passes this
dict through each node in sequence (or in parallel for sub-agents in Phase 3).

Field ownership:
  raw_question        → set by caller (agent.py / main.py)
  jurisdiction        → set by caller; refined by gatekeeper
  is_in_scope         → set by gatekeeper
  refusal_message     → set by gatekeeper (only when out-of-scope)
  language_name       → set by gatekeeper (detect_language)
  is_english          → set by gatekeeper
  english_query       → set by gatekeeper
  sources_label       → set by gatekeeper
  ip_type             → set by router
  resolved_jurisdiction → set by router ("IN", "INTL", or "BOTH")
  search_queries      → set by researcher
  source_catalog      → set by researcher (immutable numbered dict)
  draft_answer        → set by drafter
  is_verified         → set by verifier
  verification_feedback → set by verifier (critique for retry)
  retry_count         → managed by graph (max 1)
  confidence_level    → set by verifier
  confidence_score    → set by verifier
  confidence_reason   → set by verifier
  escalation_recommended → set by verifier / presenter
  escalation_reason   → set by verifier / presenter
  final_answer        → set by presenter
  cited_sources       → set by presenter
  disclaimer          → set by presenter (always code-injected, never from model)
"""

from typing import Annotated, TypedDict


class SourceItem(TypedDict):
    number: int
    title: str
    url: str
    content: str        # snippet used for citation grounding


class ConfidenceInfo(TypedDict):
    level: str           # "HIGH" | "MEDIUM" | "LOW" | "UNCERTAIN"
    score: float         # 0.0 – 1.0
    reason: str          # human-readable explanation


class OrchestratorState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────────────
    raw_question: str
    jurisdiction: str           # "india" | "international" | "both"  (from caller)

    # ── Gatekeeper outputs ──────────────────────────────────────────────────────
    is_in_scope: bool
    refusal_message: str | None
    language_name: str          # e.g. "Hindi (Devanagari script)"
    is_english: bool
    english_query: str          # English rewrite for search
    sources_label: str          # Localized "Sources" word

    # ── Router outputs ──────────────────────────────────────────────────────────
    ip_type: str                # "patent" | "trademark" | "gi" | "copyright" | "ayush" | "abs" | "general"
    resolved_jurisdiction: str  # "IN" | "INTL" | "BOTH"

    # ── Researcher outputs ──────────────────────────────────────────────────────
    search_queries: list[str]
    source_catalog: dict[int, SourceItem]   # 1-indexed, immutable after researcher

    # ── Drafter outputs ─────────────────────────────────────────────────────────
    draft_answer: str

    # ── Verifier outputs ────────────────────────────────────────────────────────
    is_verified: bool
    verification_feedback: str | None
    retry_count: int
    confidence: ConfidenceInfo
    escalation_recommended: bool
    escalation_reason: str | None

    # ── Presenter outputs ────────────────────────────────────────────────────────
    final_answer: str
    cited_sources: list[SourceItem]
    disclaimer: str             # Always code-injected, never from model


# ── Routing constants ─────────────────────────────────────────────────────────

class Route:
    """String constants used as LangGraph conditional edge return values."""
    REFUSE = "refuse"
    RESEARCH = "research"
    VERIFY_PASS = "verify_pass"
    VERIFY_RETRY = "verify_retry"
    PRESENT = "present"


# ── Static disclaimer (code-injected, NEVER trusted from model) ───────────────

DISCLAIMER = (
    "\n\n---\n"
    "⚠️ *This response is for informational purposes only and does not constitute "
    "legal advice. For patent prosecution, regulatory filings, or legal proceedings, "
    "consult a qualified IP attorney or registered patent agent.*"
)

"""
orchestration/presenter.py — Node 6: Localization, disclaimer injection, and final assembly.

Responsibilities:
  1. Strip any model-written Sources heading/list from the draft.
  2. Build the verified Sources section in code from the actual catalog
     (only sources the model actually cited).
  3. Inject the mandatory disclaimer — always in code, NEVER trusted from the model.
  4. Attach localized Sources heading using the detected sources_label.
  5. Return the fully assembled final_answer and cited_sources list.
"""

import re

from orchestration.state import DISCLAIMER, OrchestratorState, SourceItem

# Matches trailing lines like "[1] Some Title — https://..."
_TRAILING_CITATION_LINE_RE = re.compile(
    r"^\[?\d+\]?\s.+https?://\S+", re.IGNORECASE
)
# Matches all inline [n] markers (including [2][3] style)
_CITATION_RE = re.compile(r"\[(\d+)\]")


def _strip_model_written_sources(text: str) -> str:
    """
    Remove any citation-list block the model wrote despite being told not to.
    Detects trailing '[n] ... https://...' lines and their preceding heading line.
    Language-agnostic — looks at URL pattern, not a literal 'Sources' word.
    """
    lines = text.rstrip().split("\n")
    i = len(lines)
    while i > 0 and _TRAILING_CITATION_LINE_RE.match(lines[i - 1].strip()):
        i -= 1
    # Also remove the heading line immediately before the citation block if it's short and not a section divider
    if (
        i > 0
        and i < len(lines)
        and 0 < len(lines[i - 1].strip()) <= 40
        and "http" not in lines[i - 1]
        and not lines[i - 1].strip().startswith("===")
    ):
        i -= 1
    return "\n".join(lines[:i]).rstrip()


def _find_cited_numbers(text: str) -> set[int]:
    """Extract all [n] numbers cited in the body text."""
    return {int(m) for m in _CITATION_RE.findall(text)}


def _build_sources_section(
    cited_sources: list[SourceItem],
    sources_label: str,
) -> str:
    """Build the code-verified Sources section."""
    heading = sources_label.rstrip(":") + ":"
    lines = [f"[{s['number']}] {s['title']} — {s['url']}" for s in cited_sources]
    return f"{heading}\n" + "\n".join(lines)


def presenter_node(state: OrchestratorState, model=None) -> OrchestratorState:
    """
    LangGraph node. Assembles the final response:
      1. Strip model-written sources
      2. Find which source numbers the model actually cited
      3. Build verified Sources section in code
      4. Inject disclaimer
      5. Generate structured ABS checklist & TKDL prior-art assessment
      6. Attach facilitator contact if escalation recommended
      7. Return complete final_answer + cited_sources + structured objects
    """
    draft = state.get("draft_answer", "")
    catalog = state.get("source_catalog", {})
    sources_label = state.get("sources_label", "Sources")
    confidence = state.get("confidence", {})

    # Step 1: Strip any model-generated Sources block
    body = _strip_model_written_sources(draft)

    # Step 2: Find which [n] numbers the model actually cited
    cited_numbers = _find_cited_numbers(body)
    cited_sources = [catalog[n] for n in sorted(cited_numbers) if n in catalog]

    # Step 3: Build Sources section in code
    if cited_sources:
        sources_section = _build_sources_section(cited_sources, sources_label)
        body_with_sources = f"{body}\n\n{sources_section}"
    else:
        body_with_sources = body

    # Step 4: Add confidence notice for LOW / UNCERTAIN answers
    confidence_level = confidence.get("level", "MEDIUM") if isinstance(confidence, dict) else "MEDIUM"
    if confidence_level in ("LOW", "UNCERTAIN"):
        confidence_notice = (
            f"\n\n🔴 **Confidence: {confidence_level}** — "
            f"{confidence.get('reason', 'Limited source coverage for this query.')}\n"
            f"For authoritative guidance, please escalate to a qualified IP professional."
        )
        body_with_sources += confidence_notice

    # Step 5: Inject mandatory disclaimer (code-enforced, never from model)
    final_answer = body_with_sources + DISCLAIMER

    # Step 6: Generate structured ABS checklist & TKDL assessment (Phase 4)
    abs_checklist = None
    tkdl_assessment = None
    if model:
        try:
            from orchestration.abs_helper import generate_abs_checklist
            abs_obj = generate_abs_checklist(state, model)
            if abs_obj.applicable:
                abs_checklist = abs_obj.model_dump()
        except Exception:
            abs_checklist = None

        try:
            from orchestration.tkdl_pointer import evaluate_tkdl_prior_art
            tkdl_obj = evaluate_tkdl_prior_art(state, model)
            if tkdl_obj.checked:
                tkdl_assessment = tkdl_obj.model_dump()
        except Exception:
            tkdl_assessment = None

    # Step 7: Escalation triggers & Facilitator Contact
    escalation_recommended = state.get("escalation_recommended", False)
    escalation_reason = state.get("escalation_reason")

    question_lower = state.get("raw_question", "").lower()
    escalation_keywords = [
        "patent attorney", "patent agent", "filing assistance", "infringement notice",
        "cease and desist", "lawsuit", "court", "litigation", "hire lawyer"
    ]
    if any(kw in question_lower for kw in escalation_keywords):
        escalation_recommended = True
        if not escalation_reason:
            escalation_reason = "Query requests professional patent prosecution, legal representation, or litigation counsel."

    facilitator_contact = None
    if escalation_recommended:
        facilitator_contact = {
            "title": "IPO Registered Patent & Trademark Agent Directory",
            "directory_url": "https://ipindia.gov.in",
            "nba_helpdesk": "https://nbaindia.org",
            "ayush_portal": "https://ayush.gov.in",
            "advice": "For formal patent filing, statutory appeals, or ABS clearance, engage a registered patent agent or IP attorney.",
        }

    return {
        "final_answer": final_answer,
        "cited_sources": cited_sources,
        "disclaimer": DISCLAIMER,
        "abs_checklist": abs_checklist,
        "tkdl_assessment": tkdl_assessment,
        "escalation_recommended": escalation_recommended,
        "escalation_reason": escalation_reason,
        "facilitator_contact": facilitator_contact,
    }


def refusal_node(state: OrchestratorState) -> OrchestratorState:
    """
    Short-circuit node for out-of-scope questions.
    Returns the gatekeeper's refusal message + disclaimer, no sources.
    """
    refusal = state.get("refusal_message", "This question is outside the scope of Charaka IP.")
    final = refusal + DISCLAIMER
    return {
        "final_answer": final,
        "cited_sources": [],
        "disclaimer": DISCLAIMER,
        "source_catalog": {},
    }

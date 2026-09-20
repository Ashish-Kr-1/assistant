"""
orchestration/router.py — Node 2: IP-type and jurisdiction classification.

Takes the gatekeeper's english_query + raw_question and classifies:
  - ip_type: which area of IP law / AYUSH the question belongs to
  - resolved_jurisdiction: "IN" | "INTL" | "BOTH"

This lets the researcher node filter the vector store to the most relevant
statutory corpus slices, and lets the drafter produce the right answer structure.
"""

from pydantic import BaseModel, Field

from orchestration.state import OrchestratorState

_VALID_IP_TYPES = {"patent", "trademark", "gi", "copyright", "ayush", "abs", "tkdl", "general"}

_VALID_JURISDICTIONS = {"IN", "INTL", "BOTH"}


class RouterOutput(BaseModel):
    ip_type: str = Field(
        description=(
            "The primary IP/AYUSH domain: "
            "'patent', 'trademark', 'gi', 'copyright', 'ayush', 'abs', 'tkdl', or 'general'."
        )
    )
    resolved_jurisdiction: str = Field(
        description=(
            "Jurisdiction scope needed to fully answer: "
            "'IN' (India-only), 'INTL' (international-only), or 'BOTH'."
        )
    )
    abs_clearance_required: bool = Field(
        default=False,
        description=(
            "True if the question likely involves biological resources of Indian origin "
            "and NBA clearance under Biological Diversity Act Section 6 is relevant."
        )
    )
    tkdl_check_required: bool = Field(
        default=False,
        description="True if the question involves a traditional formulation where TKDL prior-art search is relevant."
    )


_ROUTER_SYSTEM = """\
You are a legal domain classifier for Charaka IP, an assistant specializing in
Indian IP law and Ayurveda/AYUSH regulatory matters.

Given an English search query about IP or Ayurveda/AYUSH, classify:

1. ip_type — the primary legal domain:
   "patent"     — patentability, patent prosecution, patent exclusions (§3(p), §3(d), §3(e))
   "trademark"  — trade mark registration, well-known marks, passing off, Madrid Protocol
   "gi"         — geographical indications, GI tags, Lisbon Agreement
   "copyright"  — copyright, authorship, Berne Convention, software/AI copyright
   "ayush"      — AYUSH drug licensing, ASU formulation classification, Rule 158-B
   "abs"        — Access and Benefit Sharing, NBA clearance, Nagoya Protocol
   "tkdl"       — Traditional Knowledge Digital Library, prior art, §3(p) exclusions
   "general"    — overlaps multiple domains or unclear

2. resolved_jurisdiction:
   "IN"   — purely Indian law question (e.g. "What is Section 3(p) of Indian Patents Act?")
   "INTL" — purely international (e.g. "What does TRIPS Article 27 say?")
   "BOTH" — requires both Indian and international law to answer fully

3. abs_clearance_required — true if question involves Ayurvedic/herbal formulations
   derived from Indian biological resources

4. tkdl_check_required — true if question involves traditional formulations or
   ingredients that may have TKDL prior-art documentation

Examples:
  "Can I patent a traditional Ayurvedic formulation?" → patent, BOTH, abs=true, tkdl=true
  "How to register a trade mark in India?" → trademark, IN
  "What is the Nagoya Protocol?" → abs, INTL
  "GI tag for Basmati rice" → gi, IN
"""


def router_node(state: OrchestratorState, model) -> OrchestratorState:
    """
    LangGraph node. Classifies ip_type and resolved_jurisdiction.
    Also flags whether ABS clearance or TKDL check is needed.
    """
    query = state.get("english_query") or state["raw_question"]

    # Respect caller's explicit jurisdiction override
    caller_jurisdiction = (state.get("jurisdiction") or "both").upper()
    if caller_jurisdiction in ("INDIA", "IN"):
        caller_jurisdiction = "IN"
    elif caller_jurisdiction in ("INTERNATIONAL", "INTL"):
        caller_jurisdiction = "INTL"
    elif caller_jurisdiction in ("BOTH",):
        caller_jurisdiction = "BOTH"
    else:
        caller_jurisdiction = None   # let model decide

    classifier = model.with_structured_output(RouterOutput)
    result: RouterOutput = classifier.invoke([
        {"role": "system", "content": _ROUTER_SYSTEM},
        {"role": "user", "content": query},
    ])

    # Respect caller's explicit jurisdiction override
    resolved = caller_jurisdiction if caller_jurisdiction else result.resolved_jurisdiction.upper()

    if resolved not in _VALID_JURISDICTIONS:
        resolved = "BOTH"

    ip_type = result.ip_type.lower()
    if ip_type not in _VALID_IP_TYPES:
        ip_type = "general"

    return {
        "ip_type": ip_type,
        "resolved_jurisdiction": resolved,
        # Store ABS and TKDL flags in search_queries list for researcher awareness
        # (will be used in Phase 3 sub-agents; stash in state as metadata)
        "_abs_flag": result.abs_clearance_required,
        "_tkdl_flag": result.tkdl_check_required,
    }

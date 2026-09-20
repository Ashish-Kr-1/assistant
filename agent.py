"""LangChain agent implementing a retrieve-and-cite loop for IP and Ayurveda/AYUSH
regulatory questions.

Architecture (Phase 1+):
  This module is now a thin public interface over the multi-agent LangGraph
  orchestration pipeline defined in orchestration/graph.py.

  The `ask()` function signature is preserved exactly for backward compatibility
  with main.py, run_demo.py, and any external callers.

  Orchestration pipeline:
    gatekeeper → router → researcher → drafter → verifier → presenter

  The monolithic system prompt and single-agent create_agent() call have been
  replaced by the coordinated multi-agent graph. Every answer is now:
    1. Scope-checked (gatekeeper) before any search credits are consumed
    2. Routed to the correct IP domain and jurisdiction (router)
    3. Grounded in the authoritative legal corpus + Tavily fallback (researcher)
    4. Drafted with strict inline [n] citations (drafter)
    5. Verified for citation validity and hallucination (verifier, with 1 retry)
    6. Assembled with a code-injected disclaimer and verified Sources list (presenter)

Multilingual support:
  Language detection, English query generation, and localized Sources labels
  are handled inside the gatekeeper node. All 22 scheduled Indian languages
  are supported in Phase 5 via Bhashini integration.
"""

import os

from dotenv import load_dotenv

load_dotenv()


# ── Model factory (unchanged) ──────────────────────────────────────────────────

def build_model():
    """Pick the chat model from LLM_PROVIDER ('openai' or 'cohere'). Defaults to
    cohere; switch to 'openai' once a real OpenAI key is available."""
    provider = os.getenv("LLM_PROVIDER", "cohere").lower()
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0, timeout=60.0)
    if provider == "cohere":
        from langchain_cohere import ChatCohere
        return ChatCohere(model=os.getenv("COHERE_MODEL", "command-a-03-2025"), temperature=0, timeout_seconds=60)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'openai' or 'cohere')")


# ── Public API ─────────────────────────────────────────────────────────────────

def ask(question: str, model=None, jurisdiction: str = "both") -> dict:
    """Run one question through the full orchestration pipeline and return a
    backward-compatible result dict:

    {
        'answer': str,                    # final answer with citations + disclaimer
        'sources': list[dict],            # cited sources [{number, title, url}]
        'detected_language': str,         # e.g. 'Hindi (Devanagari script)'
        'english_query': str,             # English query used for search
        'ip_type': str,                   # 'patent', 'trademark', 'gi', etc.
        'jurisdiction': str,              # 'IN', 'INTL', or 'BOTH'
        'confidence': dict,               # {level, score, reason}
        'escalation_recommended': bool,
        'escalation_reason': str | None,
    }

    Args:
        question: The user's raw question (any supported language).
        model: Optional pre-built LangChain chat model (reused for efficiency).
        jurisdiction: 'india', 'international', or 'both' (default).
    """
    from orchestration.graph import run

    _model = model or build_model()
    state = run(question=question, model=_model, jurisdiction=jurisdiction)

    # Normalize cited_sources for backward compat (strip 'content' field)
    raw_sources = state.get("cited_sources") or []
    sources = [
        {"number": s["number"], "title": s["title"], "url": s["url"]}
        for s in raw_sources
    ]

    confidence = state.get("confidence") or {}
    if not isinstance(confidence, dict):
        confidence = {}

    return {
        "answer":                  state.get("final_answer", ""),
        "sources":                 sources,
        "detected_language":       state.get("language_name", "English"),
        "english_query":           state.get("english_query", question),
        "ip_type":                 state.get("ip_type", "general"),
        "jurisdiction":            state.get("resolved_jurisdiction", "BOTH"),
        "confidence":              confidence,
        "escalation_recommended":  state.get("escalation_recommended", False),
        "escalation_reason":       state.get("escalation_reason"),
        "facilitator_contact":     state.get("facilitator_contact"),
        "abs_checklist":           state.get("abs_checklist"),
        "tkdl_assessment":         state.get("tkdl_assessment"),
    }

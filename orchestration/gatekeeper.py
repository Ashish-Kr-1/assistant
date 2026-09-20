"""
orchestration/gatekeeper.py — Node 1: Scope guard + language detection.

Responsibilities:
  1. Detect the question's language, script, and produce an English search query
     (reuses the existing detect_language() logic from agent.py but now wired into state).
  2. Classify whether the question is in-scope (IP law OR Ayurveda/AYUSH regulatory).
  3. If OUT-OF-SCOPE: set refusal_message in state and short-circuit.
  4. If IN-SCOPE: populate language metadata and pass on.

This node runs BEFORE any search tool is called — no Tavily credits wasted on
off-topic queries.
"""

from pydantic import BaseModel, Field

from orchestration.state import OrchestratorState

# ── Scope classification schema ────────────────────────────────────────────────

class ScopeAndLanguage(BaseModel):
    is_in_scope: bool = Field(
        description=(
            "True if the question is about IP law (patents, trademarks, GI, copyright) "
            "OR Ayurveda/AYUSH regulatory matters. False for all other topics."
        )
    )
    refusal_reason: str | None = Field(
        default=None,
        description=(
            "If is_in_scope is False, a brief explanation of why it's out of scope, "
            "written in the user's own language. Leave null if in scope."
        )
    )
    language_name: str = Field(
        description="Human language AND script, e.g. 'English', 'Hindi (Devanagari script)', 'Hinglish (romanized)'."
    )
    is_english: bool = Field(description="True only if the input is plain English.")
    english_query: str = Field(description="The question rewritten as a concise English web search query.")
    sources_label: str = Field(description="The word for 'Sources' in the user's language/script.")


_GATEKEEPER_SYSTEM = """\
You are the first step of a legal research assistant called Charaka IP.

Your tasks:
1. Detect the language and script of the user's question.
2. Determine if the question is IN-SCOPE for this assistant.

IN-SCOPE topics ONLY:
  - Intellectual property law: patents, trade marks, geographical indications (GI), copyright.
  - Ayurveda and AYUSH regulatory matters: licensing, classification, traditional knowledge
    protection (TKDL), ABS (Access and Benefit Sharing), NBA clearance, pharmacopoeial standards.

OUT-OF-SCOPE: anything else — medicine, cooking, general law, finance, science, etc.

Language detection rules:
  - Judge by ACTUAL SCRIPT. If the text contains Devanagari characters → "Hindi (Devanagari script)".
  - Only use "Hinglish (romanized Hindi-English mix)" when written in Latin letters but uses Hindi grammar/words.
  - For out-of-scope questions, write refusal_reason in the user's own language/script.

Examples:
  "What is Section 3(p) of the Patents Act?" → in_scope=true, language="English"
  "What is the Nagoya Protocol?" → in_scope=true, language="English"
  "भारतीय पेटेंट अधिनियम की धारा 3(पी) क्या है?" → in_scope=true, language="Hindi (Devanagari script)"
  "How do I cook biryani?" → in_scope=false, refusal_reason in user language
"""

import re
_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")

_REFUSAL_TEMPLATES = {
    "english": (
        "I'm Charaka IP, an assistant specializing in IP law and Ayurveda/AYUSH regulatory topics. "
        "Your question appears to be outside my scope. I can only help with patents, trade marks, "
        "geographical indications, copyright, and Ayurveda/AYUSH regulatory matters."
    ),
    "hindi": (
        "मैं Charaka IP हूँ, जो केवल IP कानून और आयुर्वेद/AYUSH नियामक विषयों में सहायता करता है। "
        "आपका प्रश्न मेरे दायरे से बाहर लगता है।"
    ),
}


def gatekeeper_node(state: OrchestratorState, model) -> OrchestratorState:
    """
    LangGraph node. Detects scope and language. Populates:
      is_in_scope, refusal_message, language_name, is_english,
      english_query, sources_label
    """
    question = state["raw_question"]
    detector = model.with_structured_output(ScopeAndLanguage)
    result: ScopeAndLanguage = detector.invoke([
        {"role": "system", "content": _GATEKEEPER_SYSTEM},
        {"role": "user", "content": question},
    ])

    # Hard deterministic override: Devanagari text cannot be Hinglish
    language_name = result.language_name
    if _DEVANAGARI_RE.search(question) and "hinglish" in language_name.lower():
        language_name = "Hindi (Devanagari script)"

    from localization.languages import get_sources_heading
    sources_label = get_sources_heading(language_name) if result.sources_label in (None, "Sources", "Sources:") else result.sources_label

    updates: OrchestratorState = {
        "is_in_scope": result.is_in_scope,
        "language_name": language_name,
        "is_english": result.is_english,
        "english_query": result.english_query,
        "sources_label": sources_label,
        "refusal_message": None,
    }

    if not result.is_in_scope:
        # Use model-generated refusal in user's language
        refusal = result.refusal_reason or _REFUSAL_TEMPLATES["english"]
        updates["refusal_message"] = refusal

    return updates

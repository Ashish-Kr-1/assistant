"""
orchestration/tkdl_pointer.py — Structured Traditional Knowledge Prior-Art Pointer.

Evaluates formulation ingredients against Traditional Knowledge Digital Library (TKDL)
standards and Section 3(p) prior art bars, producing a structured risk assessment.
"""

from pydantic import BaseModel, Field
from orchestration.state import OrchestratorState


class TKDLAssessment(BaseModel):
    checked: bool = Field(description="True if TKDL prior-art assessment is relevant")
    identified_ingredients: list[str] = Field(default_factory=list, description="Extracted botanicals, herbs, or formulation names")
    prior_art_risk: str = Field(description="'HIGH', 'MEDIUM', or 'LOW'")
    risk_explanation: str = Field(description="Explanation of why Section 3(p) or prior art defeats or challenges patentability")
    matched_traditions: list[str] = Field(default_factory=list, description="Traditions where documented: Ayurveda, Unani, Siddha, Yoga")
    section_3p_precaution: str = Field(description="Specific warning regarding Indian Patents Act Section 3(p)")
    recommended_strategy: str = Field(description="Actionable strategy: synergy evidence, novel process, or purified novel entity")
    tkdl_database_url: str = Field(
        default="https://tkdl.res.in",
        description="Official TKDL portal link"
    )


_TKDL_POINTER_SYSTEM = """\
You are a Traditional Knowledge Digital Library (TKDL) examiner and patent prior-art strategist.
Analyze whether the user's question involves traditional formulations, herbs, or folk knowledge.

If YES, provide a structured risk assessment:
- identified_ingredients: list herbs, formulations, or substances involved
- prior_art_risk:
    "HIGH"   — Formulation is already documented in classical texts for known indications. Direct patent is barred under Section 3(p).
    "MEDIUM" — Known ingredients but in modified ratios or modern drug delivery system.
    "LOW"    — Novel isolated bioactive chemical entity or synthetic analog with surprising technical effect.
- matched_traditions: e.g. ["Ayurveda", "Siddha", "Unani"]
- section_3p_precaution: Explain the barrier under §3(p) and §3(e).
- recommended_strategy: Specific advice (e.g. demonstrate non-obvious synergistic index > 1.0, or pursue a process claim).

If unrelated to traditional knowledge or Ayurveda, set checked=false and risk="LOW".
"""


def evaluate_tkdl_prior_art(state: OrchestratorState, model) -> TKDLAssessment:
    """LangGraph helper. Produces structured TKDL prior-art risk assessment."""
    question = state.get("english_query") or state["raw_question"]
    ip_type = state.get("ip_type", "general")
    tkdl_flag = state.get("_tkdl_flag", False)

    herbal_keywords = ["ayurved", "formulation", "herb", "plant", "traditional", "ashwagandha", "curcumin", "turmeric", "neem", "triphala", "chyawanprash"]
    is_relevant = tkdl_flag or ip_type in ("ayush", "tkdl") or any(k in question.lower() for k in herbal_keywords)

    if not is_relevant:
        return TKDLAssessment(
            checked=False,
            identified_ingredients=[],
            prior_art_risk="LOW",
            risk_explanation="Query does not involve traditional herbal formulations or indigenous knowledge.",
            matched_traditions=[],
            section_3p_precaution="Section 3(p) traditional knowledge exclusion does not directly apply.",
            recommended_strategy="Standard patentability examination (novelty, inventive step, industrial applicability) applies.",
        )

    evaluator = model.with_structured_output(TKDLAssessment)
    result: TKDLAssessment = evaluator.invoke([
        {"role": "system", "content": _TKDL_POINTER_SYSTEM},
        {"role": "user", "content": f"Legal Question: {question}\nIP Domain: {ip_type}"},
    ])
    return result

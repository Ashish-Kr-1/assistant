"""
orchestration/abs_helper.py — Structured ABS Compliance Checklist Generator.

Determines whether Section 6 of the Biological Diversity Act, 2002 applies
and produces an actionable 5-step statutory compliance checklist.
"""

from pydantic import BaseModel, Field
from orchestration.state import OrchestratorState


class ABSChecklistStep(BaseModel):
    step_number: int = Field(description="Step sequence 1..5")
    title: str = Field(description="Short step title")
    authority: str = Field(description="Concerned statutory authority (e.g. NBA, SBB)")
    form: str | None = Field(default=None, description="Statutory form name if applicable (e.g. Form III, Form I)")
    mandatory: bool = Field(default=True, description="Whether this step is strictly mandatory")
    details: str = Field(description="Actionable statutory compliance requirement")


class ABSChecklist(BaseModel):
    applicable: bool = Field(description="Whether NBA clearance applies to this invention/formulation")
    summary: str = Field(description="Summary of legal obligation under BDA 2002")
    steps: list[ABSChecklistStep] = Field(default_factory=list, description="Step-by-step compliance roadmap")
    benefit_sharing_framework: str = Field(description="Overview of royalty/benefit-sharing obligations")
    portal_url: str = Field(
        default="https://nbaindia.org",
        description="Official portal URL for filing access & benefit-sharing applications"
    )


_ABS_HELPER_SYSTEM = """\
You are an Access and Benefit-Sharing (ABS) compliance officer specializing in the
Biological Diversity Act, 2002 (BDA) and the Nagoya Protocol.

Analyze the question and determine if research on Indian biological resources or
traditional knowledge is involved. If YES, generate a structured 5-step compliance checklist:

Step 1: Biological Resource Origin Identification (Section 10(4)(d)(ii) Patents Act)
Step 2: Applicant Status & Entity Check (Section 3 vs Section 7 BDA)
Step 3: NBA Form III Application Submission (Rule 18 Biological Diversity Rules 2004)
Step 4: Benefit-Sharing Agreement Negotiation & Execution with NBA
Step 5: Patent Grant Intimation & State Biodiversity Board (SBB) Intimation

If the question is unrelated to biological resources, set applicable=false.
"""


def generate_abs_checklist(state: OrchestratorState, model) -> ABSChecklist:
    """LangGraph helper. Generates a structured ABS compliance checklist."""
    question = state.get("english_query") or state["raw_question"]
    ip_type = state.get("ip_type", "general")
    abs_flag = state.get("_abs_flag", False)

    # Fast evaluation check
    bio_keywords = ["ayurved", "herb", "plant", "formulation", "extract", "biological", "biodiversity", "nba", "abs", "nagoya"]
    is_relevant = abs_flag or ip_type in ("abs", "ayush") or any(k in question.lower() for k in bio_keywords)

    if not is_relevant:
        return ABSChecklist(
            applicable=False,
            summary="This query does not appear to involve biological resources of Indian origin.",
            steps=[],
            benefit_sharing_framework="Not applicable.",
        )

    generator = model.with_structured_output(ABSChecklist)
    result: ABSChecklist = generator.invoke([
        {"role": "system", "content": _ABS_HELPER_SYSTEM},
        {"role": "user", "content": f"Legal Query: {question}\nIP Type: {ip_type}"},
    ])
    return result

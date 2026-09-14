from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    query: str = Field(..., description="User's IPR or regulatory query in plain language.")
    jurisdiction: str = Field("national", description="Jurisdiction filter: 'national' (India) or 'international'.")
    language: str = Field("en", description="ISO language code (e.g., 'en', 'hi', 'ta', 'te').")
    dpdp_consent: bool = Field(True, description="Explicit user privacy consent under DPDP Act 2023.")
    formulation_category: Optional[str] = Field(None, description="Ayurvedic product category if already classified.")
    skip_classification_gate: bool = Field(False, description="Flag to explicitly bypass Rule R9 classification gate.")
    paid_source_consent: bool = Field(
        False,
        description=(
            "Rule R6 — Per-query explicit consent to access paid/gated sources "
            "(e.g., Indian Kanoon, Manupatra, TKDL via MoU). "
            "This consent applies ONLY to this specific query and is individually logged. "
            "Previous consent is never reused. Defaults to False (public corpus only)."
        )
    )
    conversation_id: Optional[str] = Field(
        None,
        description=(
            "Phase 2 — client-managed conversation/session id. When supplied and the routed "
            "intent is INNOVATION_INTAKE, the query is handed to the Innovation Intake case flow "
            "instead of the static Rule R9 gate message. Omit to keep prior stateless behavior."
        )
    )
    user_id: str = Field(
        "anonymous_user",
        description="Phase 2 — caller identity for case ownership. Client-supplied until a real "
                     "auth system exists in this project."
    )
    mode: Optional[str] = Field(
        None,
        description="Operation mode: 'query' (direct statutory Q&A with Cohere and citations) or 'deep_research' (case intake, legal assessment & report generation)."
    )


class CitationSchema(BaseModel):
    statute: Optional[str] = None
    treaty: Optional[str] = None
    section: Optional[str] = None
    rule: Optional[str] = None
    article: Optional[str] = None
    jurisdiction: str = "national"
    official_url: str = ""
    title: str = ""
    summary: str = ""
    chunk_id: Optional[str] = None
    effective_date: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    jurisdiction: str
    answer: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: Optional[str] = "HIGH"
    citations: List[CitationSchema]
    formulation_category: Optional[str] = None
    is_abstained: bool = False
    escalate_to_human: bool = False
    abs_guidance: Optional[Dict[str, Any]] = None
    disclaimer: str
    anonymized_audit_ref: str

    # Phase 1 Intent + Entity Classification routing metadata
    intent: Optional[str] = None
    route: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    needs_clarification: Optional[bool] = False
    clarification_question: Optional[str] = None

    # Phase 2 Innovation Intake / Case metadata (present only when routed to a case)
    case_id: Optional[str] = None
    case_status: Optional[str] = None
    ready_for_research: Optional[bool] = None
    missing_information: Optional[List[str]] = None

    # Real-time backend execution logs for frontend terminal display
    execution_logs: Optional[List[str]] = Field(default_factory=list)

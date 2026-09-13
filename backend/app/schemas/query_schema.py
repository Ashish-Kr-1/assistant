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

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    query: str = Field(..., description="User's IPR or regulatory query in plain language.")
    jurisdiction: str = Field("national", description="Jurisdiction filter: 'national' (India) or 'international'.")
    language: str = Field("en", description="ISO language code (e.g., 'en', 'hi', 'ta', 'te').")
    dpdp_consent: bool = Field(True, description="Explicit user privacy consent under DPDP Act 2023.")

class CitationSchema(BaseModel):
    statute: Optional[str] = None
    treaty: Optional[str] = None
    section: Optional[str] = None
    rule: Optional[str] = None
    article: Optional[str] = None
    jurisdiction: str
    official_url: str
    title: str
    summary: str

class QueryResponse(BaseModel):
    query: str
    jurisdiction: str
    answer: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    citations: List[CitationSchema]
    formulation_category: Optional[str] = None
    disclaimer: str
    anonymized_audit_ref: str

"""Request/response models for the Charaka IP API."""

from typing import Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User's IP/Ayurveda question (any language).")
    jurisdiction: Literal["india", "international", "both"] = Field(
        default="both",
        description="Jurisdiction scope: 'india', 'international', or 'both' (default).",
    )


class ConnectorSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search term or phrase")
    connector: Literal["all", "wipo", "ip_india", "manupatra", "scc"] = Field(
        default="all",
        description="Target connector or 'all'",
    )
    jurisdiction: Literal["IN", "INTL", "BOTH"] = Field(
        default="BOTH",
        description="Jurisdiction filter: 'IN', 'INTL', or 'BOTH'",
    )


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to translate")
    source_lang: str = Field(default="hi", description="Source language ISO code")
    target_lang: str = Field(default="en", description="Target language ISO code")


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize to speech")
    target_lang: str = Field(default="hi", description="Language ISO code")
    gender: str = Field(default="female", description="'female' or 'male'")


class STTRequest(BaseModel):
    audio_base64: str = Field(..., min_length=1, description="Base64 encoded audio string")
    source_lang: str = Field(default="hi", description="Language ISO code")


class Source(BaseModel):
    number: int
    title: str
    url: str


class Confidence(BaseModel):
    level: str = Field(description="'HIGH', 'MEDIUM', 'LOW', or 'UNCERTAIN'.")
    score: float = Field(description="Numeric confidence 0.0–1.0.")
    reason: str = Field(description="Brief explanation of confidence level.")


class ABSChecklistStep(BaseModel):
    step_number: int
    title: str
    authority: str
    form: str | None = None
    mandatory: bool = True
    details: str


class ABSChecklist(BaseModel):
    applicable: bool
    summary: str
    steps: list[ABSChecklistStep] = Field(default_factory=list)
    benefit_sharing_framework: str
    portal_url: str = "https://nbaindia.org"


class TKDLAssessment(BaseModel):
    checked: bool
    identified_ingredients: list[str] = Field(default_factory=list)
    prior_art_risk: str
    risk_explanation: str
    matched_traditions: list[str] = Field(default_factory=list)
    section_3p_precaution: str
    recommended_strategy: str
    tkdl_database_url: str = "https://tkdl.res.in"


class FacilitatorContact(BaseModel):
    title: str = "IPO Registered Patent & Trademark Agent Directory"
    directory_url: str = "https://ipindia.gov.in"
    nba_helpdesk: str = "https://nbaindia.org"
    ayush_portal: str = "https://ayush.gov.in"
    advice: str = "For formal patent filing, statutory appeals, or ABS compliance, engage an authorized IP facilitator."


class AskResponse(BaseModel):
    answer: str = Field(description="Full cited answer with inline [n] markers, Sources section, and disclaimer.")
    sources: list[Source] = Field(description="Sources actually cited in the answer.")
    detected_language: str = Field(description="Detected language/script of the user's question.")
    english_query: str = Field(description="English search query used internally.")
    ip_type: str = Field(description="Detected IP domain: patent, trademark, gi, copyright, ayush, abs, tkdl, general.")
    jurisdiction: str = Field(description="Jurisdiction scope used: IN, INTL, or BOTH.")
    confidence: Confidence | None = Field(default=None, description="Answer confidence assessment.")
    escalation_recommended: bool = Field(default=False, description="True if human IP facilitator review is recommended.")
    escalation_reason: str | None = Field(default=None, description="Why escalation is recommended.")
    facilitator_contact: FacilitatorContact | None = Field(default=None, description="Directory and contact info for registered patent agents.")
    abs_checklist: ABSChecklist | None = Field(default=None, description="Structured step-by-step ABS compliance checklist under BDA 2002.")
    tkdl_assessment: TKDLAssessment | None = Field(default=None, description="Traditional Knowledge Digital Library prior-art risk assessment.")

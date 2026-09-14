"""
Innovation Intake & Case Schemas (Phase 2 — IP-SAKTI Sahayak PS045)
Defines the structured InnovationProfile, IntakeState, Case, and IntakeResponse
contracts. Phase 2 answers only "what exactly is the user's innovation?" — it
never contains a patentability, ABS-applicability, or compliance conclusion.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DevelopmentStage(str, Enum):
    IDEA = "IDEA"
    PROTOTYPE = "PROTOTYPE"
    RESEARCH = "RESEARCH"
    PILOT = "PILOT"
    COMMERCIAL = "COMMERCIAL"
    UNKNOWN = "UNKNOWN"


class IPObjective(str, Enum):
    PATENT = "PATENT"
    TRADEMARK = "TRADEMARK"
    COPYRIGHT = "COPYRIGHT"
    DESIGN = "DESIGN"
    TRADE_SECRET = "TRADE_SECRET"
    GI = "GI"
    PLANT_VARIETY = "PLANT_VARIETY"
    UNKNOWN = "UNKNOWN"


class TKBasis(str, Enum):
    CLASSICAL_TEXT = "CLASSICAL_TEXT"
    COMMUNITY_KNOWLEDGE = "COMMUNITY_KNOWLEDGE"
    TRADITIONAL_USE = "TRADITIONAL_USE"
    UNKNOWN = "UNKNOWN"
    NONE = "NONE"


class CommercialIntent(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    INDIA = "INDIA"
    EXPORT = "EXPORT"
    LICENSING = "LICENSING"
    MANUFACTURING = "MANUFACTURING"
    INVESTMENT = "INVESTMENT"
    UNKNOWN = "UNKNOWN"


class CaseStatus(str, Enum):
    INTAKE_IN_PROGRESS = "INTAKE_IN_PROGRESS"
    READY_FOR_RESEARCH = "READY_FOR_RESEARCH"
    ARCHIVED = "ARCHIVED"


class IntakeStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class FieldProvenance(str, Enum):
    """Tags whether a profile field came from the user's own words or was inferred."""
    USER_STATED = "USER_STATED"
    INFERRED = "INFERRED"


class BiologicalResource(BaseModel):
    """A single biological resource the user has stated is used. Facts only — no ABS conclusion."""
    model_config = ConfigDict(extra="forbid")

    common_name: Optional[str] = None
    scientific_name: Optional[str] = None
    part_used: Optional[str] = None
    source: Optional[str] = None
    geographical_origin: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    wild_or_cultivated: Optional[str] = None
    supplier: Optional[str] = None
    purpose_of_use: Optional[str] = None


class InnovationProfile(BaseModel):
    """
    Structured, factual record of the user's innovation.
    Only collects and structures facts — never a legal/regulatory conclusion.
    """
    model_config = ConfigDict(extra="forbid")

    # Basic Innovation
    innovation_name: Optional[str] = None
    short_description: Optional[str] = None
    problem_statement: Optional[str] = None
    proposed_solution: Optional[str] = None
    claimed_novelty: Optional[str] = None
    development_stage: DevelopmentStage = DevelopmentStage.UNKNOWN

    # Product
    product_type: Optional[str] = None
    product_name: Optional[str] = None
    dosage_form: Optional[str] = None
    intended_use: Optional[str] = None
    target_users: Optional[str] = None
    delivery_method: Optional[str] = None

    # Ayurvedic Formulation (only relevant to formulation-type cases)
    ingredients: List[str] = Field(default_factory=list)
    scientific_names: List[str] = Field(default_factory=list)
    quantities: List[str] = Field(default_factory=list)
    concentrations: List[str] = Field(default_factory=list)
    ingredient_ratios: Optional[str] = None
    extraction_method: Optional[str] = None
    processing_method: Optional[str] = None
    standardization: Optional[str] = None
    bioactive_markers: List[str] = Field(default_factory=list)
    excipients: List[str] = Field(default_factory=list)
    dosage: Optional[str] = None
    classical_reference: Optional[str] = None
    classical_text_name: Optional[str] = None
    novel_combination: Optional[bool] = None
    modified_ratio: Optional[bool] = None
    modified_process: Optional[bool] = None

    # Traditional Knowledge — user-stated facts only, never a legal TK determination
    tk_basis: TKBasis = TKBasis.UNKNOWN
    reference_text: Optional[str] = None
    reference_source: Optional[str] = None
    known_tkdl_reference: Optional[str] = None
    traditional_use_description: Optional[str] = None

    # Biological Resources — facts only, never an ABS determination
    biological_resources: List[BiologicalResource] = Field(default_factory=list)

    # IP Objective
    ip_objectives: List[IPObjective] = Field(default_factory=list)
    primary_ip_objective: Optional[IPObjective] = None
    secondary_ip_objectives: List[IPObjective] = Field(default_factory=list)

    # Commercialization
    commercial_intent: List[CommercialIntent] = Field(default_factory=list)
    target_markets: List[str] = Field(default_factory=list)

    # Jurisdictions — captured intent only, never an international legal analysis
    target_jurisdictions: List[str] = Field(default_factory=list)

    # Existing IP / Research
    existing_patent: Optional[bool] = None
    existing_prior_art_search: Optional[bool] = None
    existing_trademark_search: Optional[bool] = None
    professional_ip_report: Optional[bool] = None
    existing_application: Optional[bool] = None
    uploaded_documents: List[str] = Field(default_factory=list)

    # Field provenance: field_name -> USER_STATED | INFERRED
    field_provenance: Dict[str, FieldProvenance] = Field(default_factory=dict)


class IntakeState(BaseModel):
    """Explicit progressive-intake state machine."""
    model_config = ConfigDict(extra="forbid")

    status: IntakeStatus = IntakeStatus.NOT_STARTED
    current_section: Optional[str] = None
    completed_sections: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    next_question: Optional[str] = None
    # Tracks which field the last question targeted, so the next raw user
    # message can be attributed to that field deterministically.
    pending_field: Optional[str] = None
    # True when the assistant has asked "would you like to create a new case for
    # this invention?" and is waiting on a yes/no before creating or merging.
    awaiting_new_case_confirmation: bool = False


class Case(BaseModel):
    """Persistent Case record. Identity = user_id + conversation_id + case_id."""
    model_config = ConfigDict(extra="forbid")

    case_id: str
    user_id: str
    conversation_id: str
    title: Optional[str] = None
    status: CaseStatus = CaseStatus.INTAKE_IN_PROGRESS
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    profile: InnovationProfile = Field(default_factory=InnovationProfile)
    intake_state: IntakeState = Field(default_factory=IntakeState)


class IntakeResponse(BaseModel):
    """Standardized response contract for every Phase 2 intake code path."""
    model_config = ConfigDict(extra="forbid")

    case_id: str
    status: CaseStatus
    profile: InnovationProfile
    missing_information: List[str] = Field(default_factory=list)
    next_question: Optional[str] = None
    ready_for_research: bool = False
    message: Optional[str] = Field(
        None,
        description="Neutral assistant-facing text for this turn (the question, or a READY summary). Never a legal conclusion."
    )

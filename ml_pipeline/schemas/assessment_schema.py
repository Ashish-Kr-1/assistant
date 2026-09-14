"""
Phase 3 — Innovation Classification & Legal Domain Mapping (IP-SAKTI Sahayak PS045)

Defines the CaseAssessment schema produced by the Case Assessment Agent.

IMPORTANT: This schema captures PRELIMINARY GUIDANCE ONLY.
- Does NOT determine final patentability.
- Does NOT determine final ABS applicability.
- Does NOT perform actual legal research or prior-art searching.
- Does NOT query Qdrant or any external vector store.
- Does NOT constitute formal legal advice.

It transforms a structured InnovationProfile (from Phase 2) into a structured
preliminary assessment with IP domain classification, jurisdiction mapping,
regulatory pathway identification, and a research plan — ready for Phase 4 (CRAG).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── 3.1 Case Normalization ─────────────────────────────────────────────────

class CompletenessLevel(str, Enum):
    COMPLETE = "COMPLETE"
    ADEQUATE = "ADEQUATE"
    INCOMPLETE = "INCOMPLETE"


class NormalizedCase(BaseModel):
    """3.1 — Normalized, validated case summary extracted from InnovationProfile."""
    model_config = ConfigDict(extra="forbid")

    case_id: str
    innovation_name: Optional[str] = None
    short_description: Optional[str] = None
    product_type: Optional[str] = None
    ingredients_summary: List[str] = Field(default_factory=list)
    claimed_novelty: Optional[str] = None
    development_stage: Optional[str] = None
    tk_basis: Optional[str] = None
    ip_objectives: List[str] = Field(default_factory=list)
    target_jurisdictions: List[str] = Field(default_factory=list)
    completeness: CompletenessLevel = CompletenessLevel.ADEQUATE
    completeness_notes: List[str] = Field(default_factory=list)


# ── 3.2 Product / Formulation Classification ──────────────────────────────

class FormulationCategory(str, Enum):
    CLASSICAL_MEDICINE = "CLASSICAL_MEDICINE"
    PROPRIETARY_MEDICINE = "PROPRIETARY_MEDICINE"
    PHYTOPHARMACEUTICAL = "PHYTOPHARMACEUTICAL"
    AYURVEDA_AAHAR = "AYURVEDA_AAHAR"
    COSMETIC = "COSMETIC"
    NON_FORMULATION = "NON_FORMULATION"
    UNDETERMINED = "UNDETERMINED"


class ProductClassification(BaseModel):
    """3.2 — Product/formulation category with regulatory framework."""
    model_config = ConfigDict(extra="forbid")

    category: FormulationCategory = FormulationCategory.UNDETERMINED
    category_name: str = "Undetermined"
    description: str = ""
    regulatory_framework: str = ""
    confidence: float = 0.5
    classification_basis: str = ""  # What triggered this classification
    is_formulation_type: bool = False


# ── 3.3 IP Domain Classification ──────────────────────────────────────────

class IPDomainFlag(str, Enum):
    PATENT_BAR_LIKELY = "PATENT_BAR_LIKELY"
    PATENT_POSSIBLE = "PATENT_POSSIBLE"
    PATENT_STRONG = "PATENT_STRONG"
    TRADEMARK_PRIMARY = "TRADEMARK_PRIMARY"
    DESIGN_PROTECTION = "DESIGN_PROTECTION"
    GI_ELIGIBLE = "GI_ELIGIBLE"
    TRADE_SECRET = "TRADE_SECRET"
    UNCLEAR = "UNCLEAR"


class Section3PAnalysis(BaseModel):
    """Preliminary Section 3(p) bar analysis (not a legal determination)."""
    model_config = ConfigDict(extra="forbid")

    bar_likely: bool = False
    basis: str = ""
    notes: str = ""


class IPDomainClassification(BaseModel):
    """3.3 — IP domain mapping and preliminary barrier identification."""
    model_config = ConfigDict(extra="forbid")

    primary_ip_domain: IPDomainFlag = IPDomainFlag.UNCLEAR
    ip_domains_applicable: List[str] = Field(default_factory=list)
    ip_posture: str = ""
    section_3p_analysis: Section3PAnalysis = Field(default_factory=Section3PAnalysis)
    tkdl_relevance: bool = False
    tkdl_note: str = ""
    key_statutory_considerations: List[str] = Field(default_factory=list)


# ── 3.4 Jurisdiction & Regulatory Mapping ────────────────────────────────

class JurisdictionMapping(BaseModel):
    """A single jurisdiction's regulatory requirements."""
    model_config = ConfigDict(extra="forbid")

    jurisdiction: str
    regulatory_authority: str = ""
    applicable_frameworks: List[str] = Field(default_factory=list)
    required_licenses: List[str] = Field(default_factory=list)
    abs_applicable: bool = False
    abs_note: str = ""
    key_compliance_steps: List[str] = Field(default_factory=list)


class RegulatoryMapping(BaseModel):
    """3.4 — Multi-jurisdiction regulatory framework mapping."""
    model_config = ConfigDict(extra="forbid")

    jurisdiction_maps: List[JurisdictionMapping] = Field(default_factory=list)
    international_treaties: List[str] = Field(default_factory=list)
    abs_posture: str = ""
    export_considerations: List[str] = Field(default_factory=list)


# ── 3.5 Research Plan Generation ──────────────────────────────────────────

class ResearchPriorityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ResearchTask(BaseModel):
    """A single prioritized research task."""
    model_config = ConfigDict(extra="forbid")

    task_id: str
    priority: ResearchPriorityLevel
    category: str  # e.g. "PRIOR_ART", "REGULATORY", "ABS", "TK_DOCUMENTATION"
    title: str
    description: str
    statutory_basis: str = ""
    estimated_effort: str = ""  # e.g. "1-2 weeks"


class ResearchPlan(BaseModel):
    """3.5 — Prioritized research plan for Phase 4 CRAG engine."""
    model_config = ConfigDict(extra="forbid")

    research_tasks: List[ResearchTask] = Field(default_factory=list)
    recommended_crag_queries: List[str] = Field(default_factory=list)
    recommended_jurisdiction: str = "national"
    recommended_ip_domains: List[str] = Field(default_factory=list)
    immediate_next_steps: List[str] = Field(default_factory=list)


# ── Top-level Assessment ──────────────────────────────────────────────────

class AssessmentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CaseAssessment(BaseModel):
    """
    Full Phase 3 structured assessment of an Innovation Case.
    Produced deterministically from InnovationProfile — no LLM, no Qdrant.
    """
    model_config = ConfigDict(extra="forbid")

    case_id: str
    assessment_status: AssessmentStatus = AssessmentStatus.PENDING
    assessed_at: Optional[datetime] = None
    
    # 3.1
    normalized: Optional[NormalizedCase] = None
    # 3.2
    product_classification: Optional[ProductClassification] = None
    # 3.3
    ip_domain: Optional[IPDomainClassification] = None
    # 3.4
    regulatory_mapping: Optional[RegulatoryMapping] = None
    # 3.5
    research_plan: Optional[ResearchPlan] = None

    # Human-readable executive summary for the frontend
    executive_summary: str = ""
    key_risks: List[str] = Field(default_factory=list)
    key_opportunities: List[str] = Field(default_factory=list)

    DISCLAIMER: str = (
        "This is a PRELIMINARY GUIDANCE ONLY — not a legal determination. "
        "Patentability, ABS applicability, and regulatory compliance must be confirmed "
        "by a qualified IP attorney or registered Patent Agent. "
        "This report does not constitute formal legal advice."
    )

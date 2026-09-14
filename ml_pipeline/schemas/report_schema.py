"""
Phase 4 — Research Engine & Report Generator (IP-SAKTI Sahayak PS045)

Defines the CaseReport schema produced by the ResearchEngine: it executes the
Phase 3 ResearchPlan's `recommended_crag_queries` through the existing CRAG
pipeline (Qdrant + Cohere + CRAG grading/verification/abstention — no new
retrieval infrastructure), aggregates the results into evidence, computes a
structured risk assessment, and assembles a preliminary, source-cited report.

IMPORTANT CONSTRAINTS:
- No new retrieval/embedding infrastructure — reuses ml_pipeline.crag.graph.CRAGPipeline.
- No fabricated citations — every Evidence entry traces back to a CRAG citation
  that already passed grading + entailment verification (Rules R1-R3).
- Risk levels and confidence are AI-assisted research signals, not legal opinions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceTier(str, Enum):
    TIER_1 = "TIER_1"  # Official government/statutory/regulatory/treaty sources (WIPO, WTO, CBD, AYUSH, gov gazettes)
    TIER_2 = "TIER_2"  # Official treaty/convention documents, official gazettes
    TIER_3 = "TIER_3"  # Recognized legal databases/repositories (e.g. Indian Kanoon)
    TIER_4 = "TIER_4"  # Secondary commentary
    TIER_5 = "TIER_5"  # Blogs / general web
    UNKNOWN = "UNKNOWN"


class Evidence(BaseModel):
    """A single evidence object backing (or explicitly failing to back) a research finding."""
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    claim: str = ""
    source: str = ""
    source_type: str = ""
    title: str = ""
    official_url: str = ""
    jurisdiction: str = ""
    domain: str = ""
    act_name: Optional[str] = None
    section_id: Optional[str] = None
    effective_date: Optional[str] = None
    text_snippet: str = ""
    relevance_score: float = 0.0
    source_tier: SourceTier = SourceTier.UNKNOWN
    retrieval_method: str = "crag_hybrid_mmr"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class RiskItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk: str  # e.g. PATENT_NOVELTY, TRADITIONAL_KNOWLEDGE, BIODIVERSITY_ABS, REGULATORY, EVIDENCE_GAP ...
    level: RiskLevel = RiskLevel.UNKNOWN
    reason: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    mitigation: str = ""
    requires_human_review: bool = False


class ResearchQueryResult(BaseModel):
    """Result of executing one Phase 3 recommended_crag_query through the CRAG pipeline."""
    model_config = ConfigDict(extra="forbid")

    task_id: Optional[str] = None
    query: str
    jurisdiction: str
    domain: str = ""
    is_abstained: bool = False
    confidence_score: float = 0.0
    confidence_level: str = "LOW"
    answer: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    escalate_to_human: bool = False


class HumanEscalationPackage(BaseModel):
    """Section 29 — structured escalation package when human review is required."""
    model_config = ConfigDict(extra="forbid")

    triggered: bool = False
    reasons: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    documents_needed: List[str] = Field(default_factory=list)


class CaseReport(BaseModel):
    """
    Phase 4 — Full structured, evidence-backed, source-cited preliminary
    IP/regulatory research report for an Innovation Case.
    """
    model_config = ConfigDict(extra="forbid")

    case_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Report sections (Section 20 numbering, human-readable Markdown)
    executive_summary: str = ""
    innovation_profile_summary: str = ""
    user_objective: str = ""
    classification_section: str = ""
    ip_domain_section: str = ""
    patent_prior_art_section: str = ""
    tk_section: str = ""
    abs_section: str = ""
    regulatory_section: str = ""
    trademark_section: str = ""
    international_section: str = ""
    evidence_gaps_section: str = ""
    next_steps_section: str = ""
    human_review_section: str = ""
    sources_section: str = ""

    research_results: List[ResearchQueryResult] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    evidence_gaps: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    human_review: HumanEscalationPackage = Field(default_factory=HumanEscalationPackage)

    needs_human_review: bool = False
    overall_confidence_level: str = "LOW"  # retrieval_relevance-derived, distinct from classification_confidence

    report_markdown: str = ""

    DISCLAIMER: str = (
        "This is an AI-assisted PRELIMINARY RESEARCH REPORT ONLY — not a legal determination "
        "or formal legal advice. Patentability, ABS applicability, and regulatory compliance "
        "must be confirmed by a qualified IP attorney, registered Patent Agent, or regulatory "
        "professional before any filing or commercial decision."
    )

"""
CRAG Schema Definitions (Charaka IP PS045)
Defines data structures for Legal Chunks, Grader Outcomes, Verification,
State Models, and Guardrails (R1-R10).
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProvenanceStatus(str, Enum):
    """Corpus provenance labeling (Rule R7)."""
    VERIFIED_PUBLIC = "verified_public"
    VERIFIED_PAID = "verified_paid"
    MOCK_PENDING_ACCESS = "mock_pending_access"


class JurisdictionType(str, Enum):
    """Jurisdiction separation (Rule R4)."""
    NATIONAL = "national"
    INDIA = "india"
    INTERNATIONAL = "international"
    BOTH = "both"

    @classmethod
    def from_str(cls, val: Any) -> "JurisdictionType":
        if isinstance(val, cls):
            return val
        s = str(val).strip().lower()
        if s in ("india", "national", "domestic"):
            return cls.NATIONAL
        if s in ("international", "global", "treaty"):
            return cls.INTERNATIONAL
        if s in ("both", "all", "cross"):
            return cls.BOTH
        return cls(s)


class IPType(str, Enum):
    """IP Category classification."""
    PATENT = "patent"
    BIODIVERSITY_ABS = "biodiversity_abs"
    DRUG_REGULATORY = "drug_regulatory"
    TRADEMARK_GI = "trademark_gi"
    COPYRIGHT = "copyright"
    GENERAL = "general"


class GradingOutcome(str, Enum):
    """CRAG Relevance Grader Outcomes."""
    CORRECT = "CORRECT"
    AMBIGUOUS = "AMBIGUOUS"
    INCORRECT = "INCORRECT"


class EntailmentResult(str, Enum):
    """Citation Entailment Verification Outcomes (Rule R3)."""
    YES = "YES"
    NO = "NO"
    PARTIAL = "PARTIAL"


class ConfidenceLevel(str, Enum):
    """Mandatory confidence level on answers (Rule R8)."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class LegalChunk(BaseModel):
    """
    Statutory or Treaty Chunk with structured legal metadata (Rule R7, R10).
    """
    chunk_id: str = Field(description="Unique deterministic ID, e.g., patents_act_1970_sec_3p")
    source: str = Field(description="Originating authority, e.g., 'India Code', 'WIPO Lex'")
    act_name: str = Field(description="Official name of the statute, treaty, or gazette")
    section_id: str = Field(description="Specific section, rule, or article boundary, e.g., 'Section 3(p)'")
    jurisdiction: JurisdictionType = Field(description="National (India) or International regime")
    effective_date: str = Field(description="Effective date or last amended date for version tracking (Rule R10)")
    ip_type: IPType = Field(default=IPType.GENERAL, description="Sub-corpus classification")
    status: ProvenanceStatus = Field(
        default=ProvenanceStatus.VERIFIED_PUBLIC,
        description="Corpus provenance status. Mock data excluded from CORRECT pool (Rule R7)"
    )
    official_url: Optional[str] = Field(default=None, description="Direct URL to official gazette or treaty text")
    text: str = Field(description="Verbatim legal text content of this section/article")


class GradedChunk(BaseModel):
    """Result of CRAG relevance grading on a single chunk."""
    chunk: LegalChunk
    outcome: GradingOutcome
    reason: str = Field(description="Brief justification for the grade")


class ClaimVerification(BaseModel):
    """Verification of a specific factual/statutory claim against a cited chunk (Rule R3)."""
    claim_text: str = Field(description="The specific claim sentence extracted from generated text")
    cited_chunk_id: str = Field(description="ID of the cited source chunk")
    entailment: EntailmentResult = Field(description="Whether the chunk actually entails the claim")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    reason: str = Field(description="Reasoning behind the entailment decision")


class ABSFlag(BaseModel):
    """Biological Diversity Act (ABS) structured lookup flag (CRAG.md §3.6)."""
    triggered: bool = False
    botanical_name: Optional[str] = None
    statutory_basis: str = "Biological Diversity Act, 2002 (as amended 2023)"
    benefit_sharing_slab: Optional[str] = None
    guidance_note: str = ""
    form_required: Optional[str] = None


class CRAGState(BaseModel):
    """
    Complete state passed across LangGraph nodes.
    """
    query: str
    jurisdiction: JurisdictionType = JurisdictionType.NATIONAL
    formulation_category: Optional[str] = None
    formulation_classified: bool = False

    # Retrieval & Grading
    retrieved_chunks: List[LegalChunk] = Field(default_factory=list)
    graded_chunks: List[GradedChunk] = Field(default_factory=list)
    correct_chunks: List[LegalChunk] = Field(default_factory=list)
    fallback_triggered: bool = False

    # Generation & Verification
    generated_answers: Dict[str, str] = Field(default_factory=dict)
    verifications: List[ClaimVerification] = Field(default_factory=list)

    # Safe Abstention & Guardrails
    is_abstained: bool = False
    confidence_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    abs_pointer: Optional[ABSFlag] = None
    
    # Final Output Object
    final_output: Dict[str, Any] = Field(default_factory=dict)

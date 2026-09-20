"""
Intent and Entity Classification Schemas (Phase 1 — Charaka IP PS045)
Defines the canonical enums, entity extraction models, route mappings,
and final IntentResult contract.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Intent(str, Enum):
    """Canonical Intent Taxonomy for Phase 1."""
    CHAT = "CHAT"
    LEGAL_QA = "LEGAL_QA"
    LEGAL_CASE_QUERY = "LEGAL_CASE_QUERY"
    IP_PROTECTION = "IP_PROTECTION"
    PATENT_RESEARCH = "PATENT_RESEARCH"
    REGULATORY_ASSESSMENT = "REGULATORY_ASSESSMENT"
    ABS_ASSESSMENT = "ABS_ASSESSMENT"
    TK_ASSESSMENT = "TK_ASSESSMENT"
    INTERNATIONAL_ASSESSMENT = "INTERNATIONAL_ASSESSMENT"
    INNOVATION_ASSESSMENT = "INNOVATION_ASSESSMENT"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNKNOWN = "UNKNOWN"


class Route(str, Enum):
    """Canonical Downstream Route Taxonomy."""
    CHAT = "CHAT"
    CRAG = "CRAG"
    INNOVATION_INTAKE = "INNOVATION_INTAKE"
    RESEARCH = "RESEARCH"
    CLARIFICATION = "CLARIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


# Strict deterministic mapping from Intent to Route
INTENT_TO_ROUTE: Dict[Intent, Route] = {
    Intent.CHAT: Route.CHAT,
    Intent.LEGAL_QA: Route.CRAG,
    Intent.LEGAL_CASE_QUERY: Route.CRAG,
    Intent.IP_PROTECTION: Route.INNOVATION_INTAKE,
    Intent.PATENT_RESEARCH: Route.INNOVATION_INTAKE,
    Intent.INNOVATION_ASSESSMENT: Route.INNOVATION_INTAKE,
    Intent.REGULATORY_ASSESSMENT: Route.RESEARCH,
    Intent.ABS_ASSESSMENT: Route.RESEARCH,
    Intent.TK_ASSESSMENT: Route.RESEARCH,
    Intent.INTERNATIONAL_ASSESSMENT: Route.RESEARCH,
    Intent.UNKNOWN: Route.CLARIFICATION,
    Intent.OUT_OF_SCOPE: Route.OUT_OF_SCOPE,
}


class Entities(BaseModel):
    """Routing-level extracted entities (Phase 1 scope only)."""
    product_type: Optional[str] = None
    object_type: Optional[str] = None
    ip_type: Optional[str] = None
    domain: Optional[str] = None
    jurisdiction: Optional[str] = None
    jurisdictions: List[str] = Field(default_factory=list)
    act: Optional[str] = None
    section: Optional[str] = None
    product_name: Optional[str] = None
    ingredient_names: List[str] = Field(default_factory=list)
    requested_action: Optional[str] = None


class IntentResult(BaseModel):
    """
    Standardized Output Contract for Phase 1.
    All classification pathways (Deterministic or LLM) must return this exact structure.
    """
    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)
    route: Route
    entities: Entities = Field(default_factory=Entities)
    requires_case: bool = False
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    method: str = Field(default="RULE", description="'RULE' for deterministic, 'LLM' for model fallback")


def resolve_route(intent: Intent) -> Route:
    """Resolves Route from Intent according to statutory system mapping."""
    return INTENT_TO_ROUTE.get(intent, Route.CLARIFICATION)

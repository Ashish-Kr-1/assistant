"""
knowledge_graph/schema.py — Node and Edge schemas for the Charaka IP Knowledge Graph.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    STATUTE = "statute"             # e.g., "Patents Act 1970", "Biological Diversity Act 2002"
    SECTION = "section"             # e.g., "Section 3(p)", "Section 6"
    RULE = "rule"                   # e.g., "Rule 158-B", "Patent Rules 2003"
    TREATY = "treaty"               # e.g., "TRIPS Agreement", "Nagoya Protocol"
    ARTICLE = "article"             # e.g., "TRIPS Article 27", "Nagoya Protocol Article 5"
    AUTHORITY = "authority"         # e.g., "National Biodiversity Authority (NBA)", "IPO"
    DATABASE = "database"           # e.g., "TKDL", "InPASS", "WIPO Lex"
    CONCEPT = "concept"             # e.g., "Traditional Knowledge", "Prior Art", "Benefit Sharing"
    FORM = "form"                   # e.g., "Form 1", "NBA Form III"


class EdgeType(str, Enum):
    CONTAINS = "contains"                     # Statute -> Section
    REQUIRES_CLEARANCE = "requires_clearance" # Section -> Authority / Form
    CITES = "cites"                           # Section -> Case / Section
    IS_PRIOR_ART_FOR = "is_prior_art_for"     # TKDL / Database -> Section
    IMPLEMENTS = "implements"                 # Statute -> Treaty
    EXCLUDES = "excludes"                     # Section -> Concept (patentability exclusion)
    REGULATES = "regulates"                   # Authority / Rule -> Concept
    COMPLIES_WITH = "complies_with"           # Rule -> Statute
    MANDATES_DISCLOSURE = "mandates_disclosure" # Section -> Authority / Requirement


class KGNode(BaseModel):
    id: str = Field(description="Unique node identifier, e.g., 'IN_PATENTS_ACT_1970', 'SEC_3P'")
    name: str = Field(description="Human-readable title/name")
    node_type: NodeType
    jurisdiction: str = Field(default="IN", description="'IN' or 'INTL'")
    ip_type: str = Field(default="general", description="patent, abs, ayush, trademark, gi, copyright, tkdl")
    description: str = Field(default="", description="Detailed statutory text or summary")
    citation: str = Field(default="", description="Authoritative reference or URL")
    metadata: dict[str, Any] = Field(default_factory=dict)


class KGEdge(BaseModel):
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    edge_type: EdgeType
    description: str = Field(default="", description="Relationship explanation")
    mandatory: bool = Field(default=False, description="Whether this relationship is legally mandatory")

from pydantic import BaseModel, Field
from typing import List, Optional


class ClassificationRequest(BaseModel):
    """
    Unified Classification Request schema.
    Supports both:
    1. Phase 1 Intent + Entity Classification (via `message`)
    2. Ayurvedic Formulation 5-tier Wizard (via `is_in_first_schedule`, etc.)
    """
    message: Optional[str] = Field(None, description="Free-text user message for Phase 1 intent and entity classification.")
    is_in_first_schedule: Optional[bool] = Field(None, description="Is formulation in First Schedule text (e.g. Charaka Samhita)?")
    uses_modified_ratio_or_novel_combo: bool = Field(False, description="Are ingredient ratios modified or novel ingredients added?")
    is_standardized_extract: bool = Field(False, description="Is it a standardized active fraction extract with marker compounds?")
    intended_for_food: bool = Field(False, description="Is it intended as food supplement / nutraceutical?")
    intended_for_cosmetic: bool = Field(False, description="Is it intended for beautification / cosmetic use?")


class ClassificationResponse(BaseModel):
    category_code: str
    category_name: str
    description: str
    regulatory_framework: str
    ip_posture: str
    abs_posture: str
    required_evidence: str
    next_steps: List[str]

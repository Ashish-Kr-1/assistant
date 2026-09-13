"""
Ayurvedic Formulation Classifier Agent (CRAG.md §3.2, Rule R9).
Implements the interactive 5-tier classification decision engine:
1. Classical / Generic (First Schedule texts)
2. Patent & Proprietary (P&P) Medicine
3. Phytopharmaceutical Drug (Rule 122E)
4. Ayurveda-Aahar (Nutraceutical)
5. Cosmetic (Cosmetic Rules 2020)
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class FormulationClassificationResult(BaseModel):
    category: str = Field(description="One of: classical_generic, patent_and_proprietary, phytopharmaceutical, ayurveda_aahar, cosmetic, ambiguous")
    confidence: float = Field(ge=0.0, le=1.0)
    statutory_governance: str
    ip_bar_flag: Optional[str] = None
    clarifying_question: Optional[str] = None
    recommended_pathway: str


class FormulationClassifierAgent:
    """
    Classifies Ayurvedic products into statutory buckets and identifies Section 3(p) barriers.
    """

    CLASSICAL_TEXTS = [
        "charaka samhita", "sushruta samhita", "ashtanga hridaya", "ashtanga sangraha",
        "sahasrayoga", "sharngadhara samhita", "bhavaprakasha", "bhesajjakkhandhaka",
        "ayurvedic formulary of india", "afi", "ayurvedic pharmacopoeia of india", "api"
    ]

    @classmethod
    def classify(cls, description: str, text_reference: Optional[str] = None) -> FormulationClassificationResult:
        desc_lower = description.lower()
        ref_lower = (text_reference or "").lower()

        # Check Phytopharmaceutical
        if any(k in desc_lower for k in ["fraction", "phytopharmaceutical", "bioactive marker", "four markers", "purified fraction", "standardized fraction"]):
            return FormulationClassificationResult(
                category="phytopharmaceutical",
                confidence=0.95,
                statutory_governance="Drugs and Cosmetics Rules, 1945 — Rule 122E (CDSCO)",
                ip_bar_flag=None,
                recommended_pathway=(
                    "Eligible for strong patent protection (composition of matter or process). "
                    "Requires IND application, Phase I-III clinical trials under CDSCO."
                )
            )

        # Check Ayurveda Aahar
        if any(k in desc_lower for k in ["food", "supplement", "nutraceutical", "aahar", "dietary", "beverage", "candy", "cookie"]):
            return FormulationClassificationResult(
                category="ayurveda_aahar",
                confidence=0.92,
                statutory_governance="Food Safety and Standards (Ayurveda Aahar) Regulations, 2022",
                ip_bar_flag="No therapeutic or disease claims permitted; trade dress and trademark protection only.",
                recommended_pathway=(
                    "FSSAI license with dedicated Ayurveda Aahar logo. "
                    "Cannot contain synthetic vitamins or minerals."
                )
            )

        # Check Cosmetic
        if any(k in desc_lower for k in ["cosmetic", "shampoo", "cream", "lotion", "serum", "hair oil", "skin glow", "soap"]):
            return FormulationClassificationResult(
                category="cosmetic",
                confidence=0.90,
                statutory_governance="Cosmetics Rules, 2020 under Drugs & Cosmetics Act",
                ip_bar_flag="Formulation patent barred if simple herbal blend; trademark/design protection primary.",
                recommended_pathway="Form 32 cosmetic manufacturing license; Bureau of Indian Standards (BIS) compliance."
            )

        # Check Classical Generic
        is_classical = any(t in desc_lower or t in ref_lower for t in cls.CLASSICAL_TEXTS) or "classical" in desc_lower
        if is_classical or any(f in desc_lower for f in ["churna", "asava", "arishta", "taila", "bhasma", "kwatha", "avaleha", "vati", "guggulu", "triphala", "chyawanprash"]):
            if "modified" not in desc_lower and "novel ratio" not in desc_lower:
                return FormulationClassificationResult(
                    category="classical_generic",
                    confidence=0.96,
                    statutory_governance="Drugs and Cosmetics Act, 1940 — Section 3(a) & First Schedule Authoritative Texts",
                    ip_bar_flag="Absolute Patent Bar under Section 3(p) of The Patents Act 1970 (Traditional Knowledge).",
                    recommended_pathway=(
                        "Manufacture under Classical AYUSH Drug License. Cannot be patented. "
                        "Protected against biopiracy via CSIR-TKDL."
                    )
                )

        # Check Patent & Proprietary (P&P)
        if any(k in desc_lower for k in ["proprietary", "modified", "novel combination", "synergistic", "extract blend", "new ratio"]):
            return FormulationClassificationResult(
                category="patent_and_proprietary",
                confidence=0.88,
                statutory_governance="Drugs and Cosmetics Rules, 1945 — Rule 158B (AYUSH SLA)",
                ip_bar_flag="Vulnerable to Section 3(d) (enhanced efficacy requirement) and Section 3(e) (mere admixture bar).",
                recommended_pathway=(
                    "Requires pilot clinical safety/toxicity data under Rule 158B. "
                    "Patenting requires demonstrating unexpected synergistic efficacy beyond known textbook properties."
                )
            )

        # Ambiguous case: Needs clarifying questions
        return FormulationClassificationResult(
            category="ambiguous",
            confidence=0.40,
            statutory_governance="Undetermined",
            clarifying_question=(
                "To determine your exact IP protection pathway and Section 3(p) risk: "
                "Is this formulation drawn verbatim from an authoritative Ayurvedic text (e.g. Charaka Samhita), "
                "or is it a novel proprietary combination/standardized extract?"
            ),
            recommended_pathway="Clarification required before formal legal routing (Rule R9)."
        )

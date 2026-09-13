"""
Ayurvedic Formulation Classifier Agent (CRAG.md §3.2, Rule R9).
Implements the interactive 5-tier classification decision engine from free-text
product descriptions, feeding the CRAG pipeline's R9 classification gate:
1. Classical / Generic (First Schedule texts)
2. Patent & Proprietary (P&P) Medicine
3. Phytopharmaceutical Drug (Rule 122E)
4. Ayurveda-Aahar (Nutraceutical)
5. Cosmetic (Cosmetic Rules 2020)

Statutory/IP/ABS metadata for each category lives in formulation_taxonomy.py —
the same table backend/app/services/classification_service.py reads for the
structured wizard, so the two entry points can't disagree on the underlying law.
"""

from typing import Optional
from pydantic import BaseModel, Field

from ml_pipeline.agents.formulation_taxonomy import CATEGORY_METADATA


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

    # Authoritative texts recognized under Drugs & Cosmetics Act First Schedule and FSSAI October 2024 Compendium (71 texts)
    CLASSICAL_TEXTS = [
        # Major Brihat Trayi & Laghu Trayi
        "charaka samhita", "sushruta samhita", "ashtanga hridaya", "ashtanga sangraha",
        "sharngadhara samhita", "sharangadhara samhita", "bhavaprakasha", "bhava prakasha",
        "madhava nidana", "sahasrayoga", "bhaishajya ratnavali", "yoga ratnakara",
        # First Schedule Statutory Authoritative Texts (Drugs & Cosmetics Act 1940)
        "arogya kalpadruma", "arka prakasha", "arya bhishak", "ayurveda kalpadruma",
        "ayurveda prakasha", "ayurveda samgraha", "ayurveda chintamani", "abhinava chintamani",
        "ayurveda ratnakar", "bharat bhaishajya ratnakara", "brihat nighantu ratnakara",
        "chakra datta", "chakradatta", "dravyaguna vijnana", "gada nigraha", "gadanigraha",
        "harita samhita", "kashyapa samhita", "bhel samhita", "kupi-pakva rasayana",
        "nighantu ratnakara", "rasa chandanshu", "rasa manjari", "rasa maramritam",
        "rasa prakasha sudhakara", "rasa ratna samuccaya", "rasaratna samuccaya",
        "rasa raja sundara", "rasa tarangini", "rasatarangini", "rasa yoga sagara",
        "rasendra sara samgraha", "rasamrita", "sarva-roga chintamani", "sarvaroga chintamani",
        "vaidya chintamani", "vaidyaka shabda sindhu", "vaidyaka chikitsa sara",
        "vaidya jiwan", "vasava rajiyam", "yoga tarangini", "yoga chintamani",
        "yoga ratnasamgraha", "vishwanath chikitsa", "vrinda chikitsa", "siddha yoga",
        "vangasena", "bhesajjakkhandhaka", "parada samhita", "pathyapathya vinishchaya",
        "siddha bhesaja manimala", "ayurveda saura", "rasapaddhati", "rasendra chintamani",
        "rasendra kalpadruma", "dhanvantari nighantu", "raja nighantu", "shodhala nighantu",
        "kaiyadeva nighantu", "saligram nighantu", "priya nighantu", "hridaya dipaka nighantu",
        "siddhapradipika", "vaidya manorama", "chikitsa kalika", "chikitsa sara samgraha",
        "brihadyoga tarangini", "kalyana karaka", "arka kalpa", "aupadhenava",
        # Official pharmacopoeial compendia
        "ayurvedic formulary of india", "afi", "ayurvedic pharmacopoeia of india", "api",
        "fssai october 2024 compendium", "fssai ayurveda aahara compendium"
    ]

    @classmethod
    def _result_for(cls, category_code: str, **overrides) -> FormulationClassificationResult:
        """Builds a FormulationClassificationResult from the shared taxonomy table."""
        meta = CATEGORY_METADATA[category_code]
        return FormulationClassificationResult(
            category=meta["text_category"],
            confidence=meta["confidence"],
            statutory_governance=meta["regulatory_framework"],
            ip_bar_flag=meta["ip_posture"],
            recommended_pathway=meta["recommended_pathway"],
            **overrides,
        )

    @classmethod
    def classify(cls, description: str, text_reference: Optional[str] = None) -> FormulationClassificationResult:
        desc_lower = description.lower()
        ref_lower = (text_reference or "").lower()

        # Check Phytopharmaceutical
        if any(k in desc_lower for k in ["fraction", "phytopharmaceutical", "bioactive marker", "four markers", "purified fraction", "standardized fraction"]):
            return cls._result_for("PHYTOPHARMACEUTICAL")

        # Check Ayurveda Aahar / Nutraceutical
        if any(k in desc_lower for k in ["food", "supplement", "nutraceutical", "aahar", "dietary", "beverage", "candy", "cookie"]):
            return cls._result_for("AYURVEDA_AAHAR")

        # Check Cosmetic
        if any(k in desc_lower for k in ["cosmetic", "shampoo", "cream", "lotion", "serum", "hair oil", "skin glow", "soap"]):
            return cls._result_for("COSMETIC")

        # Check Classical Generic
        is_classical = any(t in desc_lower or t in ref_lower for t in cls.CLASSICAL_TEXTS) or "classical" in desc_lower
        if is_classical or any(f in desc_lower for f in ["churna", "asava", "arishta", "taila", "bhasma", "kwatha", "avaleha", "vati", "guggulu", "triphala", "chyawanprash"]):
            if "modified" not in desc_lower and "novel ratio" not in desc_lower:
                return cls._result_for("CLASSICAL_MEDICINE")

        # Check Patent & Proprietary (P&P)
        if any(k in desc_lower for k in ["proprietary", "modified", "novel combination", "synergistic", "extract blend", "new ratio"]):
            return cls._result_for("PROPRIETARY_MEDICINE")

        # Ambiguous case: Needs clarifying questions
        return FormulationClassificationResult(
            category="ambiguous",
            confidence=0.40,
            statutory_governance="Undetermined",
            recommended_pathway="Clarification required before formal legal routing (Rule R9).",
            clarifying_question=(
                "To determine your exact IP protection pathway and Section 3(p) risk: "
                "Is this formulation drawn verbatim from an authoritative Ayurvedic text (e.g. Charaka Samhita), "
                "or is it a novel proprietary combination/standardized extract?"
            ),
        )

from typing import Dict, Any

from ml_pipeline.agents.formulation_taxonomy import CATEGORY_METADATA


class AyurvedicFormulationClassifier:
    """
    Formulation Classifier Engine for Ayurvedic Products (structured wizard).
    Evaluates regulatory category, IP posture (Sec 3(p) TK bar, TKDL), and ABS requirements.

    Statutory/IP/ABS metadata is read from ml_pipeline.agents.formulation_taxonomy —
    the same table ml_pipeline/agents/classifier_agent.py reads for free-text
    classification inside the CRAG pipeline's R9 gate, so a product can't be told
    a different statutory story depending on which endpoint classified it.
    """

    @classmethod
    def classify(cls, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies product based on decision tree answers.

        Expected answers keys:
        - is_in_first_schedule: bool
        - uses_modified_ratio_or_novel_combo: bool
        - is_standardized_extract: bool
        - intended_for_food: bool
        - intended_for_cosmetic: bool
        """
        if answers.get("is_standardized_extract"):
            category_code = "PHYTOPHARMACEUTICAL"
        elif answers.get("intended_for_food"):
            category_code = "AYURVEDA_AAHAR"
        elif answers.get("intended_for_cosmetic"):
            category_code = "COSMETIC"
        elif answers.get("is_in_first_schedule") and not answers.get("uses_modified_ratio_or_novel_combo"):
            category_code = "CLASSICAL_MEDICINE"
        else:
            category_code = "PROPRIETARY_MEDICINE"

        meta = CATEGORY_METADATA[category_code]
        return {
            "category_code": category_code,
            "category_name": meta["name"],
            "description": meta["description"],
            "regulatory_framework": meta["regulatory_framework"],
            "ip_posture": meta["ip_posture"],
            "abs_posture": meta["abs_posture"],
            "required_evidence": meta["required_evidence"],
            "next_steps": meta["next_steps"],
        }

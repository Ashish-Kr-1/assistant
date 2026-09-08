from typing import Dict, Any, List

class AyurvedicFormulationClassifier:
    """
    Formulation Classifier Engine for Ayurvedic Products.
    Evaluates regulatory category, IP posture (Sec 3(p) TK bar, TKDL), and ABS requirements.
    """

    CATEGORIES = {
        "CLASSICAL_MEDICINE": {
            "name": "Classical / Generic Ayurvedic Medicine",
            "description": "Formulation and process described in First-Schedule authoritative texts (e.g. Charaka Samhita, Sharangadhara Samhita).",
            "regulatory_framework": "Drugs & Cosmetics Act 1940, Schedule T (GMP)",
            "ip_posture": "Faces Section 3(p) Patenting Bar (Traditional Knowledge). Protected by TKDL defense against foreign misappropriation.",
            "abs_posture": "Exempt from ABS benefit-sharing for Indian AYUSH practitioners, but commercial manufacturers using biological resources require NBA compliance.",
            "required_evidence": "Strict compliance with Pharmacopoeial Standards (API / AFI)."
        },
        "PROPRIETARY_MEDICINE": {
            "name": "Patent or Proprietary Medicine (Ayurvedic)",
            "description": "Formulation contains ingredients specified in authoritative texts, but uses modified ratios, novel combinations, or modern dosage forms.",
            "regulatory_framework": "Drugs & Cosmetics Act Section 3(a), Rule 158B",
            "ip_posture": "Patentable subject to proving non-obvious inventive step over prior art (Sec 3(p) & Sec 3(d) non-obviousness test).",
            "abs_posture": "Commercial exploitation of biological resources requires prior notification/approval from SBB/NBA (Form I). Benefit-sharing applies.",
            "required_evidence": "Safety and efficacy data as prescribed under Rule 158B."
        },
        "PHYTOPHARMACEUTICAL": {
            "name": "Phytopharmaceutical Drug",
            "description": "Standardized fraction (extract) containing at least 4 active marker compounds derived from a medicinal plant.",
            "regulatory_framework": "Drugs & Cosmetics Rules, Rule 122E (New Drug Category)",
            "ip_posture": "Strong patent potential for novel process of extraction, standardized composition, and therapeutic indication.",
            "abs_posture": "Strict NBA approval required (Form I for Indian entity, Form III for foreign IP transfer). Benefit sharing mandatory under BDA 2023.",
            "required_evidence": "Full clinical trials (Phase I-III), fingerprinting, safety profiles equivalent to new chemical entities."
        },
        "AYURVEDA_AAHAR": {
            "name": "Ayurveda-Aahar / Food Supplement",
            "description": "Food products prepared in accordance with recipes or ingredients specified in authoritative Ayurvedic books.",
            "regulatory_framework": "FSSAI (Ayurveda Aahar) Regulations 2022",
            "ip_posture": "Process/recipe patents rare (Sec 3(e) admixture bar). GI and Trademark protection recommended.",
            "abs_posture": "Exempted if biological resource is traded as a commodity, but commercial utilization of wild species requires NBA clearance.",
            "required_evidence": "Compliance with FSSAI safety, labeling, and non-medicinal therapeutic claims."
        },
        "COSMETIC": {
            "name": "Ayurvedic Cosmetic",
            "description": "Formulation intended for cleansing, beautifying, or altering appearance containing Ayurvedic herbs.",
            "regulatory_framework": "Cosmetics Rules 2020 under Drugs & Cosmetics Act",
            "ip_posture": "Formulation and industrial designs (bottle/packaging) protected via Designs Act 2000 and Trademarks.",
            "abs_posture": "Commercial use of local bio-resources requires State Biodiversity Board (SBB) notification.",
            "required_evidence": "Dermatological safety, absence of banned heavy metals or synthetic steroids."
        }
    }

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
            category = "PHYTOPHARMACEUTICAL"
        elif answers.get("intended_for_food"):
            category = "AYURVEDA_AAHAR"
        elif answers.get("intended_for_cosmetic"):
            category = "COSMETIC"
        elif answers.get("is_in_first_schedule") and not answers.get("uses_modified_ratio_or_novel_combo"):
            category = "CLASSICAL_MEDICINE"
        else:
            category = "PROPRIETARY_MEDICINE"

        info = cls.CATEGORIES[category]
        return {
            "category_code": category,
            "category_name": info["name"],
            "description": info["description"],
            "regulatory_framework": info["regulatory_framework"],
            "ip_posture": info["ip_posture"],
            "abs_posture": info["abs_posture"],
            "required_evidence": info["required_evidence"],
            "next_steps": [
                "Verify specific herbs against NBA Threat Status / Threatened Species list.",
                "Conduct InPASS & TKDL prior-art search for novelty evaluation.",
                "Prepare regulatory submission dossier for CDSCO / State Licensing Authority / FSSAI."
            ]
        }

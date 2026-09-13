"""
Canonical 5-Tier Ayurvedic Formulation Taxonomy (CRAG.md §3.2, Rule R9).

Single source of truth for the statutory/IP/ABS metadata behind each formulation
category. Previously this metadata was hand-duplicated in two places —
ml_pipeline/agents/classifier_agent.py (free-text classifier feeding the CRAG
R9 gate) and backend/app/services/classification_service.py (structured
wizard behind /api/v1/classify) — which meant the same product could be told
two different statutory stories depending on which endpoint was hit. Both now
read from this table; only their *decision logic* (how they arrive at a
category — keyword matching vs. boolean decision tree) stays separate, since
that reflects a genuine difference in input shape, not a difference in law.
"""

from typing import Any, Dict, List, TypedDict


class CategoryMetadata(TypedDict):
    text_category: str  # lowercase slug used by FormulationClassifierAgent
    name: str
    description: str
    regulatory_framework: str
    ip_posture: str
    abs_posture: str
    required_evidence: str
    recommended_pathway: str
    next_steps: List[str]
    confidence: float


CATEGORY_METADATA: Dict[str, CategoryMetadata] = {
    "CLASSICAL_MEDICINE": {
        "text_category": "classical_generic",
        "name": "Classical / Generic Ayurvedic Medicine",
        "description": (
            "Formulation and process described verbatim in First-Schedule authoritative "
            "texts (e.g. Charaka Samhita, Sharangadhara Samhita)."
        ),
        "regulatory_framework": (
            "Drugs & Cosmetics Act 1940, Schedule T (GMP) — Section 3(a) & First Schedule Authoritative Texts"
        ),
        "ip_posture": (
            "Absolute Patent Bar under Section 3(p) of The Patents Act 1970 (Traditional Knowledge). "
            "Protected by TKDL defense against foreign misappropriation."
        ),
        "abs_posture": (
            "Exempt from ABS benefit-sharing for Indian AYUSH practitioners, but commercial "
            "manufacturers using biological resources require NBA compliance."
        ),
        "required_evidence": "Strict compliance with Pharmacopoeial Standards (API / AFI).",
        "recommended_pathway": (
            "Manufacture under Classical AYUSH Drug License. Cannot be patented. "
            "Protected against biopiracy via CSIR-TKDL."
        ),
        "next_steps": [
            "Verify specific herbs against NBA Threat Status / Threatened Species list.",
            "Conduct InPASS & TKDL prior-art search for novelty evaluation.",
            "Prepare regulatory submission dossier for CDSCO / State Licensing Authority / FSSAI.",
        ],
        "confidence": 0.96,
    },
    "PROPRIETARY_MEDICINE": {
        "text_category": "patent_and_proprietary",
        "name": "Patent or Proprietary Medicine (Ayurvedic)",
        "description": (
            "Formulation contains ingredients specified in authoritative texts, but uses "
            "modified ratios, novel combinations, or modern dosage forms."
        ),
        "regulatory_framework": "Drugs and Cosmetics Rules, 1945 — Rule 158B (AYUSH SLA)",
        "ip_posture": (
            "Vulnerable to Section 3(d) (enhanced efficacy requirement) and Section 3(e) "
            "(mere admixture bar). Patentable only on proving a non-obvious inventive step "
            "over prior art."
        ),
        "abs_posture": (
            "Commercial exploitation of biological resources requires prior notification/approval "
            "from SBB/NBA (Form I). Benefit-sharing applies."
        ),
        "required_evidence": "Safety and efficacy data as prescribed under Rule 158B.",
        "recommended_pathway": (
            "Requires pilot clinical safety/toxicity data under Rule 158B. Patenting requires "
            "demonstrating unexpected synergistic efficacy beyond known textbook properties."
        ),
        "next_steps": [
            "Verify specific herbs against NBA Threat Status / Threatened Species list.",
            "Conduct InPASS & TKDL prior-art search for novelty evaluation.",
            "Prepare regulatory submission dossier for CDSCO / State Licensing Authority / FSSAI.",
        ],
        "confidence": 0.88,
    },
    "PHYTOPHARMACEUTICAL": {
        "text_category": "phytopharmaceutical",
        "name": "Phytopharmaceutical Drug",
        "description": (
            "Standardized fraction (extract) containing at least 4 active marker compounds "
            "derived from a medicinal plant."
        ),
        "regulatory_framework": "Drugs and Cosmetics Rules, 1945 — Rule 122E (CDSCO, New Drug Category)",
        "ip_posture": (
            "Strong patent potential for novel process of extraction, standardized composition, "
            "and therapeutic indication."
        ),
        "abs_posture": (
            "Strict NBA approval required (Form I for Indian entity, Form III for foreign IP "
            "transfer). Benefit sharing mandatory under BDA 2023."
        ),
        "required_evidence": (
            "Full clinical trials (Phase I-III), fingerprinting, safety profiles equivalent to "
            "new chemical entities."
        ),
        "recommended_pathway": (
            "Eligible for strong patent protection (composition of matter or process). "
            "Requires IND application, Phase I-III clinical trials under CDSCO."
        ),
        "next_steps": [
            "Verify specific herbs against NBA Threat Status / Threatened Species list.",
            "Conduct InPASS & TKDL prior-art search for novelty evaluation.",
            "Prepare regulatory submission dossier for CDSCO / State Licensing Authority / FSSAI.",
        ],
        "confidence": 0.95,
    },
    "AYURVEDA_AAHAR": {
        "text_category": "ayurveda_aahar",
        "name": "Ayurveda-Aahar / Food Supplement",
        "description": (
            "Food products prepared strictly in accordance with recipes or ingredients specified "
            "in the 71 authoritative Ayurvedic books (FSSAI October 2024 Compendium). Excludes "
            "Ayurvedic drugs, proprietary medicines, bhasmas, and cosmetics."
        ),
        "regulatory_framework": "Food Safety and Standards (Ayurveda Aahar) Regulations, 2022 & October 2024 Compendium",
        "ip_posture": (
            "No therapeutic or disease claims permitted; trade dress, trademark, and design "
            "protection primary. Excludes Ayurvedic drugs, proprietary medicines, bhasmas, and cosmetics."
        ),
        "abs_posture": (
            "Exempted if biological resource is normally traded as a commodity (NTAC), but "
            "commercial utilization of wild species requires NBA/SBB clearance."
        ),
        "required_evidence": (
            "FSSAI license with dedicated Ayurveda Aahar logo. Free from synthetic vitamins, "
            "minerals, or amino acids."
        ),
        "recommended_pathway": (
            "FSSAI license with mandatory Ayurveda Aahar logo. Formulated strictly from the 71 "
            "authoritative texts. Prohibits synthetic vitamins, minerals, or amino acids."
        ),
        "next_steps": [
            "Verify specific herbs against NBA Threat Status / Threatened Species list.",
            "Conduct InPASS & TKDL prior-art search for novelty evaluation.",
            "Prepare regulatory submission dossier for CDSCO / State Licensing Authority / FSSAI.",
        ],
        "confidence": 0.92,
    },
    "COSMETIC": {
        "text_category": "cosmetic",
        "name": "Ayurvedic Cosmetic",
        "description": (
            "Formulation intended for cleansing, beautifying, or altering appearance containing "
            "Ayurvedic herbs."
        ),
        "regulatory_framework": "Cosmetics Rules 2020 under Drugs & Cosmetics Act",
        "ip_posture": (
            "Formulation patent barred if simple herbal blend; trademark and industrial design "
            "protection (bottle/packaging) primary via Designs Act 2000."
        ),
        "abs_posture": "Commercial use of local bio-resources requires State Biodiversity Board (SBB) notification.",
        "required_evidence": "Dermatological safety, absence of banned heavy metals or synthetic steroids.",
        "recommended_pathway": "Form 32 cosmetic manufacturing license; Bureau of Indian Standards (BIS) compliance.",
        "next_steps": [
            "Verify specific herbs against NBA Threat Status / Threatened Species list.",
            "Conduct InPASS & TKDL prior-art search for novelty evaluation.",
            "Prepare regulatory submission dossier for CDSCO / State Licensing Authority / FSSAI.",
        ],
        "confidence": 0.90,
    },
}

# Reverse lookup: text_category slug (used by FormulationClassifierAgent) -> category code
TEXT_CATEGORY_TO_CODE: Dict[str, str] = {
    meta["text_category"]: code for code, meta in CATEGORY_METADATA.items()
}


def get_metadata_by_code(category_code: str) -> CategoryMetadata:
    return CATEGORY_METADATA[category_code]


def get_metadata_by_text_category(text_category: str) -> CategoryMetadata:
    return CATEGORY_METADATA[TEXT_CATEGORY_TO_CODE[text_category]]

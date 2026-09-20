"""
Phase 3 — Case Assessment Agent (Charaka IP PS045)

Implements the 5-subpart deterministic classification and mapping pipeline:

  3.1  CASE NORMALIZATION          — sanitizes/validates the InnovationProfile
  3.2  PRODUCT CLASSIFICATION      — maps to the 5-tier Ayurvedic taxonomy
  3.3  IP DOMAIN CLASSIFICATION    — identifies applicable IP regimes & barriers
  3.4  JURISDICTION & REGULATORY   — maps target jurisdictions to regulatory frameworks
  3.5  RESEARCH PLAN GENERATION    — generates prioritized tasks for Phase 4 CRAG

IMPORTANT CONSTRAINTS (enforced by design — no runtime checks needed):
  - Zero LLM calls. Fully deterministic.
  - Zero Qdrant / vector store queries.
  - Zero actual legal research or prior-art searching.
  - Zero final patentability/ABS/compliance determinations.
  - Pure transformation: InnovationProfile → CaseAssessment.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from ml_pipeline.schemas.case_schema import (
    InnovationProfile,
    IPObjective,
    TKBasis,
    DevelopmentStage,
)
from ml_pipeline.schemas.assessment_schema import (
    AssessmentStatus,
    CaseAssessment,
    CompletenessLevel,
    FormulationCategory,
    IPDomainClassification,
    IPDomainFlag,
    JurisdictionMapping,
    NormalizedCase,
    ProductClassification,
    RegulatoryMapping,
    ResearchPlan,
    ResearchPriorityLevel,
    ResearchTask,
    Section3PAnalysis,
)
from ml_pipeline.agents.formulation_taxonomy import CATEGORY_METADATA

logger = logging.getLogger("case_assessment_agent")

# ── Constants ──────────────────────────────────────────────────────────────

_NATIONAL_AUTHORITY = "CDSCO / State Licensing Authority (AYUSH)"
_FOOD_AUTHORITY = "FSSAI"
_COSMETIC_AUTHORITY = "CDSCO (Cosmetics Division)"

_JURISDICTION_REGULATORY_MAP = {
    "INDIA": {
        "authority": "CDSCO / AYUSH Ministry / FSSAI",
        "frameworks": [
            "Drugs and Cosmetics Act, 1940",
            "The Patents Act, 1970 (amended 2005)",
            "Biological Diversity Act, 2002 (amended 2023)",
        ],
        "abs_applicable": True,
        "abs_note": "NBA/SBB approval required for commercial utilization of biological resources.",
    },
    "USA": {
        "authority": "FDA (CFSAN / CDER) / USPTO",
        "frameworks": [
            "Dietary Supplement Health and Education Act (DSHEA), 1994",
            "Patent Act (35 U.S.C.)",
        ],
        "abs_applicable": False,
        "abs_note": "USA is not a party to the Nagoya Protocol on ABS.",
    },
    "EU": {
        "authority": "EMA / EFSA / EPO / National Patent Offices",
        "frameworks": [
            "EU Traditional Herbal Medicinal Products Directive 2004/24/EC",
            "EU Biodiversity Regulation (ABS Regulation No. 511/2014)",
            "European Patent Convention (EPC)",
        ],
        "abs_applicable": True,
        "abs_note": "EU ABS Regulation applies — due diligence declaration required for biological resources.",
    },
    "UK": {
        "authority": "MHRA / UKIPO",
        "frameworks": [
            "Human Medicines Regulations 2012",
            "Patents Act 1977",
        ],
        "abs_applicable": False,
        "abs_note": "UK has not yet implemented full Nagoya Protocol post-Brexit.",
    },
    "GERMANY": {
        "authority": "BfArM / DPMA / EPO",
        "frameworks": [
            "Arzneimittelgesetz (AMG)",
            "EU Traditional Herbal Medicinal Products Directive",
            "EU ABS Regulation No. 511/2014",
        ],
        "abs_applicable": True,
        "abs_note": "EU ABS Regulation applies.",
    },
    "JAPAN": {
        "authority": "PMDA / JPO",
        "frameworks": [
            "Pharmaceutical and Medical Device Act (PMD Act)",
            "Patent Act (Japan)",
        ],
        "abs_applicable": True,
        "abs_note": "Japan is a party to the Nagoya Protocol.",
    },
    "AUSTRALIA": {
        "authority": "TGA / IP Australia",
        "frameworks": [
            "Therapeutic Goods Act 1989",
            "Patents Act 1990",
        ],
        "abs_applicable": True,
        "abs_note": "Australia is a party to the Nagoya Protocol.",
    },
    "CANADA": {
        "authority": "Health Canada / CIPO",
        "frameworks": [
            "Natural Health Products Regulations",
            "Patent Act (Canada)",
        ],
        "abs_applicable": False,
        "abs_note": "Canada has not ratified the Nagoya Protocol.",
    },
    "EUROPE": {
        "authority": "EMA / EPO",
        "frameworks": [
            "EU Traditional Herbal Medicinal Products Directive 2004/24/EC",
            "European Patent Convention (EPC)",
            "EU ABS Regulation No. 511/2014",
        ],
        "abs_applicable": True,
        "abs_note": "EU ABS Regulation applies.",
    },
}

_INTERNATIONAL_TREATIES = [
    "TRIPS Agreement (WTO)",
    "Patent Cooperation Treaty (PCT)",
    "Convention on Biological Diversity (CBD)",
    "Nagoya Protocol on Access and Benefit-Sharing",
    "WIPO GRATK Treaty (2024)",
]

_FORMULATION_PRODUCT_TYPES = {
    "TABLET", "CAPSULE", "POWDER", "OIL", "CREAM", "FOOD", "COSMETIC",
    "FORMULATION", "AYURVEDIC_FORMULATION", "MEDICINE",
}


class CaseAssessmentAgent:
    """
    Phase 3 deterministic assessment engine.
    Pure function: InnovationProfile → CaseAssessment. No I/O side effects.
    """

    @classmethod
    def assess(cls, case_id: str, profile: InnovationProfile) -> CaseAssessment:
        """
        Runs the full 5-subpart assessment pipeline and returns a CaseAssessment.
        """
        logger.info("Phase 3: starting assessment for case %s", case_id)

        try:
            # 3.1 Case Normalization
            normalized = cls._normalize(case_id, profile)

            # 3.2 Product / Formulation Classification
            product_cls = cls._classify_product(profile)

            # 3.3 IP Domain Classification
            ip_domain = cls._classify_ip_domain(profile, product_cls)

            # 3.4 Jurisdiction & Regulatory Mapping
            regulatory = cls._map_regulatory(profile, product_cls, ip_domain)

            # 3.5 Research Plan Generation
            research_plan = cls._generate_research_plan(
                profile, product_cls, ip_domain, regulatory
            )

            # Executive summary
            summary, risks, opportunities = cls._executive_summary(
                profile, product_cls, ip_domain, regulatory, research_plan
            )

            assessment = CaseAssessment(
                case_id=case_id,
                assessment_status=AssessmentStatus.COMPLETED,
                assessed_at=datetime.now(timezone.utc),
                normalized=normalized,
                product_classification=product_cls,
                ip_domain=ip_domain,
                regulatory_mapping=regulatory,
                research_plan=research_plan,
                executive_summary=summary,
                key_risks=risks,
                key_opportunities=opportunities,
            )

            logger.info("Phase 3: assessment completed for case %s — %s", case_id, product_cls.category.value)
            return assessment

        except Exception as e:
            logger.error("Phase 3: assessment failed for case %s: %s", case_id, e, exc_info=True)
            return CaseAssessment(
                case_id=case_id,
                assessment_status=AssessmentStatus.FAILED,
                assessed_at=datetime.now(timezone.utc),
                executive_summary=f"Assessment could not be completed: {e}",
            )

    # ── 3.1 Case Normalization ─────────────────────────────────────────────

    @classmethod
    def _normalize(cls, case_id: str, profile: InnovationProfile) -> NormalizedCase:
        notes: List[str] = []
        ip_objectives = [obj.value for obj in profile.ip_objectives]

        if not profile.short_description:
            notes.append("No product description provided — research queries will be less precise.")
        if not profile.claimed_novelty:
            notes.append("No novelty claim stated — patent potential cannot be estimated.")
        if not profile.target_jurisdictions:
            notes.append("No target jurisdictions specified — regulatory mapping will default to India.")
        if not profile.ingredients and (profile.product_type or "").upper() in _FORMULATION_PRODUCT_TYPES:
            notes.append("No ingredients listed for formulation-type product.")

        if not notes:
            completeness = CompletenessLevel.COMPLETE
        elif len(notes) <= 2:
            completeness = CompletenessLevel.ADEQUATE
        else:
            completeness = CompletenessLevel.INCOMPLETE

        return NormalizedCase(
            case_id=case_id,
            innovation_name=profile.innovation_name or profile.product_name,
            short_description=profile.short_description,
            product_type=profile.product_type,
            ingredients_summary=list(profile.ingredients[:15]),  # cap for display
            claimed_novelty=profile.claimed_novelty,
            development_stage=profile.development_stage.value if profile.development_stage else None,
            tk_basis=profile.tk_basis.value if profile.tk_basis else None,
            ip_objectives=ip_objectives,
            target_jurisdictions=list(profile.target_jurisdictions),
            completeness=completeness,
            completeness_notes=notes,
        )

    # ── 3.2 Product / Formulation Classification ──────────────────────────

    @classmethod
    def _classify_product(cls, profile: InnovationProfile) -> ProductClassification:
        product_type_upper = (profile.product_type or "").upper()
        desc_lower = (profile.short_description or "").lower()
        novelty_lower = (profile.claimed_novelty or "").lower()
        ingredients = profile.ingredients
        is_formulation = product_type_upper in _FORMULATION_PRODUCT_TYPES or bool(ingredients)

        # Decision tree mirroring classification_service.py's logic, driven by profile fields
        # Phytopharmaceutical: standardized extract / bioactive markers
        if (
            bool(profile.standardization)
            or bool(profile.bioactive_markers)
            or profile.extraction_method
            or any(k in desc_lower for k in ["fraction", "phytopharmaceutical", "standardized extract", "bioactive marker"])
            or any(k in novelty_lower for k in ["standardized", "fraction", "bioactive"])
        ):
            return cls._build_product_cls("PHYTOPHARMACEUTICAL", is_formulation,
                                          "Standardized extract / bioactive markers detected in profile.")

        # Ayurveda Aahar
        if (
            any(k in desc_lower for k in ["food", "supplement", "nutraceutical", "aahar", "dietary", "beverage"])
            or product_type_upper in ("FOOD",)
        ):
            return cls._build_product_cls("AYURVEDA_AAHAR", is_formulation,
                                          "Food/supplement product type identified.")

        # Cosmetic
        if (
            any(k in desc_lower for k in ["cosmetic", "shampoo", "cream", "lotion", "serum", "soap"])
            or product_type_upper == "COSMETIC"
        ):
            return cls._build_product_cls("COSMETIC", is_formulation,
                                          "Cosmetic product type identified.")

        # Classical Medicine: verbatim from classical text, no novel modification
        if profile.tk_basis == TKBasis.CLASSICAL_TEXT or (profile.classical_reference and not profile.novel_combination):
            if not profile.modified_ratio and not profile.modified_process and not profile.novel_combination:
                return cls._build_product_cls("CLASSICAL_MEDICINE", is_formulation,
                                              "TK basis: classical text; no novel modification stated.")

        # Proprietary / P&P: novel combination, modified ratio, or novel process
        if (
            profile.novel_combination
            or profile.modified_ratio
            or profile.modified_process
            or any(k in novelty_lower for k in ["novel", "proprietary", "modified", "synergistic", "new ratio", "new combination"])
            or any(k in desc_lower for k in ["proprietary", "novel combination", "modified ratio"])
        ):
            return cls._build_product_cls("PROPRIETARY_MEDICINE", is_formulation,
                                          "Novel modification / proprietary combination stated in profile.")

        # If it's a formulation-type product but we can't classify, lean toward classical
        if is_formulation:
            if profile.tk_basis in (TKBasis.TRADITIONAL_USE, TKBasis.COMMUNITY_KNOWLEDGE):
                return cls._build_product_cls("CLASSICAL_MEDICINE", is_formulation,
                                              "Traditional/community use basis without stated modification.")
            return cls._build_product_cls("PROPRIETARY_MEDICINE", is_formulation,
                                          "Formulation without sufficient classification signals — defaulting to Proprietary.")

        # Non-formulation (device, process, software, etc.)
        if product_type_upper in ("DEVICE", "PROCESS", "SOFTWARE", "INVENTION"):
            meta_fallback = {
                "name": "Non-Formulation Innovation",
                "description": "Device, process, method, or software innovation.",
                "regulatory_framework": "The Patents Act, 1970; relevant sector regulation",
                "ip_posture": "Patent-eligible if novel, inventive, and industrially applicable — Section 3(p) does not apply to non-Ayurvedic innovations.",
                "abs_posture": "ABS may apply if biological materials are used in the process.",
                "confidence": 0.75,
            }
            return ProductClassification(
                category=FormulationCategory.NON_FORMULATION,
                category_name=meta_fallback["name"],
                description=meta_fallback["description"],
                regulatory_framework=meta_fallback["regulatory_framework"],
                confidence=meta_fallback["confidence"],
                classification_basis="Non-formulation product type.",
                is_formulation_type=False,
            )

        return ProductClassification(
            category=FormulationCategory.UNDETERMINED,
            category_name="Undetermined",
            description="Insufficient information to classify product category.",
            regulatory_framework="",
            confidence=0.3,
            classification_basis="No product type or formulation signals detected.",
            is_formulation_type=is_formulation,
        )

    @classmethod
    def _build_product_cls(cls, code: str, is_formulation: bool, basis: str) -> ProductClassification:
        meta = CATEGORY_METADATA[code]
        cat_map = {
            "CLASSICAL_MEDICINE": FormulationCategory.CLASSICAL_MEDICINE,
            "PROPRIETARY_MEDICINE": FormulationCategory.PROPRIETARY_MEDICINE,
            "PHYTOPHARMACEUTICAL": FormulationCategory.PHYTOPHARMACEUTICAL,
            "AYURVEDA_AAHAR": FormulationCategory.AYURVEDA_AAHAR,
            "COSMETIC": FormulationCategory.COSMETIC,
        }
        return ProductClassification(
            category=cat_map[code],
            category_name=meta["name"],
            description=meta["description"],
            regulatory_framework=meta["regulatory_framework"],
            confidence=meta["confidence"],
            classification_basis=basis,
            is_formulation_type=is_formulation,
        )

    # ── 3.3 IP Domain Classification ──────────────────────────────────────

    @classmethod
    def _classify_ip_domain(
        cls, profile: InnovationProfile, product_cls: ProductClassification
    ) -> IPDomainClassification:

        ip_domains: List[str] = []
        statutory_notes: List[str] = []
        tkdl_note = ""

        # Determine primary objective
        primary = profile.primary_ip_objective or (
            profile.ip_objectives[0] if profile.ip_objectives else None
        )

        # Section 3(p) analysis
        s3p = cls._analyze_section_3p(profile, product_cls)

        # TKDL relevance
        tkdl_relevant = product_cls.category in (
            FormulationCategory.CLASSICAL_MEDICINE,
            FormulationCategory.PROPRIETARY_MEDICINE,
        ) or profile.tk_basis in (TKBasis.CLASSICAL_TEXT, TKBasis.TRADITIONAL_USE, TKBasis.COMMUNITY_KNOWLEDGE)

        if tkdl_relevant:
            tkdl_note = (
                "TKDL (Traditional Knowledge Digital Library) prior-art search is recommended "
                "before any patent filing to identify existing traditional knowledge disclosures "
                "that may affect novelty. The CSIR-TKDL database covers formulations from "
                "Ayurveda, Unani, Siddha, and Yoga."
            )

        # Determine domain and posture by product category
        category = product_cls.category

        if category == FormulationCategory.CLASSICAL_MEDICINE:
            primary_domain = IPDomainFlag.PATENT_BAR_LIKELY
            ip_domains = ["TKDL_DEFENSE", "CLASSICAL_PROTECTION"]
            ip_posture = (
                "**Section 3(p) Patent Bar Likely** — Formulations verbatim from First Schedule "
                "authoritative texts face an absolute patent bar under Section 3(p) of the "
                "Patents Act, 1970 (as traditional knowledge). Consider TKDL registration and "
                "GI protection if eligible."
            )
            statutory_notes = [
                "Section 3(p), The Patents Act, 1970: traditional knowledge bar",
                "CSIR-TKDL: prior-art database protecting against foreign misappropriation",
            ]
            if IPObjective.TRADEMARK in profile.ip_objectives:
                ip_domains.append("TRADEMARK")
                ip_posture += " Trademark and trade dress protection remain available."

        elif category == FormulationCategory.PROPRIETARY_MEDICINE:
            primary_domain = IPDomainFlag.PATENT_POSSIBLE
            ip_domains = ["PATENT", "TRADEMARK"]
            ip_posture = (
                "**Patent Possible (Section 3(d)/(e) risks present)** — Proprietary combinations "
                "may face Section 3(d) (no enhanced efficacy for known substance) and Section 3(e) "
                "(mere admixture bar). A novel inventive step over prior art, demonstrating synergistic "
                "or unexpected efficacy, is required for a valid Indian patent claim."
            )
            statutory_notes = [
                "Section 3(d), The Patents Act, 1970: enhanced efficacy requirement",
                "Section 3(e): admixture bar — must demonstrate non-obvious synergy",
                "Section 3(p): TKDL prior-art search required to confirm novelty over TK",
            ]

        elif category == FormulationCategory.PHYTOPHARMACEUTICAL:
            primary_domain = IPDomainFlag.PATENT_STRONG
            ip_domains = ["PATENT", "PROCESS_PATENT", "COMPOSITION_PATENT"]
            ip_posture = (
                "**Strong Patent Potential** — Standardized phytopharmaceutical extracts with "
                "defined bioactive markers are patentable for novel composition of matter, "
                "extraction process, and therapeutic indication under the Patents Act, 1970."
            )
            statutory_notes = [
                "Rule 122E, Drugs and Cosmetics Rules: New Drug category for phytopharmaceuticals",
                "Full Phase I-III clinical trials required for CDSCO approval",
                "NBA Form I (Indian entity) or Form III (foreign IP transfer) required",
            ]

        elif category == FormulationCategory.AYURVEDA_AAHAR:
            primary_domain = IPDomainFlag.TRADEMARK_PRIMARY
            ip_domains = ["TRADEMARK", "TRADE_DRESS", "DESIGN"]
            ip_posture = (
                "**Trademark & Design Primary** — Food/supplement products cannot make therapeutic "
                "or disease claims. IP protection focuses on brand identity (trademark), packaging "
                "design, and trade dress under the Trade Marks Act, 1999 and Designs Act, 2000."
            )
            statutory_notes = [
                "FSSAI Ayurveda Aahar Regulations, 2022 — no therapeutic claims",
                "October 2024 FSSAI Compendium: 71 authoritative texts — ingredient compliance",
                "No synthetic vitamins/minerals/amino acids permitted",
            ]

        elif category == FormulationCategory.COSMETIC:
            primary_domain = IPDomainFlag.TRADEMARK_PRIMARY
            ip_domains = ["TRADEMARK", "DESIGN", "TRADE_DRESS"]
            ip_posture = (
                "**Trademark & Design Primary** — Cosmetic formulation patents face high bars if "
                "based on known herbal blends. Trademark (brand/logo under Trade Marks Act, 1999) "
                "and industrial design (packaging under Designs Act, 2000) are the primary paths."
            )
            statutory_notes = [
                "Cosmetics Rules 2020 under Drugs & Cosmetics Act: Form 32 license",
                "BIS compliance required for certain categories",
                "SBB notification required for commercial use of local bio-resources",
            ]

        elif category == FormulationCategory.NON_FORMULATION:
            primary_domain = IPDomainFlag.PATENT_STRONG if primary == IPObjective.PATENT else IPDomainFlag.UNCLEAR
            ip_domains = ["PATENT", "DESIGN"] if primary == IPObjective.PATENT else ["TRADEMARK", "COPYRIGHT"]
            ip_posture = (
                "**Patent Eligible (Section 3(p) not applicable)** — Non-formulation innovations "
                "(devices, processes, methods) are not subject to the TK patent bar. Patentability "
                "depends on novelty, inventive step, and industrial applicability under Sections 2(1)(j), 2(1)(ja)."
            )
            statutory_notes = [
                "Sections 2(1)(j), 2(1)(ja), The Patents Act, 1970: novelty and inventive step",
                "Section 3(p) TK bar does not apply to non-formulation inventions",
            ]

        else:
            primary_domain = IPDomainFlag.UNCLEAR
            ip_domains = []
            ip_posture = "Insufficient classification data — IP posture cannot be determined at this stage."
            statutory_notes = []

        # Add requested IP objective considerations
        for obj in profile.ip_objectives:
            if obj == IPObjective.GI and "GI" not in ip_domains:
                ip_domains.append("GI")
                ip_posture += " Geographical Indication protection may be available if the product has a specific geographic origin."
            if obj == IPObjective.PLANT_VARIETY and "PLANT_VARIETY" not in ip_domains:
                ip_domains.append("PLANT_VARIETY")
                statutory_notes.append("Protection of Plant Varieties and Farmers' Rights Act, 2001")

        return IPDomainClassification(
            primary_ip_domain=primary_domain,
            ip_domains_applicable=ip_domains,
            ip_posture=ip_posture,
            section_3p_analysis=s3p,
            tkdl_relevance=tkdl_relevant,
            tkdl_note=tkdl_note,
            key_statutory_considerations=statutory_notes,
        )

    @classmethod
    def _analyze_section_3p(
        cls, profile: InnovationProfile, product_cls: ProductClassification
    ) -> Section3PAnalysis:
        if product_cls.category == FormulationCategory.CLASSICAL_MEDICINE:
            return Section3PAnalysis(
                bar_likely=True,
                basis="Formulation classified as verbatim classical text derivation.",
                notes=(
                    "Section 3(p) of The Patents Act, 1970 bars patents on traditional knowledge "
                    "per se. This is a PRELIMINARY ASSESSMENT — actual determination requires TKDL "
                    "search and qualified IP counsel review."
                ),
            )
        if product_cls.category == FormulationCategory.PROPRIETARY_MEDICINE:
            return Section3PAnalysis(
                bar_likely=False,
                basis="Novel modification claimed — Section 3(p) less likely but requires TKDL search.",
                notes=(
                    "If the novel combination or process is fully documented in any classical text, "
                    "Section 3(p) may still apply. TKDL search is mandatory before filing."
                ),
            )
        if product_cls.category == FormulationCategory.NON_FORMULATION:
            return Section3PAnalysis(
                bar_likely=False,
                basis="Non-formulation innovation — Section 3(p) TK bar does not apply.",
                notes="",
            )
        return Section3PAnalysis(
            bar_likely=False,
            basis="Insufficient data for Section 3(p) analysis.",
            notes="Consult a qualified IP attorney for definitive assessment.",
        )

    # ── 3.4 Jurisdiction & Regulatory Mapping ─────────────────────────────

    @classmethod
    def _map_regulatory(
        cls,
        profile: InnovationProfile,
        product_cls: ProductClassification,
        ip_domain: IPDomainClassification,
    ) -> RegulatoryMapping:

        target_juris = list(profile.target_jurisdictions) or ["INDIA"]
        jur_maps: List[JurisdictionMapping] = []
        export_considerations: List[str] = []

        for jur in target_juris:
            jur_upper = jur.upper()
            reg_info = _JURISDICTION_REGULATORY_MAP.get(jur_upper, {
                "authority": "Relevant national authority",
                "frameworks": ["Country-specific pharmaceutical/IP law"],
                "abs_applicable": False,
                "abs_note": "Verify Nagoya Protocol status for this jurisdiction.",
            })

            # Tailor required licenses per product category
            licenses = cls._required_licenses(jur_upper, product_cls)
            compliance_steps = cls._compliance_steps(jur_upper, product_cls, ip_domain)

            jur_maps.append(JurisdictionMapping(
                jurisdiction=jur_upper,
                regulatory_authority=reg_info["authority"],
                applicable_frameworks=reg_info["frameworks"],
                required_licenses=licenses,
                abs_applicable=reg_info["abs_applicable"],
                abs_note=reg_info["abs_note"],
                key_compliance_steps=compliance_steps,
            ))

        # International treaties applicable
        treaties = []
        if len(target_juris) > 1:
            treaties.append("Patent Cooperation Treaty (PCT) — international patent filing route")
        if any(j in ("USA", "EU", "GERMANY", "EUROPE", "UK", "JAPAN", "AUSTRALIA") for j in target_juris):
            treaties.append("TRIPS Agreement (WTO) — sets minimum IP standards in WTO member states")
        if any(reg.abs_applicable for reg in jur_maps):
            treaties.append("Nagoya Protocol on ABS — binding in ratifying jurisdictions")
            treaties.append("Convention on Biological Diversity (CBD)")
        if any(j in ("EU", "GERMANY", "EUROPE", "JAPAN", "AUSTRALIA") for j in target_juris):
            treaties.append("WIPO GRATK Treaty (2024) — disclosure of origin for TK-based patents")

        # ABS posture
        category_code_map = {
            FormulationCategory.CLASSICAL_MEDICINE: "CLASSICAL_MEDICINE",
            FormulationCategory.PROPRIETARY_MEDICINE: "PROPRIETARY_MEDICINE",
            FormulationCategory.PHYTOPHARMACEUTICAL: "PHYTOPHARMACEUTICAL",
            FormulationCategory.AYURVEDA_AAHAR: "AYURVEDA_AAHAR",
            FormulationCategory.COSMETIC: "COSMETIC",
        }
        abs_posture = ""
        code = category_code_map.get(product_cls.category)
        if code and code in CATEGORY_METADATA:
            abs_posture = CATEGORY_METADATA[code]["abs_posture"]

        # Export considerations
        if len(target_juris) > 1:
            export_considerations.append("Export of biological material requires NBA export permit under Section 7, BDA 2002.")
        if any(j in ("EU", "GERMANY", "EUROPE") for j in target_juris):
            export_considerations.append("EU ABS Regulation (No. 511/2014): due diligence declaration required for EU market entry.")
        if "USA" in target_juris:
            export_considerations.append("FDA pre-market notification (DSHEA) required for dietary supplements in USA.")

        return RegulatoryMapping(
            jurisdiction_maps=jur_maps,
            international_treaties=treaties,
            abs_posture=abs_posture,
            export_considerations=export_considerations,
        )

    @classmethod
    def _required_licenses(cls, jurisdiction: str, product_cls: ProductClassification) -> List[str]:
        cat = product_cls.category
        if jurisdiction == "INDIA":
            if cat == FormulationCategory.CLASSICAL_MEDICINE:
                return ["AYUSH Classical Drug License (State Licensing Authority)", "Schedule T GMP Compliance"]
            if cat == FormulationCategory.PROPRIETARY_MEDICINE:
                return ["AYUSH Proprietary Drug License (Rule 158B)", "Clinical Safety/Toxicity Data"]
            if cat == FormulationCategory.PHYTOPHARMACEUTICAL:
                return ["CDSCO New Drug Approval (Rule 122E)", "Phase I-III Clinical Trial IND"]
            if cat == FormulationCategory.AYURVEDA_AAHAR:
                return ["FSSAI Ayurveda Aahar License", "Mandatory Ayurveda Aahar Logo"]
            if cat == FormulationCategory.COSMETIC:
                return ["CDSCO Form 32 Manufacturing License", "BIS Compliance (if applicable)"]
        if jurisdiction == "USA":
            return ["FDA Dietary Supplement Notification (DSHEA)", "GRAS Status (if food)"]
        if jurisdiction in ("EU", "GERMANY", "EUROPE"):
            return ["EMA Traditional Herbal Registration (THMPD Article 16d)", "EU ABS Due Diligence Declaration"]
        return ["Country-specific marketing authorization"]

    @classmethod
    def _compliance_steps(
        cls, jurisdiction: str, product_cls: ProductClassification, ip_domain: IPDomainClassification
    ) -> List[str]:
        steps = []
        cat = product_cls.category

        if jurisdiction == "INDIA":
            steps.append("Conduct TKDL & InPASS prior-art search (recommended before any filing).")
            if cat == FormulationCategory.PHYTOPHARMACEUTICAL:
                steps.append("File IND application with CDSCO and initiate Phase I clinical trials.")
                steps.append("Submit NBA Form I for biological resource utilization approval.")
            elif cat == FormulationCategory.PROPRIETARY_MEDICINE:
                steps.append("Prepare safety & efficacy data dossier under Drugs & Cosmetics Rule 158B.")
                steps.append("File NBA Form I for biological resource utilization (if applicable).")
            elif cat == FormulationCategory.CLASSICAL_MEDICINE:
                steps.append("Prepare API/AFI pharmacopoeial compliance documentation.")
                steps.append("Verify each ingredient against NBA Threatened Species list.")
            elif cat == FormulationCategory.AYURVEDA_AAHAR:
                steps.append("Verify all ingredients against FSSAI October 2024 Compendium (71 texts).")
                steps.append("Ensure no synthetic vitamins, minerals, or amino acids in formulation.")
            elif cat == FormulationCategory.COSMETIC:
                steps.append("File Form 32 application with State Licensing Authority.")
                steps.append("Ensure absence of banned heavy metals and synthetic steroids.")
            if ip_domain.section_3p_analysis.bar_likely is False and IPDomainFlag.PATENT_POSSIBLE in (ip_domain.primary_ip_domain, ):
                steps.append("Draft patent specification highlighting inventive step over prior art.")
        else:
            steps.append(f"Engage local regulatory counsel for {jurisdiction} market entry.")
            steps.append("Assess Nagoya Protocol compliance obligations in target jurisdiction.")

        return steps

    # ── 3.5 Research Plan Generation ──────────────────────────────────────

    @classmethod
    def _generate_research_plan(
        cls,
        profile: InnovationProfile,
        product_cls: ProductClassification,
        ip_domain: IPDomainClassification,
        regulatory: RegulatoryMapping,
    ) -> ResearchPlan:

        tasks: List[ResearchTask] = []
        crag_queries: List[str] = []
        next_steps: List[str] = []
        task_counter = [0]

        def add_task(priority, category, title, description, statutory_basis="", effort=""):
            task_counter[0] += 1
            tasks.append(ResearchTask(
                task_id=f"T{task_counter[0]:02d}",
                priority=priority,
                category=category,
                title=title,
                description=description,
                statutory_basis=statutory_basis,
                estimated_effort=effort,
            ))

        cat = product_cls.category
        ingredients = profile.ingredients[:5]  # top 5 for query generation

        # --- Prior Art / TKDL ---
        if cat in (FormulationCategory.CLASSICAL_MEDICINE, FormulationCategory.PROPRIETARY_MEDICINE,
                   FormulationCategory.PHYTOPHARMACEUTICAL):
            add_task(
                ResearchPriorityLevel.HIGH, "PRIOR_ART",
                "TKDL & InPASS Prior-Art Search",
                "Search CSIR-TKDL and InPASS databases for existing TK disclosures and prior patents "
                "that may affect the novelty of this formulation. Required before any patent filing.",
                statutory_basis="Section 3(p), The Patents Act, 1970; CSIR-TKDL Treaty",
                effort="1-2 weeks",
            )
            if ingredients:
                ing_str = ", ".join(ingredients[:3])
                crag_queries.append(f"Section 3(p) patent bar for formulation containing {ing_str}")
                crag_queries.append(f"TKDL prior art for {ing_str} formulation")

        # --- IP Protection Research ---
        if IPObjective.PATENT in profile.ip_objectives:
            if cat == FormulationCategory.PROPRIETARY_MEDICINE:
                add_task(
                    ResearchPriorityLevel.HIGH, "IP_STRATEGY",
                    "Section 3(d)/(e) Compliance Strategy",
                    "Research the enhanced efficacy requirement under Section 3(d) and admixture bar under "
                    "Section 3(e). Identify what synergistic/unexpected efficacy evidence is needed to "
                    "overcome these bars for this proprietary formulation.",
                    statutory_basis="Sections 3(d), 3(e), The Patents Act, 1970",
                    effort="2-4 weeks",
                )
                crag_queries.append("Section 3(d) enhanced efficacy requirement Ayurvedic formulation India patent")
                crag_queries.append(f"Section 3(e) admixture bar novel combination {ingredients[0] if ingredients else 'herbal'}")

            if cat == FormulationCategory.PHYTOPHARMACEUTICAL:
                add_task(
                    ResearchPriorityLevel.HIGH, "IP_STRATEGY",
                    "Phytopharmaceutical Patent Strategy",
                    "Research composition of matter and process patent eligibility for this standardized "
                    "extract under Indian and international patent law.",
                    statutory_basis="Rule 122E, Drugs and Cosmetics Rules; The Patents Act, 1970",
                    effort="3-6 weeks",
                )
                crag_queries.append("phytopharmaceutical patent India Rule 122E standardized extract")

        if IPObjective.TRADEMARK in profile.ip_objectives:
            add_task(
                ResearchPriorityLevel.MEDIUM, "IP_STRATEGY",
                "Trademark Availability Search",
                "Search for conflicting marks in the relevant product class (Nice Classification Class 5 for "
                "pharmaceuticals; Class 3 for cosmetics; Class 30/31 for foods) through Trade Marks Registry.",
                statutory_basis="Trade Marks Act, 1999",
                effort="1 week",
            )
            crag_queries.append("trademark registration Ayurvedic product India Nice Classification")

        # --- ABS / Biodiversity ---
        has_biological = bool(profile.biological_resources) or bool(ingredients)
        abs_jur_needed = any(jm.abs_applicable for jm in regulatory.jurisdiction_maps)

        if has_biological and abs_jur_needed:
            add_task(
                ResearchPriorityLevel.HIGH, "ABS",
                "NBA/SBB Approval Requirements",
                "Determine whether this formulation requires NBA (National Biodiversity Authority) approval "
                "under Section 3, 4, or 7 of the Biological Diversity Act, 2002 (as amended 2023). "
                "Identify applicable form (Form I/III) and benefit-sharing slab.",
                statutory_basis="Biological Diversity Act, 2002 (amended 2023); Nagoya Protocol",
                effort="2-3 weeks",
            )
            crag_queries.append("Biological Diversity Act 2002 NBA approval commercial utilization biological resources")
            if regulatory.export_considerations:
                add_task(
                    ResearchPriorityLevel.MEDIUM, "ABS",
                    "Export ABS Compliance",
                    "Research ABS compliance obligations for export of this formulation to target markets, "
                    "including EU ABS Regulation No. 511/2014 and Nagoya Protocol obligations.",
                    statutory_basis="Nagoya Protocol on ABS; EU ABS Regulation No. 511/2014",
                    effort="1-2 weeks",
                )
                crag_queries.append("Nagoya Protocol access benefit sharing export India formulation")

        # --- Regulatory Compliance ---
        add_task(
            ResearchPriorityLevel.HIGH, "REGULATORY",
            "Regulatory Pathway Determination",
            f"Confirm applicable regulatory pathway for a {product_cls.category_name} product in "
            f"{', '.join(profile.target_jurisdictions or ['India'])}. Identify all required licenses, "
            "clinical data, and submission dossier requirements.",
            statutory_basis=product_cls.regulatory_framework,
            effort="1-2 weeks",
        )
        crag_queries.append(f"{product_cls.category_name} regulatory requirements India CDSCO AYUSH FSSAI")

        # --- TK Documentation ---
        if ip_domain.tkdl_relevance:
            add_task(
                ResearchPriorityLevel.MEDIUM, "TK_DOCUMENTATION",
                "Traditional Knowledge Documentation & TKDL Audit",
                "Verify all claimed traditional knowledge elements against TKDL and authoritative classical "
                "texts. Prepare a traditional knowledge documentation report to establish provenance and "
                "prevent future biopiracy claims.",
                statutory_basis="CSIR-TKDL; WIPO GRATK Treaty (2024)",
                effort="2-3 weeks",
            )
            crag_queries.append("traditional knowledge documentation TKDL biopiracy protection India")

        # --- International filing ---
        intl_juris = [j for j in (profile.target_jurisdictions or []) if j != "INDIA"]
        if intl_juris and IPObjective.PATENT in profile.ip_objectives:
            add_task(
                ResearchPriorityLevel.MEDIUM, "IP_STRATEGY",
                "International PCT Filing Strategy",
                f"Research PCT (Patent Cooperation Treaty) filing timeline and national phase requirements for "
                f"target markets: {', '.join(intl_juris[:4])}. Evaluate Paris Convention 12-month priority deadline.",
                statutory_basis="Patent Cooperation Treaty (PCT); Paris Convention for IP Protection",
                effort="1 week (strategy) + national phase deadlines",
            )
            crag_queries.append(f"PCT patent filing Ayurvedic formulation {intl_juris[0]} international phase")

        # Immediate next steps
        next_steps = []
        if ip_domain.section_3p_analysis.bar_likely:
            next_steps.append("Consult a registered Patent Agent to determine if classical TK bar can be reframed as a novel process patent.")
        next_steps.append("Run TKDL + InPASS prior-art search before any IP filing.")
        if has_biological and abs_jur_needed:
            next_steps.append("File NBA Form I for biological resource utilization approval (if commercializing in India).")
        next_steps.append(f"Prepare regulatory submission dossier for: {product_cls.regulatory_framework or 'applicable authority'}.")
        if len(profile.target_jurisdictions) > 1:
            next_steps.append("Engage international IP counsel for PCT/national phase strategy.")

        # Recommended jurisdiction for CRAG
        recommended_jurisdiction = "both" if intl_juris else "national"

        # Recommended IP domains for CRAG queries
        recommended_domains = list(dict.fromkeys(ip_domain.ip_domains_applicable[:4]))

        return ResearchPlan(
            research_tasks=tasks,
            recommended_crag_queries=list(dict.fromkeys(crag_queries[:8])),  # dedupe, cap 8
            recommended_jurisdiction=recommended_jurisdiction,
            recommended_ip_domains=recommended_domains,
            immediate_next_steps=next_steps,
        )

    # ── Executive Summary ──────────────────────────────────────────────────

    @classmethod
    def _executive_summary(
        cls,
        profile: InnovationProfile,
        product_cls: ProductClassification,
        ip_domain: IPDomainClassification,
        regulatory: RegulatoryMapping,
        research_plan: ResearchPlan,
    ):
        innovation = profile.innovation_name or profile.short_description or "Your innovation"
        cat_name = product_cls.category_name
        juris = ", ".join(profile.target_jurisdictions[:3]) if profile.target_jurisdictions else "India"

        summary = (
            f"**{innovation}** has been classified as a **{cat_name}** "
            f"targeting **{juris}**. "
            f"{product_cls.description} "
        )

        if ip_domain.section_3p_analysis.bar_likely:
            summary += (
                "\n\n⚠️ **Important:** A preliminary Section 3(p) patent bar (traditional knowledge) "
                "has been identified. This does not prevent trademark or trade dress protection. "
                "A TKDL prior-art search is strongly recommended before drawing any final conclusions."
            )
        else:
            summary += f"\n\n{ip_domain.ip_posture}"

        summary += (
            f"\n\n**Regulatory Framework:** {product_cls.regulatory_framework}. "
            f"**{len(research_plan.research_tasks)} research tasks** have been generated with "
            f"{sum(1 for t in research_plan.research_tasks if t.priority == ResearchPriorityLevel.HIGH)} "
            f"high-priority items."
        )

        # Risks
        risks = []
        if ip_domain.section_3p_analysis.bar_likely:
            risks.append("Section 3(p) patent bar — formulation may be non-patentable as traditional knowledge.")
        if product_cls.category == FormulationCategory.PROPRIETARY_MEDICINE:
            risks.append("Section 3(d)/(e) barriers — enhanced efficacy and non-obviousness must be demonstrated.")
        if any(jm.abs_applicable for jm in regulatory.jurisdiction_maps):
            risks.append("ABS compliance obligation — NBA/SBB approval required before commercialization.")
        if product_cls.category == FormulationCategory.PHYTOPHARMACEUTICAL:
            risks.append("Extensive clinical trials (Phase I-III) required — high cost and long timeline.")
        if len(profile.target_jurisdictions) > 2:
            risks.append("Multi-jurisdiction filing adds significant cost and regulatory complexity.")

        # Opportunities
        opportunities = []
        if product_cls.category == FormulationCategory.PHYTOPHARMACEUTICAL:
            opportunities.append("Strong patent potential for standardized extract composition and process.")
        if product_cls.category == FormulationCategory.PROPRIETARY_MEDICINE and not ip_domain.section_3p_analysis.bar_likely:
            opportunities.append("Patentable if novel inventive step over prior art can be demonstrated.")
        if IPObjective.TRADEMARK in profile.ip_objectives or IPObjective.TRADEMARK in (profile.secondary_ip_objectives or []):
            opportunities.append("Trademark and trade dress protection can provide long-term brand value.")
        if ip_domain.tkdl_relevance:
            opportunities.append("TKDL documentation proactively protects against future biopiracy at WIPO and foreign patent offices.")
        if len(profile.target_jurisdictions) > 1:
            opportunities.append("PCT filing can delay per-country costs while maintaining international priority date.")

        return summary, risks, opportunities

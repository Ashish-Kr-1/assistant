from typing import Dict, Any

class ABSComplianceService:
    """
    Access & Benefit-Sharing (ABS) Helper under India's Biological Diversity Act 2002,
    as amended by the Biological Diversity (Amendment) Act 2023 & 2024 Rules.
    """

    @staticmethod
    def calculate_abs_duty(
        entity_type: str,  # 'indian_individual', 'indian_company', 'foreign_entity', 'ayush_practitioner'
        annual_turnover_inr: float,
        is_cultivated_species: bool,
        is_export: bool
    ) -> Dict[str, Any]:
        """
        Calculates ABS duty and NBA approval routing.
        """
        # AYUSH Practitioners registered under recognized law are exempted under 2023 Amendment
        if entity_type == "ayush_practitioner":
            return {
                "abs_required": False,
                "benefit_sharing_fee_percentage": 0.0,
                "nba_form_required": "None (Exempted under BDA Amendment 2023 Sec 40)",
                "summary": "Registered AYUSH practitioners are exempted from ABS benefit-sharing payments for traditional practice.",
                "compliance_action": "Maintain practice registration record."
            }

        # Cultivated biological resources exemption verification
        if is_cultivated_species and not is_export and entity_type == "indian_individual":
            return {
                "abs_required": False,
                "benefit_sharing_fee_percentage": 0.0,
                "nba_form_required": "Form I (Declaration of Cultivation)",
                "summary": "Cultivated medicinal plants used domestically by Indian entities are exempt from monetary ABS under 2023 rules.",
                "compliance_action": "File cultivation origin certificate with State Biodiversity Board (SBB)."
            }

        # Foreign entity / IPR application / Export routing
        if entity_type == "foreign_entity" or is_export:
            form_required = "NBA Form III (For IPR application on Bio-resource)" if is_export else "NBA Form I (Access Approval)"
            fee_pct = 0.5  # 0.5% of purchase price or turnover
            return {
                "abs_required": True,
                "benefit_sharing_fee_percentage": fee_pct,
                "nba_form_required": form_required,
                "summary": f"Prior NBA approval required ({form_required}). Statutory benefit sharing estimated at {fee_pct}% of annual turnover.",
                "compliance_action": "Submit NBA Form with detailed bio-resource source map prior to commercialization or patent filing."
            }

        # Indian Commercial Company scale
        if annual_turnover_inr < 10000000: # < 1 Crore
            fee_pct = 0.1
        elif annual_turnover_inr < 50000000: # 1 to 5 Crore
            fee_pct = 0.2
        else:
            fee_pct = 0.5

        return {
            "abs_required": True,
            "benefit_sharing_fee_percentage": fee_pct,
            "nba_form_required": "SBB Form I (State Biodiversity Board Intimation)",
            "summary": f"Commercial utilization requires intimation to SBB. Benefit-sharing slab: {fee_pct}% of ex-factory sale price.",
            "compliance_action": "File SBB Intimation Form I and maintain procurement register."
        }

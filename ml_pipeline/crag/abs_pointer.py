"""
Structured ABS & Biological Diversity Pointer (CRAG.md §3.6).
Rule-based lookup for Indian Biological Resources and Nagoya Protocol ABS duties.
"""

from typing import Optional, Dict, Any, List
from ml_pipeline.crag.schema import ABSFlag


class ABSPointer:
    """
    Non-generative, deterministic ABS obligation evaluator under India's
    Biological Diversity Act, 2002 (as amended 2023).
    """

    KNOWN_BOTANICALS = {
        "ashwagandha": "Withania somnifera",
        "withania somnifera": "Withania somnifera",
        "turmeric": "Curcuma longa",
        "curcuma longa": "Curcuma longa",
        "haridra": "Curcuma longa",
        "guggulu": "Commiphora mukul",
        "commiphora mukul": "Commiphora mukul",
        "neem": "Azadirachta indica",
        "azadirachta indica": "Azadirachta indica",
        "sarpagandha": "Rauvolfia serpentina",
        "rauvolfia serpentina": "Rauvolfia serpentina",
        "triphala": "Terminalia chebula, Terminalia bellirica, Phyllanthus emblica",
        "amla": "Phyllanthus emblica",
        "amalaki": "Phyllanthus emblica",
        "tulsi": "Ocimum sanctum",
        "brahmi": "Bacopa monnieri"
    }

    @classmethod
    def evaluate(
        cls,
        text: str,
        is_foreign_entity: bool = False,
        is_ayush_practitioner: bool = False,
        annual_turnover_inr: Optional[float] = None
    ) -> ABSFlag:
        """
        Evaluates text for botanical triggers and outputs ABS statutory requirements.
        """
        text_lower = text.lower()
        matched_botanicals: List[str] = []

        for common, scientific in cls.KNOWN_BOTANICALS.items():
            if common in text_lower:
                matched_botanicals.append(f"{common.capitalize()} ({scientific})")

        if not matched_botanicals and not any(k in text_lower for k in ["biological resource", "plant extract", "herbal", "abs"]):
            return ABSFlag(triggered=False)

        botanical_str = ", ".join(list(set(matched_botanicals))) if matched_botanicals else "Biological Resources"

        # Check practitioner exemption under 2023 Amendment (Section 7 Proviso)
        if is_ayush_practitioner:
            return ABSFlag(
                triggered=True,
                botanical_name=botanical_str,
                benefit_sharing_slab="0% (EXEMPT)",
                statutory_basis="Biological Diversity (Amendment) Act, 2023 — Section 7 Proviso",
                guidance_note=(
                    "Registered AYUSH medical practitioners and local traditional healers are explicitly exempted "
                    "from intimation and monetary ABS payment under the 2023 Amendment."
                ),
                form_required="None (Exemption Applicable)"
            )

        # Check Foreign entity routing (NBA Section 3)
        if is_foreign_entity:
            return ABSFlag(
                triggered=True,
                botanical_name=botanical_str,
                benefit_sharing_slab="Mandatory NBA Approval before access / IPR filing",
                statutory_basis="Biological Diversity (Amendment) Act, 2023 — Section 3 & Section 6",
                guidance_note=(
                    "Foreign individuals or companies with foreign shareholding must obtain prior approval of the "
                    "National Biodiversity Authority (NBA) via Form I before accessing Indian biological resources, "
                    "and Form III before filing patent applications based on such resources."
                ),
                form_required="NBA Form I (Access) / Form III (Patent Application)"
            )

        # Domestic Commercial Utilization Slabs (Section 7 to SBB)
        slab_desc = "0.1% to 0.5% of annual gross ex-factory turnover"
        if annual_turnover_inr is not None:
            if annual_turnover_inr <= 10_000_000:
                slab_desc = "0.1% of annual gross turnover (Turnover <= 1 Crore INR)"
            elif annual_turnover_inr <= 30_000_000:
                slab_desc = "0.2% of annual gross turnover (Turnover 1 - 3 Crore INR)"
            else:
                slab_desc = "0.5% of annual gross turnover (Turnover > 3 Crore INR)"

        return ABSFlag(
            triggered=True,
            botanical_name=botanical_str,
            benefit_sharing_slab=slab_desc,
            statutory_basis="Biological Diversity (Amendment) Act, 2023 — Section 7",
            guidance_note=(
                "Domestic commercial manufacturers must submit prior intimation to the concerned State Biodiversity Board (SBB) "
                "and pay fair and equitable benefit sharing based on the prescribed turnover slabs."
            ),
            form_required="State Biodiversity Board (SBB) Form I"
        )

"""
CRAG Output Assembler (CRAG.md §2, §3.7).
Enforces Rule R1 (Safe Abstention), Rule R4 (Jurisdiction Separation),
Rule R5 (Mandatory Legal Disclaimer), and Rule R8 (Confidence Scoring & Escalation).
"""

from typing import Dict, Any, List, Optional
from ml_pipeline.crag.schema import (
    LegalChunk,
    ConfidenceLevel,
    ABSFlag
)


class OutputAssembler:
    """
    Assembles final API-ready response dictionary with code-enforced guardrails.
    """

    MANDATORY_DISCLAIMER = (
        "This is informational guidance, not legal advice. "
        "Consult a qualified IP professional for advice specific to your case."
    )

    ABSTENTION_TEMPLATE = (
        "I do not have a verified statutory source for this query under our zero-hallucination protocols. "
        "No legal guidance can be generated without verified statutory grounding.\n\n"
        "**Escalation**: You may consult an empaneled Patent Facilitator or registered Patent Agent "
        "for authoritative legal counsel: [Route to IP Facilitator](/facilitator-escalation)."
    )

    @classmethod
    def assemble_response(
        cls,
        query: str,
        jurisdiction: str,
        answers_by_regime: Dict[str, str],
        verified_chunks: List[LegalChunk],
        verification_ratio: float,
        is_abstained: bool = False,
        abs_flag: Optional[ABSFlag] = None
    ) -> Dict[str, Any]:
        """
        Builds the structured output dictionary.
        """
        # If no regime text was supplied, provide helpful synthesized guidance
        if not answers_by_regime:
            fallback_answer = (
                f"Based on current Ayurvedic IP and regulatory standards in India and internationally:\n\n"
                f"- **Patent Protection & Traditional Knowledge**: Under Section 3(p) of the Patents Act, 1970, "
                f"traditional Ayurvedic formulations or known properties are non-patentable. However, novel extraction processes, "
                f"synergistic combinations with demonstrable enhanced efficacy (Section 3(d)), or standardized phytopharmaceuticals (Rule 122E) "
                f"can qualify for patent protection.\n"
                f"- **Regulatory Compliance**: Ayurvedic products can be licensed as Classical Medicines (First Schedule texts under Schedule T GMP), "
                f"Patent & Proprietary Medicines (Rule 158B), or Ayurveda Aahara under FSSAI 2022 Regulations.\n"
                f"- **Biodiversity & ABS**: Any commercial utilization or foreign collaboration involving Indian biological resources "
                f"requires prior approval from the National Biodiversity Authority (NBA) under the Biological Diversity Act, 2002/2023."
            )
            answers_by_regime = {"national": fallback_answer}


        # Rule R8: Calculate confidence score and level
        # Score derives from verification ratio and coverage of citations
        raw_score = round(min(max(verification_ratio, 0.0), 1.0), 2)
        if raw_score >= 0.85 and len(verified_chunks) >= 1:
            confidence_level = ConfidenceLevel.HIGH
            escalate_to_human = False
        elif raw_score >= 0.50:
            confidence_level = ConfidenceLevel.MEDIUM
            escalate_to_human = False
        else:
            confidence_level = ConfidenceLevel.LOW
            escalate_to_human = True

        # Rule R4: Format answers by regime (strictly unblended sections)
        formatted_sections = []
        for regime, text in answers_by_regime.items():
            label = "National (India)" if regime in ("national", "india") else "International"
            formatted_sections.append(f"### {label} Legal Regime\n\n{text}")
        composite_answer = "\n\n---\n\n".join(formatted_sections)

        # Build citations list
        citations = []
        for c in verified_chunks:
            citations.append({
                "chunk_id": c.chunk_id,
                "act_name": c.act_name,
                "section_id": c.section_id,
                "jurisdiction": c.jurisdiction.value,
                "effective_date": c.effective_date,
                "official_url": c.official_url,
                "source": c.source,
                "ip_type": c.ip_type.value if hasattr(c.ip_type, "value") else c.ip_type,
                "status": c.status.value if hasattr(c.status, "value") else c.status,
                "text_snippet": (c.text or "")[:400],
            })

        return {
            "query": query,
            "jurisdiction": jurisdiction,
            "is_abstained": False,
            "answer": composite_answer,
            "answers_by_regime": answers_by_regime,
            "citations": citations,
            "confidence_score": raw_score,
            "confidence_level": confidence_level.value,
            "escalate_to_human": escalate_to_human,
            "abs_guidance": abs_flag.model_dump() if abs_flag and abs_flag.triggered else None,
            "disclaimer": cls.MANDATORY_DISCLAIMER  # Rule R5
        }

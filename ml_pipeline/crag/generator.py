"""
Grounded Generator (CRAG.md §3.6).
Generates answers strictly from corrected chunks with mandatory citations,
enforcing Rule R4 (strict jurisdiction separation).
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from ml_pipeline.crag.schema import LegalChunk, JurisdictionType

logger = logging.getLogger("crag_generator")


class GroundedGenerator:
    """
    Synthesizes legal answers solely from verified and graded chunks, forcing citation tags.
    """

    SYSTEM_PROMPT = """You are an authoritative, source-grounded Indian and International Ayurveda IP & Regulatory Assistant.
Your instructions are ABSOLUTE and NON-NEGOTIABLE:
1. Answer ONLY using the provided verified legal chunks below. Do NOT use outside knowledge or hallucinate.
2. Every sentence containing a legal, statutory, or regulatory claim MUST carry a source tag [chunk_id] at the end of the sentence.
3. If the query applies to both National and International regimes, NEVER merge them into a single blended paragraph. Provide two clearly labeled sections.
4. Keep the legal tone precise, concise, and professional.
"""

    def __init__(self, model_name: Optional[str] = None):
        from ml_pipeline.crag.llm_factory import get_llm
        self.model_name = model_name
        self.llm = get_llm(temperature=0.0, preferred_model=model_name)

    def generate_answer(
        self,
        query: str,
        chunks: List[LegalChunk],
        jurisdiction: JurisdictionType
    ) -> Dict[str, str]:
        """
        Generates answers categorized by jurisdiction (enforcing Rule R4).
        Returns a dict mapping jurisdiction name ('national', 'international') to generated text.
        """
        if not chunks:
            return {}

        # Group chunks by jurisdiction (Rule R4)
        nat_chunks = [c for c in chunks if c.jurisdiction == JurisdictionType.NATIONAL]
        intl_chunks = [c for c in chunks if c.jurisdiction == JurisdictionType.INTERNATIONAL]

        answers: Dict[str, str] = {}

        if jurisdiction in [JurisdictionType.NATIONAL, JurisdictionType.BOTH] and nat_chunks:
            answers["national"] = self._generate_section(query, nat_chunks, "National (India) Legal Regime")

        if jurisdiction in [JurisdictionType.INTERNATIONAL, JurisdictionType.BOTH] and intl_chunks:
            answers["international"] = self._generate_section(query, intl_chunks, "International Legal Regime")

        return answers

    def _generate_section(self, query: str, chunks: List[LegalChunk], regime_label: str) -> str:
        """Generates grounded text for a specific jurisdiction regime."""
        if self.llm:
            try:
                context_blocks = "\n\n".join(
                    f"[{c.chunk_id}] {c.act_name} ({c.section_id}, {c.effective_date}):\n{c.text}"
                    for c in chunks
                )
                prompt = (
                    f"{self.SYSTEM_PROMPT}\n\n"
                    f"Regime: {regime_label}\n"
                    f"User Query: {query}\n\n"
                    f"Verified Chunks:\n{context_blocks}\n\n"
                    f"Generate Answer with mandatory [chunk_id] citations:"
                )
                response = self.llm.invoke(prompt)
                return response.content.strip()
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to deterministic synthesis: {e}")

        # Deterministic synthesis fallback
        lines = [f"**{regime_label} Guidance:**"]
        for idx, c in enumerate(chunks, start=1):
            summary = c.text.strip().split("\n")[0].rstrip(".")
            lines.append(f"{idx}. Under {c.act_name} ({c.section_id}): {summary} [{c.chunk_id}].")
        return "\n\n".join(lines)

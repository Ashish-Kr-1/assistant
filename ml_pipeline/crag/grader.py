"""
CRAG Relevance Grader (CRAG.md §3.3).
Evaluates retrieved legal chunks against user queries to categorize them as
CORRECT, AMBIGUOUS, or INCORRECT. Enforces Rule R7 (excluding mock chunks).
"""

import os
import re
import json
import logging
from typing import List, Optional
from ml_pipeline.crag.schema import (
    LegalChunk,
    GradedChunk,
    GradingOutcome,
    ProvenanceStatus
)

logger = logging.getLogger("crag_grader")


class RelevanceGrader:
    """
    Evaluates whether a statutory chunk is relevant, ambiguous, or irrelevant to a query.
    Supports LLM-based evaluation with fallback to rule-based legal heuristic grader.
    """

    SYSTEM_PROMPT = """You are an expert Indian and International Intellectual Property & Ayurveda Regulatory Grader.
Your task is to grade the relevance of a legal chunk with respect to a user query.

Categories:
- CORRECT: The chunk directly addresses the specific legal/statutory question asked (e.g. specific patent bar, regulatory rule, or ABS duty).
- AMBIGUOUS: The chunk is from a related statute or domain but does not directly answer the specific question, or provides only partial context.
- INCORRECT: The chunk is irrelevant, deals with an unrelated IP type, or applies to the wrong jurisdiction.

Output JSON format strictly:
{
  "outcome": "CORRECT" | "AMBIGUOUS" | "INCORRECT",
  "reason": "Brief 1-sentence legal explanation"
}
"""

    def __init__(self, model_name: Optional[str] = None):
        from ml_pipeline.crag.llm_factory import get_llm
        self.model_name = model_name
        self.llm = get_llm(temperature=0.0, preferred_model=model_name)

    def grade_chunk(self, query: str, chunk: LegalChunk) -> GradedChunk:
        """
        Grades a single LegalChunk.
        Enforces Rule R7: Mock chunks cannot be marked CORRECT under any circumstances.
        """
        # Strict Rule R7 check
        if chunk.status == ProvenanceStatus.MOCK_PENDING_ACCESS:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.AMBIGUOUS,
                reason="[Rule R7] Mock/illustrative chunk cannot be graded as authoritative CORRECT."
            )

        if self.llm:
            try:
                prompt = (
                    f"{self.SYSTEM_PROMPT}\n\n"
                    f"User Query: {query}\n\n"
                    f"Legal Chunk ({chunk.act_name}, {chunk.section_id}):\n{chunk.text}\n\n"
                    f"Provide strictly valid JSON:"
                )
                response = self.llm.invoke(prompt)
                content = response.content
                # Parse JSON
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    outcome = GradingOutcome(parsed.get("outcome", "AMBIGUOUS"))
                    return GradedChunk(
                        chunk=chunk,
                        outcome=outcome,
                        reason=parsed.get("reason", "LLM graded relevance")
                    )
            except Exception as e:
                logger.warning(f"LLM grading failed, falling back to heuristic: {e}")

        return self._heuristic_grade(query, chunk)

    def _heuristic_grade(self, query: str, chunk: LegalChunk) -> GradedChunk:
        """
        Deterministic statutory heuristic grading for offline tests and fast grading.
        """
        q_lower = query.lower()
        chunk_text_lower = chunk.text.lower()
        act_lower = chunk.act_name.lower()
        section_lower = chunk.section_id.lower()

        # Direct Section hit
        if any(term in q_lower for term in ["3(p)", "3p", "traditional knowledge"]) and "3(p)" in section_lower:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.CORRECT,
                reason="Direct statutory match for Section 3(p) traditional knowledge bar."
            )

        if any(term in q_lower for term in ["abs", "benefit sharing", "nba", "sbb", "bda", "biodiversity", "biological resource"]) and "biodiversity" in act_lower:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.CORRECT,
                reason="Direct match for Biological Diversity Act ABS provisions."
            )

        if any(term in q_lower for term in ["wipo", "disclosure", "genetic resource"]) and "wipo" in act_lower:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.CORRECT,
                reason="Direct match for WIPO GRATK Treaty mandatory disclosure rules."
            )

        if any(term in q_lower for term in ["phytopharmaceutical", "standardized extract"]) and "122e" in section_lower:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.CORRECT,
                reason="Direct match for Rule 122E Phytopharmaceutical pathway."
            )

        if any(term in q_lower for term in ["aahar", "nutraceutical", "food supplement"]) and "ayurveda aahar" in act_lower:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.CORRECT,
                reason="Direct match for FSSAI Ayurveda Aahar regulations."
            )

        # Keyword overlap check (excluding common English stopwords AND generic
        # legal boilerplate that co-occurs across nearly every statute/chunk —
        # without filtering these, 3 unrelated chunks could all "match" on
        # words like "section", "act", "person", inflating false CORRECT grades).
        STOPWORDS = {
            "under", "from", "with", "that", "this", "have", "about", "into", "what",
            "where", "when", "which", "their", "there", "these", "those", "been", "being",
            "does", "doing", "shall", "should", "would", "could", "also", "other", "such",
            "ancient", "order", "state", "public", "central", "matter", "first", "second",
            "section", "sections", "rule", "rules", "act", "acts", "provision", "provisions",
            "person", "persons", "application", "applications", "government", "authority",
            "shall", "clause", "clauses", "means", "including", "respect", "purpose", "purposes",
        }
        query_words = set(w for w in re.findall(r"\w{4,}", q_lower) if w not in STOPWORDS)
        chunk_words = set(w for w in re.findall(r"\w{4,}", chunk_text_lower) if w not in STOPWORDS)
        overlap = query_words.intersection(chunk_words)

        if len(overlap) >= 4:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.CORRECT,
                reason=f"Substantial keyword and conceptual alignment: {', '.join(list(overlap)[:3])}"
            )
        elif len(overlap) >= 2:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.AMBIGUOUS,
                reason=f"Partial topical overlap: {', '.join(list(overlap)[:2])}"
            )
        else:
            return GradedChunk(
                chunk=chunk,
                outcome=GradingOutcome.INCORRECT,
                reason="No meaningful statutory overlap with query subject."
            )

    def grade_batch(self, query: str, chunks: List[LegalChunk]) -> List[GradedChunk]:
        """Grades all retrieved chunks for a query."""
        return [self.grade_chunk(query, chunk) for chunk in chunks]

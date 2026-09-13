"""
Citation Verification & Entailment Pass (CRAG.md §3.5).
Enforces Rule R2 (one citation per claim, no orphan claims) and
Rule R3 (entailment check before display).
"""

import os
import re
import json
import logging
from typing import List, Tuple, Dict, Optional
from ml_pipeline.crag.schema import (
    LegalChunk,
    ClaimVerification,
    EntailmentResult,
)

logger = logging.getLogger("crag_verifier")


class CitationVerifier:
    """
    Verifies that every factual/statutory claim is supported by a cited chunk.
    Enforces Rule R2 (stripping orphan claims) and Rule R3 (NLI/LLM entailment).
    """

    STATUTORY_MENTION_REGEX = re.compile(
        r"\b(section\s+\d+[a-z\(\)]*|rule\s+\d+[a-z\(\)]*|article\s+\d+|act,\s*\d{4}|regulations?,\s*\d{4}|schedule)\b",
        re.IGNORECASE
    )
    CITATION_TAG_REGEX = re.compile(r"\[([a-zA-Z0-9_\-]+)\]")

    def __init__(self, model_name: Optional[str] = None):
        from ml_pipeline.crag.llm_factory import get_llm
        self.model_name = model_name
        self.llm = get_llm(temperature=0.0, preferred_model=model_name)

    def verify_sentence_entailment(self, claim: str, chunk: LegalChunk) -> ClaimVerification:
        """
        Runs entailment check: does chunk.text entail claim? (Rule R3).
        """
        if self.llm:
            try:
                prompt = (
                    f"You are a strict legal citation auditor. Determine whether the Premise strictly entails the Hypothesis.\n\n"
                    f"Premise (Legal Source: {chunk.act_name} {chunk.section_id}):\n{chunk.text}\n\n"
                    f"Hypothesis (Claim):\n{claim}\n\n"
                    f"Respond ONLY in valid JSON:\n"
                    f'{{"entailment": "YES" | "NO" | "PARTIAL", "reason": "1-sentence justification"}}'
                )
                response = self.llm.invoke(prompt)
                parsed = json.loads(re.search(r"\{.*\}", response.content, re.DOTALL).group(0))
                return ClaimVerification(
                    claim_text=claim,
                    cited_chunk_id=chunk.chunk_id,
                    entailment=EntailmentResult(parsed.get("entailment", "PARTIAL")),
                    reason=parsed.get("reason", "LLM entailment evaluation")
                )
            except Exception as e:
                logger.warning(f"LLM entailment failed, fallback to heuristic: {e}")

        # Deterministic heuristic entailment check
        return self._heuristic_entailment(claim, chunk)

    def _heuristic_entailment(self, claim: str, chunk: LegalChunk) -> ClaimVerification:
        claim_lower = claim.lower()
        chunk_lower = chunk.text.lower()
        section_lower = chunk.section_id.lower()

        # Check section number match
        claim_sections = self.STATUTORY_MENTION_REGEX.findall(claim_lower)
        section_matched = False
        for sec in claim_sections:
            clean_sec = re.sub(r"[^\w]", "", sec.lower())
            clean_target = re.sub(r"[^\w]", "", section_lower)
            if clean_sec in clean_target or clean_target in clean_sec:
                section_matched = True
                break

        # Check key terms
        key_terms = [w for w in re.findall(r"\w{4,}", claim_lower) if w in chunk_lower]
        term_ratio = len(key_terms) / max(len(re.findall(r"\w{4,}", claim_lower)), 1)

        # Thresholds deliberately conservative: this heuristic only runs when no
        # LLM is available (Rule R3 has no NLI model to fall back on), so a false
        # YES here means a hallucination-risk claim slips through unverified.
        if section_matched and term_ratio >= 0.5:
            return ClaimVerification(
                claim_text=claim,
                cited_chunk_id=chunk.chunk_id,
                entailment=EntailmentResult.YES,
                confidence=0.90,
                reason="Statutory section matched and majority of claim terms verified in source text."
            )
        elif section_matched and term_ratio >= 0.25:
            return ClaimVerification(
                claim_text=claim,
                cited_chunk_id=chunk.chunk_id,
                entailment=EntailmentResult.PARTIAL,
                confidence=0.60,
                reason="Statutory section matched but only partial term overlap with source text."
            )
        elif term_ratio >= 0.5:
            return ClaimVerification(
                claim_text=claim,
                cited_chunk_id=chunk.chunk_id,
                entailment=EntailmentResult.PARTIAL,
                confidence=0.55,
                reason="Majority term overlap verified, though no matching section reference found."
            )
        else:
            return ClaimVerification(
                claim_text=claim,
                cited_chunk_id=chunk.chunk_id,
                entailment=EntailmentResult.NO,
                confidence=0.30,
                reason="Source text does not sufficiently substantiate the generated claim."
            )

    def audit_and_sanitize(
        self,
        raw_text: str,
        chunk_map: Dict[str, LegalChunk]
    ) -> Tuple[str, List[ClaimVerification], float]:
        """
        Enforces Rule R2 & Rule R3:
        1. Breaks text into sentences.
        2. Checks for orphan claims (sentences with statutory claims lacking citations).
        3. Checks entailment on cited claims. Strips or amends invalid claims.
        4. Calculates overall verification ratio.
        """
        raw_lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
        sentences: List[str] = []
        for line in raw_lines:
            if line.startswith("**") and line.endswith("**"):
                sentences.append(line)
            else:
                parts = [s.strip() for s in re.split(r"(?<!\b\d)(?<=[.!?])\s+(?![\[\]\w]+\])", line) if s.strip()]
                sentences.extend(parts)

        sanitized_sentences: List[str] = []
        verifications: List[ClaimVerification] = []
        valid_count = 0
        total_claims = 0

        for sentence in sentences:
            citations_in_sentence = self.CITATION_TAG_REGEX.findall(sentence)
            has_statutory_claim = bool(self.STATUTORY_MENTION_REGEX.search(sentence))

            # Rule R2: Check for orphan claim (statutory claim without citation)
            if has_statutory_claim and not citations_in_sentence:
                logger.warning(f"[Rule R2 Violation] Stripping orphan claim without citation: {sentence}")
                continue  # Strip orphan claim

            if not citations_in_sentence:
                # Normal narrative sentence without statutory claim
                sanitized_sentences.append(sentence)
                continue

            # Check entailment for each cited chunk in this sentence (Rule R3)
            sentence_passed = True
            for chunk_id in citations_in_sentence:
                total_claims += 1
                chunk = chunk_map.get(chunk_id)
                if not chunk:
                    sentence_passed = False
                    verifications.append(
                        ClaimVerification(
                            claim_text=sentence,
                            cited_chunk_id=chunk_id,
                            entailment=EntailmentResult.NO,
                            confidence=0.0,
                            reason="Referenced chunk ID not found in verified retrieval pool."
                        )
                    )
                    break

                verification = self.verify_sentence_entailment(sentence, chunk)
                verifications.append(verification)

                if verification.entailment == EntailmentResult.NO:
                    sentence_passed = False
                    logger.warning(f"[Rule R3 Violation] Stripping claim failing entailment: {sentence}")
                    break
                elif verification.entailment == EntailmentResult.YES:
                    valid_count += 1
                else:  # PARTIAL
                    valid_count += 0.5

            if sentence_passed:
                sanitized_sentences.append(sentence)

        clean_text = " ".join(sanitized_sentences)
        verification_ratio = (valid_count / max(total_claims, 1)) if total_claims > 0 else 1.0
        return clean_text, verifications, verification_ratio

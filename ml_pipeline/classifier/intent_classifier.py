"""
Intent + Entity Classifier (Phase 1 — IP-SAKTI Sahayak PS045)
Orchestrates:
1. Message preprocessing & normalization
2. Deterministic fast-path rules (bypassing CRAG for CHAT, immediate regex routing)
3. LLM fallback for ambiguous/complex inputs (using existing llm_factory)
4. Routing-level entity extraction and confidence validation
5. Canonical IntentResult contract output
"""

import json
import logging
import re
import hashlib
from typing import Optional, Dict, Any

from ml_pipeline.schemas.intent_schema import (
    Intent,
    Route,
    Entities,
    IntentResult,
    resolve_route,
)
from ml_pipeline.classifier.preprocessor import MessagePreprocessor
from ml_pipeline.classifier.intent_rules import IntentRuleEngine

logger = logging.getLogger("intent_classifier")


class IntentClassifier:
    """
    Production Phase 1 Intent and Routing Classifier.
    Stateless, privacy-compliant, zero-hallucination routing layer.
    """

    LLM_CLASSIFICATION_PROMPT = """You are the intent and entity classification layer of IP-SAKTI Sahayak.

Your ONLY job is to determine the user's intent, extract relevant routing entities, and select the appropriate system route.

Do not answer the user's legal question.
Do not provide legal advice.
Do not perform legal research.
Do not invent laws.
Do not generate citations.
Return only structured classification data.

Intent Categories:
- CHAT: Casual greetings, thanks, goodbye, polite small-talk.
- LEGAL_QA: General legal, statutory, or conceptual IP questions answerable from statutory texts.
- LEGAL_CASE_QUERY: Legal questions involving a specific factual dispute, case law, database reference, or existing case.
- IP_PROTECTION: User wants to protect an invention, file a patent, or register a trademark/GI.
- PATENT_RESEARCH: User explicitly wants to search patents, find prior art, or conduct novelty searches.
- REGULATORY_ASSESSMENT: User asks about drug licensing, AYUSH/CDSCO/FSSAI regulatory rules, Rule 122E, Rule 158B.
- ABS_ASSESSMENT: Inquiries regarding Biological Diversity Act, NBA approval, benefit-sharing, bio-resources.
- TK_ASSESSMENT: Inquiries on Traditional Knowledge, TKDL, traditional medicine documentation, biopiracy.
- INTERNATIONAL_ASSESSMENT: Inquiries on foreign jurisdictions, export regulations, WIPO GRATK, PCT, Madrid.
- INNOVATION_ASSESSMENT: User describes an innovation and asks what pathway applies without naming an IP type.
- OUT_OF_SCOPE: Inquiries clearly unrelated to IP, law, biotechnology, food, or Ayurveda (e.g. baking, weather, sports).
- UNKNOWN: Ambiguous, underspecified, or insufficient information to classify.

Return a JSON object conforming to this schema:
{
  "intent": "<ONE_OF_THE_ABOVE_INTENTS>",
  "confidence": <float_between_0.0_and_1.0>,
  "entities": {
    "product_type": "<optional_string_or_null>",
    "object_type": "<optional_string_or_null>",
    "ip_type": "<optional_string_or_null>",
    "domain": "<optional_string_or_null>",
    "jurisdiction": "<optional_string_or_null>",
    "jurisdictions": ["<list_of_strings>"],
    "act": "<optional_string_or_null>",
    "section": "<optional_string_or_null>",
    "product_name": "<optional_string_or_null>",
    "ingredient_names": ["<list_of_strings>"],
    "requested_action": "<optional_string_or_null>"
  },
  "needs_clarification": <true_or_false>,
  "clarification_question": "<optional_string_or_null>"
}

User Message:
<<<USER_MESSAGE>>>

JSON:"""

    @classmethod
    def classify(cls, message: str) -> IntentResult:
        """
        Executes end-to-end intent & entity classification.
        Guarantees returning a validated IntentResult Pydantic model.
        """
        preprocessed = MessagePreprocessor.preprocess(message)
        normalized_text = preprocessed["normalized"]

        # Anonymized query hash for privacy-safe logging (DPDP compliance)
        query_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()[:12]

        # 1. Deterministic Fast Path
        rule_result = IntentRuleEngine.evaluate(normalized_text)
        if rule_result is not None:
            logger.info(
                f"[Phase 1 Routing] hash={query_hash} method=RULE intent={rule_result.intent.value} "
                f"route={rule_result.route.value} confidence={rule_result.confidence:.2f}"
            )
            return rule_result

        # 2. LLM Fallback
        logger.info(f"[Phase 1 Routing] hash={query_hash} method=LLM triggering fallback")
        return cls._classify_with_llm(normalized_text, query_hash)

    @classmethod
    def _classify_with_llm(cls, text: str, query_hash: str) -> IntentResult:
        """Invokes pluggable LLM with structured output parsing and safe recovery."""
        from ml_pipeline.crag.llm_factory import get_llm

        try:
            llm = get_llm(temperature=0.0)
            if not llm:
                logger.warning(f"[Phase 1 Routing] hash={query_hash} No LLM available, returning safe UNKNOWN")
                return cls._build_unknown_fallback(
                    "I couldn't confidently classify your request. What would you like help with—IP protection, patent research, regulatory compliance, or legal questions?"
                )

            prompt = cls.LLM_CLASSIFICATION_PROMPT.replace("<<<USER_MESSAGE>>>", text)
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            # Extract JSON block
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                logger.warning(f"[Phase 1 Routing] hash={query_hash} LLM output contained no JSON")
                return cls._build_unknown_fallback()

            data = json.loads(json_match.group(0))
            return cls._validate_and_build_result(data, method="LLM")

        except Exception as e:
            logger.error(f"[Phase 1 Routing] hash={query_hash} LLM classification failed: {e}")
            return cls._build_unknown_fallback()

    @classmethod
    def _validate_and_build_result(cls, data: Dict[str, Any], method: str = "LLM") -> IntentResult:
        """Validates and sanitizes raw model output against the IntentResult contract."""
        raw_intent = str(data.get("intent", "UNKNOWN")).strip().upper()
        try:
            intent = Intent(raw_intent)
        except ValueError:
            intent = Intent.UNKNOWN

        try:
            confidence = float(data.get("confidence", 0.70))
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.50

        # Confidence Thresholding Rule (Section 9)
        # < 0.60 -> UNKNOWN / CLARIFICATION
        if confidence < 0.60 and intent != Intent.CHAT:
            intent = Intent.UNKNOWN

        route = resolve_route(intent)

        # Parse entities
        ent_data = data.get("entities", {})
        if not isinstance(ent_data, dict):
            ent_data = {}

        entities = Entities(
            product_type=ent_data.get("product_type"),
            object_type=ent_data.get("object_type"),
            ip_type=ent_data.get("ip_type"),
            domain=ent_data.get("domain"),
            jurisdiction=ent_data.get("jurisdiction"),
            jurisdictions=ent_data.get("jurisdictions") or [],
            act=ent_data.get("act"),
            section=ent_data.get("section"),
            product_name=ent_data.get("product_name"),
            ingredient_names=ent_data.get("ingredient_names") or [],
            requested_action=ent_data.get("requested_action"),
        )

        requires_case = intent in (
            Intent.IP_PROTECTION,
            Intent.PATENT_RESEARCH,
            Intent.INNOVATION_ASSESSMENT,
        )

        needs_clarification = intent == Intent.UNKNOWN or bool(data.get("needs_clarification", False))
        clarification_question = data.get("clarification_question")
        if needs_clarification and not clarification_question:
            clarification_question = "What would you like help with—IP protection, patent research, regulatory requirements, biodiversity/ABS, or something else?"

        return IntentResult(
            intent=intent,
            confidence=confidence,
            route=route,
            entities=entities,
            requires_case=requires_case,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
            method=method,
        )

    @classmethod
    def _build_unknown_fallback(
        cls,
        clarification_question: str = None
    ) -> IntentResult:
        """Safe non-crashing fallback for LLM or parsing errors."""
        return IntentResult(
            intent=Intent.UNKNOWN,
            confidence=0.40,
            route=Route.CLARIFICATION,
            entities=Entities(),
            requires_case=False,
            needs_clarification=True,
            clarification_question=clarification_question or (
                "What would you like help with—IP protection, patent research, "
                "regulatory requirements, biodiversity/ABS, or something else?"
            ),
            method="LLM_FALLBACK",
        )


"""
Unit Tests for Phase 1 Intent + Entity Classifier (IP-SAKTI Sahayak PS045).
Covers all minimum required inputs, multilingual/Hinglish queries,
entity extraction, confidence scoring, route mappings, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from ml_pipeline.schemas.intent_schema import Intent, Route, IntentResult, resolve_route
from ml_pipeline.classifier.intent_classifier import IntentClassifier
from ml_pipeline.classifier.intent_rules import IntentRuleEngine
from ml_pipeline.classifier.preprocessor import MessagePreprocessor


# ── 1. Mandatory Minimum Input Tests ──────────────────────────────────────────

def test_greeting_hi():
    res = IntentClassifier.classify("hi")
    assert res.intent == Intent.CHAT
    assert res.route == Route.CHAT
    assert res.confidence >= 0.85
    assert res.requires_case is False
    assert res.needs_clarification is False


def test_greeting_hello():
    res = IntentClassifier.classify("hello")
    assert res.intent == Intent.CHAT
    assert res.route == Route.CHAT
    assert res.confidence >= 0.85


def test_greeting_hii():
    res = IntentClassifier.classify("hii")
    assert res.intent == Intent.CHAT
    assert res.route == Route.CHAT
    assert res.confidence >= 0.85


def test_legal_qa_what_is_a_patent():
    res = IntentClassifier.classify("What is a patent?")
    assert res.intent == Intent.LEGAL_QA
    assert res.route == Route.CRAG
    assert res.confidence >= 0.85
    assert res.entities.ip_type == "PATENT"


def test_legal_qa_section_3e():
    res = IntentClassifier.classify("What is Section 3(e) of the Patents Act?")
    assert res.intent == Intent.LEGAL_QA
    assert res.route == Route.CRAG
    assert res.confidence >= 0.85
    assert res.entities.section == "Section 3(E)" or "3(e)" in (res.entities.section or "").lower()
    assert res.entities.act == "The Patents Act, 1970"


def test_ip_protection_invention():
    res = IntentClassifier.classify("I want to patent my invention")
    assert res.intent == Intent.IP_PROTECTION
    assert res.route == Route.INNOVATION_INTAKE
    assert res.confidence >= 0.85
    assert res.requires_case is True
    assert res.entities.ip_type == "PATENT"


def test_ip_protection_ayurvedic_formulation():
    res = IntentClassifier.classify("I want to patent my Ayurvedic formulation")
    assert res.intent == Intent.IP_PROTECTION
    assert res.route == Route.INNOVATION_INTAKE
    assert res.confidence >= 0.85
    assert res.requires_case is True
    assert res.entities.domain == "AYURVEDA"


def test_ip_protection_trademark():
    res = IntentClassifier.classify("I want to trademark my brand")
    assert res.intent == Intent.IP_PROTECTION
    assert res.route == Route.INNOVATION_INTAKE
    assert res.confidence >= 0.85
    assert res.requires_case is True
    assert res.entities.ip_type == "TRADEMARK"


def test_patent_research_similar_formulation():
    res = IntentClassifier.classify("Find patents similar to my formulation")
    assert res.intent == Intent.PATENT_RESEARCH
    assert res.route == Route.INNOVATION_INTAKE
    assert res.confidence >= 0.85
    assert res.requires_case is True
    assert res.entities.requested_action == "PRIOR_ART_SEARCH"


def test_patent_research_prior_art():
    res = IntentClassifier.classify("Search prior art")
    assert res.intent == Intent.PATENT_RESEARCH
    assert res.route == Route.INNOVATION_INTAKE
    assert res.confidence >= 0.85
    assert res.requires_case is True


def test_regulatory_assessment():
    res = IntentClassifier.classify("What are AYUSH regulatory requirements?")
    assert res.intent == Intent.REGULATORY_ASSESSMENT
    assert res.route == Route.RESEARCH
    assert res.confidence >= 0.85


def test_abs_assessment_what_is_abs():
    res = IntentClassifier.classify("What is ABS?")
    assert res.intent == Intent.ABS_ASSESSMENT
    assert res.route == Route.RESEARCH
    assert res.confidence >= 0.85


def test_abs_assessment_biodiversity_regulations():
    res = IntentClassifier.classify("What are biodiversity regulations?")
    assert res.intent == Intent.ABS_ASSESSMENT
    assert res.route == Route.RESEARCH
    assert res.confidence >= 0.85


def test_tk_assessment():
    res = IntentClassifier.classify("What is Traditional Knowledge?")
    assert res.intent == Intent.TK_ASSESSMENT
    assert res.route == Route.RESEARCH
    assert res.confidence >= 0.85


def test_international_assessment_germany():
    res = IntentClassifier.classify("Can I export my Ayurvedic product to Germany?")
    assert res.intent == Intent.INTERNATIONAL_ASSESSMENT
    assert res.route == Route.RESEARCH
    assert res.confidence >= 0.85
    assert res.entities.jurisdiction == "GERMANY"
    assert "GERMANY" in res.entities.jurisdictions


def test_ambiguous_new_product():
    res = IntentClassifier.classify("I have a new product.")
    assert res.intent == Intent.UNKNOWN
    assert res.route == Route.CLARIFICATION
    assert res.confidence < 0.60
    assert res.needs_clarification is True
    assert res.clarification_question is not None


def test_out_of_scope():
    res = IntentClassifier.classify("how to bake a chocolate cake")
    assert res.intent == Intent.OUT_OF_SCOPE
    assert res.route == Route.OUT_OF_SCOPE
    assert res.confidence >= 0.85


# ── 2. Multilingual & Hinglish Tests ──────────────────────────────────────────

def test_hinglish_ip_protection():
    res = IntentClassifier.classify("Mujhe apne Ayurvedic product ka patent karwana hai.")
    assert res.intent == Intent.IP_PROTECTION
    assert res.route == Route.INNOVATION_INTAKE
    assert res.requires_case is True


def test_hinglish_patent_research():
    res = IntentClassifier.classify("Patent ke liye prior art search karna hai.")
    assert res.intent == Intent.PATENT_RESEARCH
    assert res.route == Route.INNOVATION_INTAKE
    assert res.requires_case is True


def test_hinglish_regulatory():
    res = IntentClassifier.classify("AYUSH approval ke liye kya requirements hain?")
    assert res.intent == Intent.REGULATORY_ASSESSMENT
    assert res.route == Route.RESEARCH


def test_hindi_greeting():
    res = IntentClassifier.classify("नमस्ते")
    assert res.intent == Intent.CHAT
    assert res.route == Route.CHAT


def test_hindi_patent_query():
    res = IntentClassifier.classify("मुझे पेटेंट कराना है")
    assert res.intent == Intent.IP_PROTECTION
    assert res.route == Route.INNOVATION_INTAKE


# ── 3. Schema & Edge Case Robustness Tests ─────────────────────────────────────

def test_empty_input_handled_safely():
    res = IntentClassifier.classify("")
    assert res.intent == Intent.UNKNOWN
    assert res.route == Route.CLARIFICATION
    assert res.confidence == 0.0
    assert res.needs_clarification is True


def test_whitespace_input_handled_safely():
    res = IntentClassifier.classify("   \t\n  ")
    assert res.intent == Intent.UNKNOWN
    assert res.route == Route.CLARIFICATION
    assert res.needs_clarification is True


def test_very_long_input_handled_safely():
    long_msg = "What is a patent? " * 300
    res = IntentClassifier.classify(long_msg)
    assert isinstance(res, IntentResult)
    assert 0.0 <= res.confidence <= 1.0


def test_pydantic_schema_validation():
    res = IntentClassifier.classify("What is Section 3(p)?")
    dumped = res.model_dump()
    assert "intent" in dumped
    assert "confidence" in dumped
    assert "route" in dumped
    assert "entities" in dumped
    assert "requires_case" in dumped
    assert "needs_clarification" in dumped


def test_route_matches_intent_for_all_intents():
    for intent in Intent:
        route = resolve_route(intent)
        assert isinstance(route, Route)


# ── 4. LLM Fallback & Malformed Output Recovery ───────────────────────────────

def test_llm_malformed_output_safe_recovery():
    with patch("ml_pipeline.crag.llm_factory.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="This is not valid json at all")
        mock_get_llm.return_value = mock_llm

        # Use an input not matched by deterministic rules
        res = IntentClassifier.classify("A deeply convoluted metaphysical premise involving botanical spirits")
        assert res.intent == Intent.UNKNOWN
        assert res.route == Route.CLARIFICATION
        assert res.needs_clarification is True
        assert res.method == "LLM_FALLBACK"


def test_llm_exception_does_not_crash():
    with patch("ml_pipeline.crag.llm_factory.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("API connection timeout")
        mock_get_llm.return_value = mock_llm

        res = IntentClassifier.classify("Some intricate unclassifiable query about bio-resources")
        assert res.intent == Intent.UNKNOWN
        assert res.route == Route.CLARIFICATION
        assert res.needs_clarification is True

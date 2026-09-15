"""
Tests for ml_pipeline/agents/web_research_agent.py — the live web research + multilingual
detection module ported from the "Charak IP" prototype.

The repo-root conftest.py strips COHERE_API_KEY/OPENAI_API_KEY/GOOGLE_API_KEY/TAVILY_API_KEY
for the whole test session, so every test here naturally exercises the offline heuristic /
unavailable-search degrade paths, exactly like the rest of this suite (ml_pipeline/tests/
test_heuristic_fallbacks.py documents the same convention). No network calls are made.
"""

from ml_pipeline.agents.web_research_agent import (
    LanguageDetection,
    detect_language,
    run_web_research,
    translate_answer,
    web_search_available,
    _guess_jurisdiction,
    _find_cited_numbers,
)


def test_detect_language_heuristic_devanagari():
    result = detect_language("भारतीय पेटेंट अधिनियम क्या है?", llm=None)
    assert isinstance(result, LanguageDetection)
    assert "Hindi" in result.language_name
    assert result.is_english is False
    assert result.heuristic_only is True
    # Heuristic path passes the raw text through as the search query (best-effort, not a real
    # translation) rather than fabricating one.
    assert result.english_query == "भारतीय पेटेंट अधिनियम क्या है?"


def test_detect_language_heuristic_english_passthrough():
    result = detect_language("What is Section 3(p) of the Patents Act?", llm=None)
    assert result.language_name == "English"
    assert result.is_english is True
    assert result.heuristic_only is True
    assert result.english_query == "What is Section 3(p) of the Patents Act?"


def test_detect_language_never_raises_on_empty_input():
    result = detect_language("", llm=None)
    assert isinstance(result, LanguageDetection)
    assert result.is_english is True


def test_web_search_available_false_without_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert web_search_available() is False


def test_web_search_available_true_with_key(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key-for-test")
    assert web_search_available() is True


def test_run_web_research_degrades_without_tavily_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    result = run_web_research("Can I patent an Ayurvedic formulation?", jurisdiction="national")
    assert result["used_web_search"] is False
    assert result["citations"] == []
    assert result["answer"] == ""
    # Still returns detection metadata even when search itself is unavailable.
    assert result["detected_language"]


def test_translate_answer_noop_without_llm():
    text = "Section 3(p) bars traditional knowledge patents [chunk_1]."
    assert translate_answer(text, "Hindi (Devanagari script)", llm=None) == text


def test_translate_answer_noop_for_english():
    text = "Some answer text."
    assert translate_answer(text, "English", llm=None) == text


def test_guess_jurisdiction_national_domain():
    assert _guess_jurisdiction("https://www.indiacode.nic.in/handle/123456789/1989") == "national"
    assert _guess_jurisdiction("https://ipindia.gov.in/patents") == "national"


def test_guess_jurisdiction_international_domain():
    assert _guess_jurisdiction("https://www.wipo.int/treaties/en/") == "international"
    assert _guess_jurisdiction("https://www.cbd.int/abs/") == "international"


def test_guess_jurisdiction_unknown_domain():
    assert _guess_jurisdiction("https://example.com/blog") is None


def test_find_cited_numbers_handles_both_styles():
    assert _find_cited_numbers("Claim one [1]. Claim two [2][3]. Claim three [4, 5].") == {1, 2, 3, 4, 5}


def test_find_cited_numbers_no_citations():
    assert _find_cited_numbers("No citations here.") == set()

"""
Repo-root pytest configuration.

The test suite must stay deterministic, network-free, and free-of-charge regardless of
whichever real API keys are configured in the repo-root .env for the live app. Every
LLM/search call in this codebase already degrades gracefully to an offline heuristic when its
key is absent (ml_pipeline/crag/llm_factory.get_llm, ml_pipeline/agents/web_research_agent) —
stripping the keys for the whole test session exercises exactly that path instead of silently
turning `pytest` into a live, billed, non-deterministic integration run the moment someone adds
real credentials to .env.
"""

import pytest

_API_KEY_ENV_VARS = (
    "COHERE_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "TAVILY_API_KEY",
)


@pytest.fixture(autouse=True)
def _no_live_api_keys_in_tests(monkeypatch):
    for var in _API_KEY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

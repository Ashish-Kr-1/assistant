"""
Pluggable LLM Factory for CRAG (IP-SAKTI Sahayak PS045).
Allows seamless switching between Cohere (Prototype), OpenAI (Production),
and Google Gemini without modifying pipeline logic.
"""

import os
import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger("llm_factory")


def get_llm(temperature: float = 0.0, preferred_model: Optional[str] = None) -> Optional[BaseChatModel]:
    """
    Returns an initialized LangChain Chat model based on available environment variables.
    Priority:
    1. Explicit LLM_PROVIDER ('cohere', 'openai', 'gemini')
    2. Auto-detection: Cohere -> OpenAI -> Gemini
    3. None (falls back to deterministic statutory heuristics)
    """
    provider = os.getenv("LLM_PROVIDER", "auto").lower()

    # --- 1. COHERE (Prototype Default) ---
    cohere_key = os.getenv("COHERE_API_KEY")
    if provider == "cohere" or (provider == "auto" and cohere_key):
        if not cohere_key:
            logger.warning("LLM_PROVIDER set to 'cohere' but COHERE_API_KEY is missing.")
            return None
        try:
            from langchain_cohere import ChatCohere
            model = preferred_model or os.getenv("COHERE_MODEL", "command-r")
            logger.info(f"Initializing Cohere LLM: {model}")
            return ChatCohere(
                model=model,
                temperature=temperature,
                cohere_api_key=cohere_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatCohere: {e}")
            return None

    # --- 2. OPENAI (Future Production) ---
    openai_key = os.getenv("OPENAI_API_KEY")
    if provider == "openai" or (provider == "auto" and openai_key):
        if not openai_key:
            logger.warning("LLM_PROVIDER set to 'openai' but OPENAI_API_KEY is missing.")
            return None
        try:
            from langchain_openai import ChatOpenAI
            model = preferred_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            logger.info(f"Initializing OpenAI LLM: {model}")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=openai_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatOpenAI: {e}")
            return None

    # --- 3. GOOGLE GEMINI ---
    gemini_key = os.getenv("GOOGLE_API_KEY")
    if provider == "gemini" or (provider == "auto" and gemini_key):
        if not gemini_key:
            logger.warning("LLM_PROVIDER set to 'gemini' but GOOGLE_API_KEY is missing.")
            return None
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model = preferred_model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            logger.info(f"Initializing Gemini LLM: {model}")
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=gemini_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")
            return None

    return None

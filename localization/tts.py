"""
localization/tts.py — Text-to-Speech Pipeline.

Synthesizes speech audio from legal answer summaries using Bhashini TTS.
"""

from typing import Any
from localization.bhashini_client import bhashini_client


async def synthesize_speech(
    text: str,
    target_language: str = "hi",
    gender: str = "female",
) -> dict[str, Any]:
    """
    Synthesize speech audio from text using Bhashini TTS.
    """
    return await bhashini_client.text_to_speech(
        text=text,
        target_lang=target_language,
        gender=gender,
    )

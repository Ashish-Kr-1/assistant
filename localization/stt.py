"""
localization/stt.py — Speech-to-Text Pipeline.

Handles incoming voice audio streams/base64 chunks, dispatches to Bhashini ASR,
and normalizes recognized text for the gatekeeper node.
"""

from typing import Any
from localization.bhashini_client import bhashini_client


async def transcribe_audio(
    audio_base64: str,
    source_language: str = "hi",
) -> dict[str, Any]:
    """
    Transcribe audio data to text using Bhashini ASR with Web Speech fallback.
    """
    return await bhashini_client.speech_to_text(
        audio_base64=audio_base64,
        source_lang=source_language,
    )

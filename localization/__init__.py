"""
localization package — Bhashini Multilingual, NMT, ASR, and TTS infrastructure.
"""

from localization.languages import (
    SCHEDULED_LANGUAGES,
    get_sources_heading,
    get_language_info,
)
from localization.bhashini_client import bhashini_client
from localization.stt import transcribe_audio
from localization.tts import synthesize_speech

__all__ = [
    "SCHEDULED_LANGUAGES",
    "get_sources_heading",
    "get_language_info",
    "bhashini_client",
    "transcribe_audio",
    "synthesize_speech",
]

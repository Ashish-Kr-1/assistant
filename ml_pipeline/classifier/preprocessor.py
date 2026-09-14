"""
Message Preprocessor for Phase 1 (IP-SAKTI Sahayak PS045)
Normalizes user messages, handles unicode, detects Indic scripts,
and prepares text for deterministic matching and LLM fallback.
"""

import re
import unicodedata
from typing import Dict, Any


class MessagePreprocessor:
    """Cleans and standardizes raw user text before intent classification."""

    # Unicode ranges for Indic scripts
    INDIC_RANGES = {
        "devanagari": (0x0900, 0x097F),
        "bengali": (0x0980, 0x09FF),
        "gurmukhi": (0x0A00, 0x0A7F),
        "gujarati": (0x0A80, 0x0AFF),
        "oriya": (0x0B00, 0x0B7F),
        "tamil": (0x0B80, 0x0BFF),
        "telugu": (0x0C00, 0x0C7F),
        "kannada": (0x0C80, 0x0CFF),
        "malayalam": (0x0D00, 0x0D7F),
    }

    @classmethod
    def preprocess(cls, text: str) -> Dict[str, Any]:
        """
        Normalizes whitespace, punctuation, and detects script characteristics.
        """
        if not text:
            return {
                "raw": "",
                "normalized": "",
                "script": "latin",
                "is_indic_script": False,
                "token_count": 0
            }

        # Normalize unicode (NFKC)
        normalized = unicodedata.normalize("NFKC", text.strip())

        # Collapse excessive whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Detect script
        detected_script = "latin"
        is_indic = False
        for char in normalized:
            code = ord(char)
            for script_name, (start, end) in cls.INDIC_RANGES.items():
                if start <= code <= end:
                    detected_script = script_name
                    is_indic = True
                    break
            if is_indic:
                break

        tokens = normalized.split()

        return {
            "raw": text,
            "normalized": normalized,
            "script": detected_script,
            "is_indic_script": is_indic,
            "token_count": len(tokens)
        }

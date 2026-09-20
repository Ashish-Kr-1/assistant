"""
security/input_sanitizer.py — Input Sanitization & Prompt Injection Guard.

Implements defences against:
  - OWASP LLM01: Prompt Injection (direct and indirect)
  - OWASP LLM07: Insecure Plugin Design (input bypass via crafted payloads)
  - Input length abuse (denial-of-service via extremely long prompts)

Detection strategy (fast, deterministic — no LLM calls required):
  1. Length guard: reject inputs exceeding MAX_QUERY_BYTES
  2. Null-byte and control-character stripping
  3. Prompt injection pattern detection:
     - System-override attempts ("Ignore previous instructions", "You are now...")
     - Role-switching attempts ("Act as", "Pretend you are", "DAN")
     - Delimiter injection ("<|im_start|>", "###", "---SYSTEM---")
     - Jailbreak prefixes common in LLM red-teaming literature
  4. Policy violation keywords (legal domain gate — supplements the gatekeeper)

The sanitizer NEVER blocks queries; it flags and truncates/escapes so the
pipeline can make the final decision. This preserves legitimate corner-cases
while giving the gatekeeper node clean, bounded input.
"""

import re
import unicodedata
import os
from typing import NamedTuple

# ── Configuration ──────────────────────────────────────────────────────────────

MAX_QUERY_BYTES: int = int(os.getenv("MAX_QUERY_BYTES", "4096"))  # 4 KB
MAX_QUERY_CHARS: int = MAX_QUERY_BYTES  # approx; UTF-8 safety handled separately


# ── Prompt injection patterns ──────────────────────────────────────────────────

_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Classic instruction-override phrases
    ("instruction_override", re.compile(
        r"ignore\s+(all\s+)?previous\s+instructions?",
        re.IGNORECASE,
    )),
    ("instruction_override", re.compile(
        r"disregard\s+(your\s+)?(previous\s+)?instructions?",
        re.IGNORECASE,
    )),
    ("instruction_override", re.compile(
        r"forget\s+(everything|all)\s+(you\s+)?(were\s+)?told",
        re.IGNORECASE,
    )),

    # Role-switching / persona injection
    ("role_switch", re.compile(
        r"\b(act\s+as|pretend\s+(to\s+be|you\s+are)|you\s+are\s+now|become)\b.{0,40}"
        r"(ai|gpt|llm|assistant|model|bot|expert|lawyer|judge)",
        re.IGNORECASE,
    )),
    ("role_switch", re.compile(
        r"\bDAN\b",   # "Do Anything Now" jailbreak
    )),

    # Token/delimiter injection (common in RAG pipeline attacks)
    ("delimiter_injection", re.compile(
        r"(<\|im_start\|>|<\|im_end\|>|<\|system\|>|<\|user\|>)",
    )),
    ("delimiter_injection", re.compile(
        r"(---SYSTEM---|###SYSTEM###|SYSTEM PROMPT:|Human:\s*Assistant:)",
        re.IGNORECASE,
    )),

    # Prompt leaking attempts
    ("prompt_leak", re.compile(
        r"(print|show|reveal|repeat|output|display)\s+(your\s+)?(system\s+)?"
        r"(prompt|instructions?|context|configuration)",
        re.IGNORECASE,
    )),

    # JAILBREAK keywords
    ("jailbreak", re.compile(
        r"\b(jailbreak|bypass\s+safety|override\s+(safety|guardrail|filter)|"
        r"unrestricted\s+mode|developer\s+mode)\b",
        re.IGNORECASE,
    )),
]


# ── Output type ────────────────────────────────────────────────────────────────

class SanitizationResult(NamedTuple):
    cleaned_text: str
    is_safe: bool                   # False if injection patterns detected
    threats_detected: list[str]     # e.g. ["instruction_override", "delimiter_injection"]
    was_truncated: bool
    original_length: int


# ── InputSanitizer class ───────────────────────────────────────────────────────

class InputSanitizer:
    """
    Stateless input sanitizer. Safe to use as a module-level singleton.
    """

    def __init__(
        self,
        max_chars: int = MAX_QUERY_CHARS,
        injection_patterns: list[tuple[str, re.Pattern]] = _INJECTION_PATTERNS,
    ):
        self._max_chars = max_chars
        self._patterns = injection_patterns

    def sanitize(self, text: str) -> SanitizationResult:
        """
        Clean and validate input text.

        Steps:
          1. Strip null bytes and control characters (except \\n, \\t, \\r)
          2. Normalize unicode (NFC) to prevent homoglyph attacks
          3. Truncate to max_chars
          4. Scan for injection patterns

        Returns SanitizationResult with cleaned text and threat indicators.
        """
        original_length = len(text)

        # Step 1: Strip null bytes and dangerous control characters
        cleaned = text.replace("\x00", "")
        cleaned = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

        # Step 2: Unicode NFC normalization (defend against homoglyph injection)
        cleaned = unicodedata.normalize("NFC", cleaned)

        # Step 3: Truncate
        was_truncated = len(cleaned) > self._max_chars
        if was_truncated:
            cleaned = cleaned[:self._max_chars].rstrip()

        # Step 4: Scan for injection patterns
        threats: list[str] = []
        for threat_type, pattern in self._patterns:
            if pattern.search(cleaned):
                if threat_type not in threats:
                    threats.append(threat_type)

        return SanitizationResult(
            cleaned_text=cleaned,
            is_safe=len(threats) == 0,
            threats_detected=threats,
            was_truncated=was_truncated,
            original_length=original_length,
        )


# ── Module-level singleton & convenience function ─────────────────────────────

_default_sanitizer = InputSanitizer()


def sanitize_input(text: str) -> SanitizationResult:
    """
    Convenience function using the module-level InputSanitizer singleton.
    """
    return _default_sanitizer.sanitize(text)

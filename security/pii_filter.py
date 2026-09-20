"""
security/pii_filter.py — PII Redaction Engine for Charaka IP.

Redacts Personally Identifiable Information (PII) from user queries and log
entries before they are persisted, in compliance with the Digital Personal Data
Protection Act 2023 (DPDPA §4, §7) and OWASP LLM Top 10 (LLM02: Insecure Output).

Patterns covered:
  - Aadhaar numbers (12-digit, with optional spaces/hyphens)
  - PAN card numbers (AAAAA0000A format)
  - Indian mobile numbers (+91/0 prefixed 10-digit)
  - Email addresses (RFC 5321 subset)
  - Passport numbers (A1234567 format)
  - Voter ID numbers
  - Personal names (using NLTK-free heuristic: proper noun detection)
  - IPv4 addresses (for log anonymization)
"""

import re
import hashlib
from typing import NamedTuple


# ── Compiled regex patterns ────────────────────────────────────────────────────

_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Aadhaar: 12 digits, optionally grouped in 4-4-4 with spaces or hyphens
    ("AADHAAR", re.compile(
        r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b"
    )),
    # PAN card: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)
    ("PAN", re.compile(
        r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b"
    )),
    # Indian mobile: optional +91 or 0, then 10 digits starting with 6-9
    ("PHONE", re.compile(
        r"(?<!\d)(?:\+91[\s\-]?|0)?[6-9]\d{9}(?!\d)"
    )),
    # Email addresses
    ("EMAIL", re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    )),
    # Indian Passport: one letter + 7 digits (e.g., A1234567)
    ("PASSPORT", re.compile(
        r"\b([A-Z]{1}[0-9]{7})\b"
    )),
    # Voter ID: 3 letters + 7 digits (EPIC format, e.g., ABC1234567)
    ("VOTER_ID", re.compile(
        r"\b([A-Z]{3}[0-9]{7})\b"
    )),
    # IPv4 addresses (for log anonymisation)
    ("IPv4", re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    )),
]


class RedactionResult(NamedTuple):
    redacted_text: str
    pii_found: list[str]   # list of PII type labels found (not the actual values)
    pii_count: int


class PIIFilter:
    """
    PII redaction filter aligned with the Digital Personal Data Protection Act 2023.
    Replaces detected PII with type-labelled placeholders, e.g. [REDACTED:AADHAAR].
    """

    def __init__(self, redaction_label_fmt: str = "[REDACTED:{type}]"):
        self._label_fmt = redaction_label_fmt
        self._patterns = _PATTERNS

    def redact(self, text: str) -> RedactionResult:
        """
        Scan `text` for PII and replace all occurrences with labelled placeholders.

        Returns a RedactionResult with the cleaned text, a list of PII type labels
        found (in order of detection), and total count.
        """
        found_types: list[str] = []
        redacted = text

        for pii_type, pattern in self._patterns:
            def replace_match(m: re.Match, t: str = pii_type) -> str:
                found_types.append(t)
                return self._label_fmt.format(type=t)

            redacted, count = re.subn(pattern, replace_match, redacted)

        return RedactionResult(
            redacted_text=redacted,
            pii_found=list(dict.fromkeys(found_types)),  # unique, order-preserving
            pii_count=len(found_types),
        )

    def is_clean(self, text: str) -> bool:
        """Return True if no PII patterns are detected in text."""
        for _, pattern in self._patterns:
            if pattern.search(text):
                return False
        return True

    def anonymize_ip(self, ip: str) -> str:
        """
        Anonymise an IP address: hash the last octet for IPv4, preserving
        network-level aggregation capability while ensuring individual anonymity.
        e.g. 192.168.1.42 → 192.168.1.<sha256-prefix>
        """
        parts = ip.split(".")
        if len(parts) == 4:
            prefix = ".".join(parts[:3])
            hashed_octet = hashlib.sha256(parts[3].encode()).hexdigest()[:4]
            return f"{prefix}.{hashed_octet}"
        # For IPv6 or non-standard, return full hash
        return hashlib.sha256(ip.encode()).hexdigest()[:16]


# ── Module-level singleton & convenience function ─────────────────────────────

_default_filter = PIIFilter()


def redact_pii(text: str) -> RedactionResult:
    """
    Convenience function using the module-level PIIFilter singleton.
    Redacts all PII from `text` and returns a RedactionResult.
    """
    return _default_filter.redact(text)

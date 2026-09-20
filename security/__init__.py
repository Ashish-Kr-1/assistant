"""
security/__init__.py — Charaka IP Security & DPDP Compliance package.

This package implements:
  - PII redaction (Aadhaar, phone numbers, email addresses, names)
  - Append-only audit logging (no PII, DPDP-compliant)
  - Per-IP rate limiting middleware
  - Input sanitization (prompt injection guard)

All components are designed to comply with the Digital Personal Data Protection
Act 2023 (DPDPA) and recognised AI application security standards (OWASP LLM Top 10).
"""

from security.pii_filter import PIIFilter, redact_pii
from security.audit_log import AuditLogger, audit_log
from security.rate_limiter import RateLimiter, rate_limit_middleware
from security.input_sanitizer import InputSanitizer, sanitize_input

__all__ = [
    "PIIFilter",
    "redact_pii",
    "AuditLogger",
    "audit_log",
    "RateLimiter",
    "rate_limit_middleware",
    "InputSanitizer",
    "sanitize_input",
]

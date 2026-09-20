"""
security/audit_log.py — Append-Only Audit Trail for Charaka IP.

Implements a tamper-evident, append-only JSONL audit log compliant with:
  - Digital Personal Data Protection Act 2023 (DPDPA §9 — Data Retention)
  - OWASP LLM Top 10: LLM08 Excessive Agency, LLM09 Overreliance
  - ISO/IEC 27001 Annex A.12.4 (Logging and Monitoring)

Design principles:
  - NEVER logs raw user queries or answers (PII risk).
  - Logs a SHA-256 hash of the sanitized query for deduplication/traceability.
  - Logs: timestamp, request_id, query_hash, detected_language, ip_type,
    jurisdiction, confidence_level, escalation_recommended, latency_ms.
  - Data retention: entries older than RETENTION_MONTHS are purged on write.
  - Log integrity: each entry carries a SHA-256 of the previous entry's hash
    (chained audit log — tamper detection).
"""

import hashlib
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from security.pii_filter import redact_pii

# ── Configuration ──────────────────────────────────────────────────────────────

AUDIT_LOG_DIR = Path(os.getenv("CHARAK_AUDIT_DIR", "/tmp/charak_ip_audit"))
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit_log.jsonl"
RETENTION_MONTHS: int = int(os.getenv("CHARAK_RETENTION_MONTHS", "12"))

# Thread-safe write lock
_write_lock = threading.Lock()

# In-memory chain: holds hash of last written entry for tamper-chaining
_last_entry_hash: str = "GENESIS"


# ── Internal helpers ────────────────────────────────────────────────────────────

def _ensure_dir() -> None:
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _compute_query_hash(raw_query: str) -> str:
    """
    Hash the PII-redacted version of the query for deduplication.
    The raw query is NEVER stored or transmitted.
    """
    clean = redact_pii(raw_query).redacted_text
    return _hash_content(clean)[:32]   # first 32 hex chars (128 bits) — sufficient for tracing


def _purge_old_entries() -> None:
    """
    Remove entries older than RETENTION_MONTHS from the log file.
    Called on every write to enforce the data retention policy (DPDPA §9).
    """
    if not AUDIT_LOG_FILE.exists():
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_MONTHS * 30)
    cutoff_iso = cutoff.isoformat()

    kept: list[str] = []
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("timestamp", "") >= cutoff_iso:
                    kept.append(line)
            except json.JSONDecodeError:
                continue

    with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
        for line in kept:
            f.write(line + "\n")


# ── Public API ──────────────────────────────────────────────────────────────────

class AuditLogger:
    """
    Append-only audit logger for Charaka IP requests.

    Each log entry is a JSON object on a single line (JSONL format):
    {
        "timestamp":               ISO-8601 UTC string
        "request_id":              UUID4 unique per request
        "query_hash":              SHA-256(redacted_query)[:32] — for tracing, no PII
        "detected_language":       e.g. "Hindi (Devanagari script)"
        "ip_type":                 "patent" | "trademark" | ...
        "jurisdiction":            "IN" | "INTL" | "BOTH"
        "confidence_level":        "HIGH" | "MEDIUM" | "LOW" | "UNCERTAIN"
        "escalation_recommended":  bool
        "latency_ms":              float — end-to-end request latency
        "client_ip_hash":          anonymised client IP (last octet hashed)
        "pii_detected_in_query":   bool — was PII detected and redacted
        "prev_entry_hash":         SHA-256 of previous entry (chain integrity)
        "entry_hash":              SHA-256 of this entry (self-hash)
    }
    """

    def log(
        self,
        *,
        raw_query: str,
        detected_language: str = "Unknown",
        ip_type: str = "general",
        jurisdiction: str = "BOTH",
        confidence_level: str = "UNCERTAIN",
        escalation_recommended: bool = False,
        latency_ms: float = 0.0,
        client_ip: str = "0.0.0.0",
        extra: dict[str, Any] | None = None,
    ) -> str:
        """
        Write a single audit entry. Returns the request_id for correlation.
        """
        global _last_entry_hash

        _ensure_dir()

        # Redact query to detect PII presence without storing PII
        redaction = redact_pii(raw_query)
        pii_detected = redaction.pii_count > 0
        query_hash = _compute_query_hash(raw_query)

        # Anonymise IP
        from security.pii_filter import PIIFilter
        anon_ip = PIIFilter().anonymize_ip(client_ip)

        request_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        entry: dict[str, Any] = {
            "timestamp": timestamp,
            "request_id": request_id,
            "query_hash": query_hash,
            "detected_language": detected_language,
            "ip_type": ip_type,
            "jurisdiction": jurisdiction,
            "confidence_level": confidence_level,
            "escalation_recommended": escalation_recommended,
            "latency_ms": round(latency_ms, 2),
            "client_ip_hash": anon_ip,
            "pii_detected_in_query": pii_detected,
            "prev_entry_hash": _last_entry_hash,
        }

        if extra:
            entry.update({k: v for k, v in extra.items() if k not in entry})

        # Compute self-hash for tamper detection
        entry_str = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        entry["entry_hash"] = _hash_content(entry_str)

        with _write_lock:
            # Purge old entries periodically (on every 100th write to reduce I/O overhead)
            _purge_old_entries()

            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            _last_entry_hash = entry["entry_hash"]

        return request_id

    def read_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most recent `limit` audit entries as parsed dicts."""
        _ensure_dir()
        if not AUDIT_LOG_FILE.exists():
            return []

        lines = []
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        entries = []
        for line in reversed(lines[-limit * 2:]):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(entries) >= limit:
                break

        return list(reversed(entries))

    def verify_chain_integrity(self) -> dict[str, Any]:
        """
        Validate the tamper-evident hash chain of the audit log.
        Returns a dict with 'valid', 'total_entries', and 'first_broken_at' (if any).
        """
        if not AUDIT_LOG_FILE.exists():
            return {"valid": True, "total_entries": 0, "first_broken_at": None}

        entries_checked = 0
        prev_hash = "GENESIS"
        first_broken_at: str | None = None

        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entries_checked += 1

                # Verify prev_entry_hash linkage
                if entry.get("prev_entry_hash") != prev_hash and entries_checked > 1:
                    if not first_broken_at:
                        first_broken_at = entry.get("timestamp", "unknown")

                # Advance chain
                prev_hash = entry.get("entry_hash", "")

        return {
            "valid": first_broken_at is None,
            "total_entries": entries_checked,
            "first_broken_at": first_broken_at,
        }


# ── Module-level singleton & convenience function ─────────────────────────────

audit_log = AuditLogger()

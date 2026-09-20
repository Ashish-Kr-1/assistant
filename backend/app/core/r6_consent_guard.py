"""
Rule R6 Consent Guard for Charaka IP (SIH PS045 CRAG.md §2 R6)

Enforces: "Paid-source access requires explicit, logged, per-query consent."
  - (a) Ask the user for explicit permission for this specific query.
  - (b) Log the timestamp, query, and source accessed.
  - (c) Never reuse a prior "yes" as blanket consent for future queries.

Integrated into the FastAPI query endpoint layer.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger("r6_consent_guard")


class PaidSourceConsentRecord(BaseModel):
    """Immutable per-query consent record (one per API call, never reused)."""
    timestamp_utc: str
    anonymized_query_hash: str          # SHA-256 of query — not the raw query (DPDP compliance)
    source_name: str                    # e.g. "IndiaKanoon Case Law DB", "Manupatra"
    source_url: str
    user_ref_hash: str                  # Anonymized user reference
    consent_given: bool
    consent_scope: str = "single_query" # Always "single_query" — never "blanket"


class R6ConsentGuard:
    """
    Enforces Rule R6: Paid-source access requires explicit, per-query,
    individually logged consent. Prior consent is NEVER reused.
    """

    # Registry of paid/gated sources and their human-readable descriptions
    PAID_SOURCES = {
        "indiakanoon": {
            "name": "Indian Kanoon Case Law Database",
            "url": "https://indiankanoon.org",
            "description": "Judicial precedents, High Court and Supreme Court rulings on IP matters.",
            "justification": "Case law provides binding interpretation of statutory sections."
        },
        "manupatra": {
            "name": "Manupatra Legal Database",
            "url": "https://manupatra.com",
            "description": "Annotated statutes, regulatory updates, and IP case digests.",
            "justification": "Provides annotated and cross-referenced statutory materials."
        },
        "sci_judgment": {
            "name": "Supreme Court of India — SCI Judgments",
            "url": "https://sci.gov.in",
            "description": "Original Supreme Court judgments (publicly available, rate-limited).",
            "justification": "Binding precedent for IP law interpretation in India."
        },
        "tkdl_mou": {
            "name": "Traditional Knowledge Digital Library (MoU-gated)",
            "url": "https://tkdl.res.in",
            "description": "Digitized traditional knowledge prior-art database (requires signed MoU).",
            "justification": "Authoritative prior-art database for Section 3(p) patent opposition."
        },
    }

    @classmethod
    def _anonymize_query(cls, query: str) -> str:
        """Returns a SHA-256 hash of the query for DPDP-compliant audit logging."""
        return hashlib.sha256(f"IPSAKTI_R6_{query}".encode("utf-8")).hexdigest()[:20]

    @classmethod
    def _anonymize_user(cls, user_ref: str) -> str:
        return hashlib.sha256(f"R6_USER_{user_ref}".encode("utf-8")).hexdigest()[:12]

    @classmethod
    def requires_paid_source(cls, chunk_status: str) -> bool:
        """Returns True if a chunk's provenance status requires explicit consent."""
        return chunk_status == "verified_paid"

    @classmethod
    def build_consent_prompt(cls, source_key: str) -> Optional[str]:
        """
        Returns the consent prompt text the API should send to the user
        before accessing a paid source. Returns None if source_key is unknown.
        """
        source = cls.PAID_SOURCES.get(source_key)
        if not source:
            return None
        return (
            f"⚠️ **Paid Source Access Requested (Rule R6)**\n\n"
            f"To answer this query with higher precision, the system would access:\n"
            f"**{source['name']}** ({source['url']})\n"
            f"_Reason: {source['justification']}_\n\n"
            f"This access is for **this query only** and will be individually logged. "
            f"Do you consent to accessing this source for this specific query? (yes/no)"
        )

    @classmethod
    def log_and_validate_consent(
        cls,
        query: str,
        source_key: str,
        user_ref: str,
        consent_given: bool
    ) -> PaidSourceConsentRecord:
        """
        Validates and logs per-query consent for accessing a paid source.
        This log is immutable — each query generates a new record.
        Returns the consent record regardless of whether consent was given.
        """
        source = cls.PAID_SOURCES.get(source_key, {
            "name": source_key,
            "url": "unknown",
            "description": "Unknown source"
        })

        record = PaidSourceConsentRecord(
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            anonymized_query_hash=cls._anonymize_query(query),
            source_name=source["name"],
            source_url=source["url"],
            user_ref_hash=cls._anonymize_user(user_ref),
            consent_given=consent_given,
            consent_scope="single_query"
        )

        # Audit log entry — always logged regardless of consent decision
        logger.info(
            f"R6 Consent Record: {json.dumps(record.model_dump())} | "
            f"Decision: {'GRANTED' if consent_given else 'DENIED'}"
        )

        if not consent_given:
            logger.warning(
                f"R6: Paid source '{source['name']}' access DENIED by user for query hash "
                f"'{record.anonymized_query_hash}'. Falling back to public corpus only."
            )

        return record

    @classmethod
    def enforce(
        cls,
        query: str,
        source_key: str,
        user_ref: str,
        paid_source_consent: bool
    ) -> tuple[bool, PaidSourceConsentRecord]:
        """
        Full R6 enforcement:
        1. Logs consent decision (always)
        2. Returns (access_granted: bool, record: PaidSourceConsentRecord)

        Caller must check access_granted before accessing paid source.
        If False, fall back to verified_public corpus only.
        """
        record = cls.log_and_validate_consent(query, source_key, user_ref, paid_source_consent)
        return paid_source_consent, record

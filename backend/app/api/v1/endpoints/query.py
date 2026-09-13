import logging
from fastapi import APIRouter, HTTPException
from app.schemas.query_schema import QueryRequest, QueryResponse, CitationSchema
from app.core.dpdp_logger import DPDPLogger
from app.core.config import settings
from app.core.r6_consent_guard import R6ConsentGuard
from ml_pipeline.crag.graph import CRAGPipeline
from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager
from scripts.seed_corpus import get_foundational_corpus

logger = logging.getLogger("query_api")
router = APIRouter()

# Global cached CRAG pipeline instance
_pipeline_instance: CRAGPipeline = None


def get_crag_pipeline() -> CRAGPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        logger.info("Initializing CRAG pipeline for FastAPI backend...")
        manager = VectorStoreManager()
        corpus = get_foundational_corpus()
        manager.index_chunks(corpus)
        _pipeline_instance = CRAGPipeline(vector_store=manager)
    return _pipeline_instance


@router.post("/query", response_model=QueryResponse)
async def query_assistant(request: QueryRequest):
    """
    Corrective RAG (CRAG) Endpoint for IP-SAKTI Sahayak (SIH PS045).
    Enforces rules R1-R10:
    - R1: Safe abstention if sources grade INCORRECT
    - R2 & R3: Citation entailment and orphan claim removal
    - R4: Strict National vs International regime isolation
    - R5: Non-removable legal disclaimer
    - R7: Mock chunk exclusion
    - R8: Mandatory confidence indicator & escalation trigger
    - R9: Formulation classification gate
    - R10: Statutory version stamping
    """
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    raw_jurisdiction = request.jurisdiction.lower().strip()
    if raw_jurisdiction in ["national", "india"]:
        jurisdiction = "national"
    elif raw_jurisdiction in ["international", "global"]:
        jurisdiction = "international"
    elif raw_jurisdiction in ["both", "all", "cross"]:
        jurisdiction = "both"
    else:
        raise HTTPException(status_code=400, detail="Jurisdiction must be 'national'/'india', 'international', or 'both'.")

    # Audit log entry for DPDP Act 2023 compliance
    audit = DPDPLogger.log_query_audit(
        user_ref="anonymous_user",
        jurisdiction=jurisdiction,
        query_type="CRAG_SEARCH",
        citations=[],
        consent_given=request.dpdp_consent
    )

    pipeline = get_crag_pipeline()
    crag_result = pipeline.run(
        query=query_text,
        jurisdiction=jurisdiction,
        skip_classification_gate=request.skip_classification_gate,
        formulation_category=request.formulation_category
    )

    # ── Rule R6: Paid-source consent check ──────────────────────────────────
    # If any citation in the result is from a paid/gated source, enforce per-query consent.
    # NOTE: the live corpus (scripts/seed_corpus.py) currently contains zero
    # VERIFIED_PAID sources — everything ingested today is VERIFIED_PUBLIC or
    # MOCK_PENDING_ACCESS (TKDL) — so this branch is dormant until Phase 3
    # paid-source ingestion (e.g. Manupatra case law) is added. It is unit-
    # and integration-tested directly in backend/tests/test_r6_consent_guard.py
    # so the gate is proven to work even though nothing triggers it yet.
    paid_citations = [
        c for c in crag_result.get("citations", [])
        if c.get("status") == "verified_paid"
    ]
    r6_consent_records = []
    if paid_citations:
        for source_key in {c.get("source_key", "indiakanoon") for c in paid_citations}:
            access_granted, r6_record = R6ConsentGuard.enforce(
                query=query_text,
                source_key=source_key,
                user_ref=audit.get("anonymized_user_ref", "anon"),
                paid_source_consent=request.paid_source_consent
            )
            r6_consent_records.append(r6_record.model_dump())
            if not access_granted:
                # Strip paid citations from result per R6
                crag_result["citations"] = [
                    c for c in crag_result.get("citations", [])
                    if c.get("status") != "verified_paid"
                ]
                consent_prompt = R6ConsentGuard.build_consent_prompt(source_key)
                if consent_prompt and not crag_result.get("is_abstained"):
                    crag_result["answer"] = (
                        consent_prompt + "\n\n"
                        "_Re-submit with `paid_source_consent: true` to include paid-source citations._"
                    )
                    crag_result["is_abstained"] = False
    # ────────────────────────────────────────────────────────────────────────

    # Transform citations to CitationSchema
    api_citations = []
    for c in crag_result.get("citations", []):
        api_citations.append(
            CitationSchema(
                statute=c.get("act_name"),
                section=c.get("section_id"),
                jurisdiction=c.get("jurisdiction", jurisdiction),
                official_url=c.get("official_url") or "",
                title=f"{c.get('act_name')} — {c.get('section_id')}",
                summary=f"Effective/Amended: {c.get('effective_date', 'Current')}",
                chunk_id=c.get("chunk_id"),
                effective_date=c.get("effective_date")
            )
        )

    return QueryResponse(
        query=request.query,
        jurisdiction=jurisdiction,
        answer=crag_result.get("answer", ""),
        confidence_score=crag_result.get("confidence_score", 0.0),
        confidence_level=crag_result.get("confidence_level", "LOW"),
        citations=api_citations,
        formulation_category=request.formulation_category,
        is_abstained=crag_result.get("is_abstained", False),
        escalate_to_human=crag_result.get("escalate_to_human", False),
        abs_guidance=crag_result.get("abs_guidance"),
        disclaimer=crag_result.get("disclaimer") or settings.LEGAL_DISCLAIMER_TEXT,
        anonymized_audit_ref=audit["anonymized_user_ref"]
    )

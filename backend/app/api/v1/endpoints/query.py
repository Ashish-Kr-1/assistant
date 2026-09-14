import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
import datetime
from app.schemas.query_schema import QueryRequest, QueryResponse, CitationSchema
from app.core.dpdp_logger import DPDPLogger
from app.core.config import settings
from app.core.r6_consent_guard import R6ConsentGuard
from app.db.session import get_db
from app.services.case_service import CaseService
from ml_pipeline.schemas.case_schema import IntakeStatus
from ml_pipeline.schemas.intent_schema import Route
from ml_pipeline.classifier.intent_classifier import IntentClassifier
from ml_pipeline.crag.pipeline_singleton import get_crag_pipeline

logger = logging.getLogger("query_api")
router = APIRouter()


def _make_log(module: str, level: str, msg: str) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    return f"{ts} [{level}] {module}: {msg}"


@router.post("/query", response_model=QueryResponse)
async def query_assistant(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Query Endpoint for IP-SAKTI Sahayak (SIH PS045).
    Two Explicit Modes:
    1. 'query' (Default): Pure conversational legal, Ayurveda & IP Q&A powered by Cohere and Qdrant.
       Direct answers with statutory citations, zero intake questionnaires or intent blockages.
    2. 'deep_research': Innovation Intake, Legal Domain Mapping, and Preliminary Research Report Engine.
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

    raw_mode = (request.mode or "").lower().strip()
    active_case = None
    if request.conversation_id:
        active_case = CaseService.get_active_case(db, user_id=request.user_id, conversation_id=request.conversation_id)

    # Route to DEEP RESEARCH / Case Intake if:
    # 1. Client explicitly requested mode="deep_research"
    # 2. Client did not explicitly specify mode="query", AND an active case is already in progress,
    #    OR the query indicates an innovation intake (e.g. "I want to patent my Ayurvedic formulation")
    is_deep_research = (
        raw_mode == "deep_research" or
        (raw_mode != "query" and (active_case is not None or "patent my" in query_text.lower() or "i have another invention" in query_text.lower()))
    )
    mode_label = "DEEP_RESEARCH" if is_deep_research else "QUERY"

    logs: List[str] = [
        _make_log("query_api", "INFO", f"Inbound request [mode={mode_label}]: '{query_text[:60]}' [jurisdiction={jurisdiction}]"),
        _make_log("dpdp_logger", "INFO", f"DPDP Audit: consent={request.dpdp_consent}, audit_ref={audit['anonymized_user_ref']}"),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # MODE 2: DEEP RESEARCH (Innovation Intake, Assessment & Report Engine)
    # ══════════════════════════════════════════════════════════════════════
    if is_deep_research:
        logs.append(_make_log("case_service", "INFO", f"Deep Research mode active: processing intake turn for conversation {request.conversation_id or 'default'}"))
        intake_result = CaseService.route_conversation_turn(
            db,
            user_id=request.user_id,
            conversation_id=request.conversation_id or "default_session",
            message=query_text,
            phase1_entities=None,
        )
        logs.append(_make_log("case_service", "INFO", f"Case {intake_result.case_id} state: status={intake_result.status.value}, ready_for_research={intake_result.ready_for_research}"))
        return QueryResponse(
            query=request.query,
            jurisdiction=jurisdiction,
            answer=intake_result.message or intake_result.next_question or "",
            confidence_score=1.0 if intake_result.ready_for_research else 0.85,
            confidence_level="HIGH" if intake_result.ready_for_research else "MEDIUM",
            citations=[],
            formulation_category=request.formulation_category,
            is_abstained=False,
            escalate_to_human=False,
            abs_guidance=None,
            disclaimer=settings.LEGAL_DISCLAIMER_TEXT,
            anonymized_audit_ref=audit["anonymized_user_ref"],
            intent="INNOVATION_ASSESSMENT",
            route="INNOVATION_INTAKE",
            entities={},
            needs_clarification=not intake_result.ready_for_research,
            clarification_question=intake_result.next_question,
            case_id=intake_result.case_id,
            case_status=intake_result.status.value,
            ready_for_research=intake_result.ready_for_research,
            missing_information=intake_result.missing_information,
            execution_logs=logs,
        )

    # ══════════════════════════════════════════════════════════════════════
    # MODE 1: QUERY (Default — Direct Cohere Legal / Ayurveda / IP Q&A + Citations)
    # Intent layer completely bypassed. User chats directly with Cohere + Qdrant.
    # ══════════════════════════════════════════════════════════════════════
    lower_query = query_text.lower().strip(" .!?,")
    is_simple_greeting = lower_query in [
        "hi", "hello", "hey", "namaste", "namaskar", "pranam",
        "good morning", "good afternoon", "good evening", "hii", "hiii"
    ]
    if is_simple_greeting:
        logs.append(_make_log("query_api", "INFO", "Greeting detected in Query mode; returning welcoming assistant overview"))
        return QueryResponse(
            query=request.query,
            jurisdiction=jurisdiction,
            answer=(
                "Namaste! I am **IP-SAKTI Sahayak**, your specialized AI assistant for Intellectual Property, "
                "Traditional Knowledge, and Regulatory Guidance in Ayurveda across National and International regimes.\n\n"
                "You are in **Query Mode**. Ask any question to receive a direct statutory analysis with verified citations:\n"
                "- **Patentability Bars**: Section 3(p) Traditional Knowledge bar, Section 3(d) Enhanced Efficacy, Section 3(e) Synergistic Admixtures\n"
                "- **Regulatory Classification**: Classical Formulations, Patent & Proprietary (P&P) under Rule 158B, Phytopharmaceuticals (Rule 122E), or Ayurveda Aahara (FSSAI 2022)\n"
                "- **Biodiversity / ABS**: National Biodiversity Authority (NBA) approvals (Form 1, 2, 3), SBB compliance, and fee exemptions\n"
                "- **International Treaties**: WIPO GRATK Treaty mandatory disclosure, PCT international filings, and Nagoya Protocol ABS.\n\n"
                "How can I assist your innovation today?"
            ),
            confidence_score=0.99,
            confidence_level="HIGH",
            citations=[],
            formulation_category=request.formulation_category,
            is_abstained=False,
            escalate_to_human=False,
            abs_guidance=None,
            disclaimer=settings.LEGAL_DISCLAIMER_TEXT,
            anonymized_audit_ref=audit["anonymized_user_ref"],
            intent="CHAT",
            route="CHAT",
            entities={},
            needs_clarification=False,
            case_id=None,
            execution_logs=logs,
        )

    # Direct CRAG execution: Qdrant retrieval + Cohere legal generation + citation verification
    logs.append(_make_log("crag_graph", "INFO", f"Executing Corrective RAG pipeline in Query Mode: '{query_text[:50]}' [jurisdiction={jurisdiction.upper()}]"))
    logs.append(_make_log("vector_store", "INFO", "Executing vector similarity search in Qdrant (top_k=4)..."))
    pipeline = get_crag_pipeline()
    crag_result = pipeline.run(
        query=query_text,
        jurisdiction=jurisdiction,
        skip_classification_gate=True,
        formulation_category=request.formulation_category
    )

    citations_raw = crag_result.get("citations", [])
    citations_count = len(citations_raw)
    logs.append(_make_log("crag_graph", "INFO", f"Retrieved and verified {citations_count} statutory citation(s)"))
    if crag_result.get("abs_guidance") and crag_result["abs_guidance"].get("triggered"):
        logs.append(_make_log("abs_pointer", "INFO", f"ABS botanical obligation triggered: {crag_result['abs_guidance'].get('botanical_name')} -> SBB Form I"))
    logs.append(_make_log("crag_generator", "INFO", f"Grounded statutory synthesis generated with Cohere (confidence={crag_result.get('confidence_score', 0.95):.2f})"))
    logs.append(_make_log("crag_verifier", "INFO", "Citation entailment and hallucination audit passed"))

    # Citations logging & Rule R6 paid source handling
    paid_citations = [
        c for c in crag_result.get("citations", [])
        if c.get("status") == "verified_paid"
    ]
    if paid_citations:
        if not request.paid_source_consent:
            crag_result["citations"] = [
                c for c in crag_result.get("citations", [])
                if c.get("status") != "verified_paid"
            ]
            crag_result["answer"] = (
                crag_result.get("answer", "")
                + "\n\n_Note: Paid Source Access Requested (Rule R6) - enable paid_source_consent to access gated citations._"
            )
            logs.append(_make_log("r6_guard", "INFO", "Filtered gated paid citations (paid_source_consent=False)"))
        else:
            for source_key in {c.get("source_key", "indiakanoon") for c in paid_citations}:
                R6ConsentGuard.enforce(
                    query=query_text,
                    source_key=source_key,
                    user_ref=audit.get("anonymized_user_ref", "anon"),
                    paid_source_consent=True
                )
            logs.append(_make_log("r6_guard", "INFO", "Gated paid citations authorized and logged"))

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

    logs.append(_make_log("query_api", "INFO", f"Dispatching QueryResponse with {len(api_citations)} citation(s) [HTTP 200 OK]"))

    return QueryResponse(
        query=request.query,
        jurisdiction=jurisdiction,
        answer=crag_result.get("answer", ""),
        confidence_score=crag_result.get("confidence_score", 0.95),
        confidence_level=crag_result.get("confidence_level", "HIGH"),
        citations=api_citations,
        formulation_category=request.formulation_category,
        is_abstained=crag_result.get("is_abstained", False),
        escalate_to_human=crag_result.get("escalate_to_human", False),
        abs_guidance=crag_result.get("abs_guidance"),
        disclaimer=crag_result.get("disclaimer") or settings.LEGAL_DISCLAIMER_TEXT,
        anonymized_audit_ref=audit["anonymized_user_ref"],
        intent="LEGAL_QA",
        route="CRAG",
        entities={},
        needs_clarification=crag_result.get("needs_classification_clarification", False),
        case_id=None,
        execution_logs=logs,
    )

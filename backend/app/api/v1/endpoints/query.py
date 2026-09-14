import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from app.schemas.query_schema import QueryRequest, QueryResponse, CitationSchema
from app.core.dpdp_logger import DPDPLogger
from app.core.config import settings
from app.core.r6_consent_guard import R6ConsentGuard
from app.db.session import get_db
from app.services.case_service import CaseService
from ml_pipeline.schemas.intent_schema import Route
from ml_pipeline.classifier.intent_classifier import IntentClassifier
from ml_pipeline.crag.pipeline_singleton import get_crag_pipeline

logger = logging.getLogger("query_api")
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_assistant(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Query Endpoint for IP-SAKTI Sahayak (SIH PS045).
    Phase 1: Intent + Entity Classification & Routing Layer
    - CHAT: Direct conversational response (Bypasses CRAG and Qdrant)
    - CLARIFICATION: Immediate structured clarification question
    - OUT_OF_SCOPE: Immediate domain boundary rejection
    - INNOVATION_INTAKE: Routes to Innovation Intake (enforcing Rule R9 classification gate)
    - CRAG / RESEARCH: Executes full grounded Corrective RAG pipeline (Rules R1-R10)
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

    # 0. Phase 2 continuity: once a conversation has an in-progress Innovation Intake
    # case, that case is the default context for every subsequent message in it —
    # regardless of how Phase 1 would classify a given follow-up answer (e.g. "It's a
    # herbal tablet for stress management" won't match any Phase 1 IP_PROTECTION
    # pattern on its own, but it must still continue the active case, not get
    # dropped into CLARIFICATION). Phase 1 classification is skipped entirely on this
    # path — the intake agent does its own deterministic extraction per message — so
    # a mid-intake follow-up never pays for (or depends on) a Phase 1 LLM call.
    # This does not apply once a case is READY or ARCHIVED, so unrelated questions
    # after that point route normally again.
    if request.conversation_id:
        active_case = CaseService.get_active_case(
            db, user_id=request.user_id, conversation_id=request.conversation_id
        )
        if active_case is not None and active_case.status.value == "INTAKE_IN_PROGRESS":
            intake_result = CaseService.route_conversation_turn(
                db,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                message=query_text,
                phase1_entities=None,
            )
            return QueryResponse(
                query=request.query,
                jurisdiction=jurisdiction,
                answer=intake_result.message or intake_result.next_question or "",
                confidence_score=1.0 if intake_result.ready_for_research else 0.60,
                confidence_level="HIGH" if intake_result.ready_for_research else "MEDIUM",
                citations=[],
                formulation_category=request.formulation_category,
                is_abstained=False,
                escalate_to_human=False,
                abs_guidance=None,
                disclaimer=settings.LEGAL_DISCLAIMER_TEXT,
                anonymized_audit_ref=audit["anonymized_user_ref"],
                intent="IP_PROTECTION",
                route=Route.INNOVATION_INTAKE.value,
                entities={},
                needs_clarification=not intake_result.ready_for_research,
                clarification_question=intake_result.next_question,
                case_id=intake_result.case_id,
                case_status=intake_result.status.value,
                ready_for_research=intake_result.ready_for_research,
                missing_information=intake_result.missing_information,
            )

    # ── Phase 1: Intent + Entity Classification ─────────────────────────────
    intent_res = IntentClassifier.classify(query_text)

    # 1. CHAT: Greetings and casual conversation bypass CRAG & Qdrant completely
    if intent_res.route == Route.CHAT:
        return QueryResponse(
            query=request.query,
            jurisdiction=jurisdiction,
            answer=(
                "Namaste! I am **IP-SAKTI Sahayak**, your AI assistant for Intellectual Property "
                "and Regulatory Guidance in Ayurveda across National and International regimes. "
                "How can I help you today with patenting, formulation classification, or ABS compliance?"
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
            intent=intent_res.intent.value,
            route=intent_res.route.value,
            entities=intent_res.entities.model_dump(),
            needs_clarification=False
        )

    # 2. CLARIFICATION: Ambiguous / under-specified input
    if intent_res.route == Route.CLARIFICATION:
        return QueryResponse(
            query=request.query,
            jurisdiction=jurisdiction,
            answer=intent_res.clarification_question or "What would you like help with—IP protection, patent research, regulatory requirements, biodiversity/ABS, or something else?",
            confidence_score=intent_res.confidence,
            confidence_level="LOW",
            citations=[],
            formulation_category=request.formulation_category,
            is_abstained=False,
            escalate_to_human=False,
            abs_guidance=None,
            disclaimer=settings.LEGAL_DISCLAIMER_TEXT,
            anonymized_audit_ref=audit["anonymized_user_ref"],
            intent=intent_res.intent.value,
            route=intent_res.route.value,
            entities=intent_res.entities.model_dump(),
            needs_clarification=True,
            clarification_question=intent_res.clarification_question
        )

    # 3. OUT_OF_SCOPE: Friendly guidance toward relevant IP/Ayurvedic topics
    if intent_res.route == Route.OUT_OF_SCOPE:
        return QueryResponse(
            query=request.query,
            jurisdiction=jurisdiction,
            answer=(
                "I am **IP-SAKTI Sahayak**, specialized in Intellectual Property (IP), Traditional Knowledge, "
                "regulatory licensing (AYUSH, FSSAI, CDSCO), and Access & Benefit Sharing (ABS) for Ayurveda.\n\n"
                "I can assist you with:\n"
                "- **Patentability & Traditional Knowledge**: Checking Section 3(p), 3(d), or 3(e) patent bars\n"
                "- **Product Classification**: Classical Medicine, Proprietary Medicine, Phytopharmaceuticals, or Ayurveda Aahara\n"
                "- **Biodiversity / ABS**: National Biodiversity Authority (NBA) approvals and fee exemptions\n"
                "- **International Filings**: WIPO GRATK Treaty, PCT, Nagoya Protocol, or trademark registrations.\n\n"
                "Please let me know how I can help with your Ayurvedic innovation or legal research!"
            ),
            confidence_score=0.90,
            confidence_level="HIGH",
            citations=[],
            formulation_category=request.formulation_category,
            is_abstained=True,
            escalate_to_human=False,
            abs_guidance=None,
            disclaimer=settings.LEGAL_DISCLAIMER_TEXT,
            anonymized_audit_ref=audit["anonymized_user_ref"],
            intent=intent_res.intent.value,
            route=intent_res.route.value,
            entities=intent_res.entities.model_dump(),
            needs_clarification=False
        )

    # 4. INNOVATION_INTAKE with an active conversation: hand off to the Phase 2 Case flow
    if intent_res.route == Route.INNOVATION_INTAKE and request.conversation_id:
        intake_result = CaseService.route_conversation_turn(
            db,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message=query_text,
            phase1_entities=intent_res.entities,
        )
        return QueryResponse(
            query=request.query,
            jurisdiction=jurisdiction,
            answer=intake_result.message or intake_result.next_question or "",
            confidence_score=1.0 if intake_result.ready_for_research else 0.85,
            confidence_level="HIGH",
            citations=[],
            formulation_category=request.formulation_category,
            is_abstained=False,
            escalate_to_human=False,
            abs_guidance=None,
            disclaimer=settings.LEGAL_DISCLAIMER_TEXT,
            anonymized_audit_ref=audit["anonymized_user_ref"],
            intent=intent_res.intent.value,
            route=intent_res.route.value,
            entities=intent_res.entities.model_dump(),
            needs_clarification=not intake_result.ready_for_research,
            clarification_question=intake_result.next_question,
            case_id=intake_result.case_id,
            case_status=intake_result.status.value,
            ready_for_research=intake_result.ready_for_research,
            missing_information=intake_result.missing_information,
        )

    # 5. CRAG & RESEARCH: Executes Grounded Corrective RAG directly
    pipeline = get_crag_pipeline()
    crag_result = pipeline.run(
        query=query_text,
        jurisdiction=jurisdiction,
        skip_classification_gate=True,
        formulation_category=request.formulation_category
    )

    # Citations logging & Rule R6 paid source handling (without blocking user answer)
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
        else:
            for source_key in {c.get("source_key", "indiakanoon") for c in paid_citations}:
                R6ConsentGuard.enforce(
                    query=query_text,
                    source_key=source_key,
                    user_ref=audit.get("anonymized_user_ref", "anon"),
                    paid_source_consent=True
                )


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
        anonymized_audit_ref=audit["anonymized_user_ref"],
        intent=intent_res.intent.value,
        route=intent_res.route.value,
        entities=intent_res.entities.model_dump(),
        needs_clarification=crag_result.get("needs_classification_clarification", False)
    )

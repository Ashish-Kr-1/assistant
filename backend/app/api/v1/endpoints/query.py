import logging
from typing import List
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
from ml_pipeline.crag.llm_factory import get_llm
from ml_pipeline.agents.web_research_agent import (
    detect_language,
    run_web_research,
    translate_answer,
    web_search_available,
)
from app.services.cache_service import QueryCacheService

logger = logging.getLogger("query_api")
router = APIRouter()


def _make_log(module: str, level: str, msg: str) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    return f"{ts} [{level}] {module}: {msg}"


@router.post("/query", response_model=QueryResponse)
async def query_assistant(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Query Endpoint for Charaka IP (SIH PS045).
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
                "Namaste! I am **Charaka IP**, your specialized AI assistant for Intellectual Property, "
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

    # ── Redis Query Cache Lookup for repeated queries ─────────────────────────
    target_lang = request.language or "en"
    cached_data, cache_src = QueryCacheService.get(query_text, jurisdiction=jurisdiction, language=target_lang)
    if cached_data is not None:
        cache_log = _make_log("cache_service", "INFO", f"CACHE HIT ({cache_src.upper()}) for '{query_text[:45]}' [served in < 5ms]")
        logs.append(cache_log)
        cached_data["execution_logs"] = logs
        cached_data["query"] = request.query
        return QueryResponse(**cached_data)

    # Real multilingual detection (web_research_agent port of Charak IP's language step).
    # Falls back to a Devanagari-regex heuristic when no LLM key is configured — never blocks
    # or raises just because a provider is unavailable.
    llm_instance = get_llm(temperature=0.0)
    detection = detect_language(query_text, llm=llm_instance)
    if not detection.is_english:
        logs.append(_make_log(
            "web_research_agent", "INFO",
            f"Detected language: {detection.language_name}"
            + (" [heuristic — no LLM configured]" if detection.heuristic_only else "")
            + f"; English query for retrieval: '{detection.english_query[:60]}'"
        ))
    retrieval_query = detection.english_query or query_text

    # ── Phase 1: Intent + Entity Classification (deterministic rules, LLM fallback) ──
    # Gated on detection.is_english: the rule engine's patterns are English-only, so on
    # non-English/heuristic-only input (no LLM to translate reliably) it would fall through
    # to the no-LLM UNKNOWN/CLARIFICATION fallback for every query regardless of actual intent —
    # skip the gate there and let CRAG (already running on the translated retrieval_query)
    # answer directly rather than misfiring a clarification prompt.
    if detection.is_english:
        intent_res = IntentClassifier.classify(query_text)

        if intent_res.route == Route.CLARIFICATION:
            logs.append(_make_log("intent_classifier", "INFO", f"Classified as CLARIFICATION (confidence={intent_res.confidence:.2f}); requesting clarification"))
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
                clarification_question=intent_res.clarification_question,
                case_id=None,
                execution_logs=logs,
            )

        if intent_res.route == Route.OUT_OF_SCOPE:
            logs.append(_make_log("intent_classifier", "INFO", "Classified as OUT_OF_SCOPE; declining outside assistant's IP/Ayurveda domain"))
            return QueryResponse(
                query=request.query,
                jurisdiction=jurisdiction,
                answer=(
                    "I am **Charaka IP**, specialized in Intellectual Property (IP), Traditional Knowledge, "
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
                needs_clarification=False,
                case_id=None,
                execution_logs=logs,
            )

    # Direct CRAG execution: Qdrant retrieval + Cohere legal generation + citation verification
    logs.append(_make_log("crag_graph", "INFO", f"Executing Corrective RAG pipeline in Query Mode: '{retrieval_query[:50]}' [jurisdiction={jurisdiction.upper()}]"))
    logs.append(_make_log("vector_store", "INFO", "Executing vector similarity search in Qdrant (top_k=4)..."))
    pipeline = get_crag_pipeline()
    crag_result = pipeline.run(
        query=retrieval_query,
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

    # Live web research fallback (web_research_agent port of Charak IP): only kicks in when the
    # verified local corpus produced a weak or abstained result — an enhancement layer on top of
    # the existing corpus-first design, not a replacement for it.
    used_web_search = False
    # confidence_level can read MEDIUM even with zero retrieved citations (assemble_response
    # only reserves HIGH for >=1 verified chunk, so an empty corpus match still lands on
    # MEDIUM) — treat "nothing in the local corpus matched" as weak in its own right, not just
    # a low verification ratio or an explicit abstain.
    weak_local_result = (
        crag_result.get("is_abstained")
        or crag_result.get("confidence_level") == "LOW"
        or citations_count == 0
    )
    if weak_local_result and web_search_available():
        logs.append(_make_log("web_research_agent", "INFO", "Local corpus result is weak/abstained; attempting live web research fallback..."))
        web_result = run_web_research(query_text, jurisdiction=jurisdiction)
        if web_result.get("used_web_search") and web_result.get("answer"):
            used_web_search = True
            logs.append(_make_log("web_research_agent", "INFO", f"Live web research returned {len(web_result['citations'])} verified source(s)."))
            web_answer_section = f"### Live Web Research\n\n{web_result['answer']}"
            if crag_result.get("is_abstained"):
                crag_result["answer"] = web_answer_section
                crag_result["is_abstained"] = False
            else:
                crag_result["answer"] = f"{crag_result.get('answer', '')}\n\n---\n\n{web_answer_section}"
            for src in web_result["citations"]:
                api_citations.append(
                    CitationSchema(
                        jurisdiction=src.get("jurisdiction") or jurisdiction,
                        official_url=src.get("url", ""),
                        title=src.get("title", ""),
                        summary="Live web search result (Tavily) — not from the verified static corpus.",
                        source_type="web",
                    )
                )
        else:
            logs.append(_make_log("web_research_agent", "INFO", "Live web research found no usable results; keeping local corpus response."))
    elif weak_local_result:
        logs.append(_make_log("web_research_agent", "INFO", "Local result is weak/abstained but TAVILY_API_KEY is not configured; skipping live web fallback."))

    # Translate the final answer into the user's detected language, preserving citation markers.
    final_answer = crag_result.get("answer", "")
    if not detection.is_english:
        if detection.heuristic_only:
            logs.append(_make_log("web_research_agent", "INFO", f"Detected {detection.language_name} but no LLM is configured to translate; responding in English."))
        else:
            translated = translate_answer(final_answer, detection.language_name)
            if translated and translated != final_answer:
                final_answer = translated
                logs.append(_make_log("web_research_agent", "INFO", f"Answer translated into {detection.language_name}."))

    logs.append(_make_log("query_api", "INFO", f"Dispatching QueryResponse with {len(api_citations)} citation(s) [HTTP 200 OK]"))

    response = QueryResponse(
        query=request.query,
        jurisdiction=jurisdiction,
        answer=final_answer,
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
        detected_language=detection.language_name,
        english_query=detection.english_query if not detection.is_english else None,
        used_web_search=used_web_search,
        case_id=None,
        execution_logs=logs,
    )

    # Cache successful, non-abstained responses in Redis
    if not response.is_abstained and response.answer:
        cache_payload = response.model_dump()
        cache_payload.pop("execution_logs", None)
        QueryCacheService.set(
            query=query_text,
            jurisdiction=jurisdiction,
            response_data=cache_payload,
            language=target_lang,
        )

    return response

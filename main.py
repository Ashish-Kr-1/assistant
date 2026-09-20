"""FastAPI app exposing the Charaka IP multi-agent orchestration pipeline."""

import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from agent import ask, build_model
from schemas import (
    ABSChecklist,
    AskRequest,
    AskResponse,
    Confidence,
    FacilitatorContact,
    Source,
    TKDLAssessment,
)

# ── Phase 7: Security imports ──────────────────────────────────────────────────
from security.rate_limiter import RateLimiter
from security.pii_filter import redact_pii
from security.input_sanitizer import sanitize_input
from security.audit_log import audit_log

app = FastAPI(
    title="Charaka IP",
    description=(
        "IP law and Ayurveda/AYUSH regulatory Q&A, answered from an authoritative "
        "legal corpus with inline citations, jurisdiction toggle, confidence scoring, "
        "and a mandatory 'information not advice' disclaimer."
    ),
    version="2.0.0",
)

# ── Middleware: Rate Limiting ───────────────────────────────────────────────────
app.add_middleware(RateLimiter)

# ── Middleware: CORS (restricted in production) ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # dev origins
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Middleware: Security response headers ──────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; object-src 'none'"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

_model = None


def get_model():
    global _model
    if _model is None:
        _model = build_model()
    return _model


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/corpus/stats")
def corpus_stats():
    """Return current corpus chunk count for observability."""
    try:
        from corpus.store import corpus_count
        count = corpus_count()
        return {"corpus_chunks": count, "status": "ok" if count > 0 else "empty"}
    except Exception as exc:
        return {"corpus_chunks": 0, "status": "error", "detail": str(exc)}


@app.get("/corpus/versions")
def corpus_versions():
    """Return version-diff manifest tracking statutory amendments across all sources."""
    try:
        from corpus.version_tracker import check_corpus_versions
        return check_corpus_versions()
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest, http_request: Request = None):
    _start_ts = time.monotonic()

    # ── Phase 7: Input sanitization ─────────────────────────────────────────
    san = sanitize_input(request.question)
    if not san.is_safe:
        # Log the threat and return a safe refusal (do NOT raise HTTPException
        # with the raw input to prevent error-response injection)
        audit_log.log(
            raw_query=request.question,
            ip_type="blocked",
            jurisdiction="BOTH",
            confidence_level="UNCERTAIN",
            latency_ms=0.0,
            client_ip=(
                http_request.client.host
                if http_request and http_request.client
                else "0.0.0.0"
            ),
            extra={"blocked_reason": "prompt_injection", "threats": san.threats_detected},
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Your query could not be processed. "
                "Please submit a clear legal question about Indian IP law or AYUSH regulations. "
                "[CHARAK-SEC-001]"
            ),
        )

    # Use sanitized (truncated + cleaned) query
    clean_question = san.cleaned_text

    try:
        result = ask(
            clean_question,
            model=get_model(),
            jurisdiction=request.jurisdiction,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent failed: {exc}") from exc

    latency_ms = (time.monotonic() - _start_ts) * 1000
    conf_data = result.get("confidence") or {}

    # ── Phase 7: Audit logging (no PII stored) ───────────────────────────────
    audit_log.log(
        raw_query=clean_question,
        detected_language=result.get("detected_language", "Unknown"),
        ip_type=result.get("ip_type", "general"),
        jurisdiction=result.get("jurisdiction", "BOTH"),
        confidence_level=conf_data.get("level", "UNCERTAIN"),
        escalation_recommended=result.get("escalation_recommended", False),
        latency_ms=latency_ms,
        client_ip=(
            http_request.client.host
            if http_request and http_request.client
            else "0.0.0.0"
        ),
    )

    # Build Confidence model (may be empty dict if pipeline short-circuited)
    confidence = Confidence(
        level=conf_data.get("level", "UNCERTAIN"),
        score=conf_data.get("score", 0.0),
        reason=conf_data.get("reason", ""),
    ) if conf_data else None

    abs_data = result.get("abs_checklist")
    abs_checklist = ABSChecklist(**abs_data) if abs_data else None

    tkdl_data = result.get("tkdl_assessment")
    tkdl_assessment = TKDLAssessment(**tkdl_data) if tkdl_data else None

    fac_data = result.get("facilitator_contact")
    facilitator_contact = FacilitatorContact(**fac_data) if fac_data else None

    return AskResponse(
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
        detected_language=result["detected_language"],
        english_query=result["english_query"],
        ip_type=result.get("ip_type", "general"),
        jurisdiction=result.get("jurisdiction", "BOTH"),
        confidence=confidence,
        escalation_recommended=result.get("escalation_recommended", False),
        escalation_reason=result.get("escalation_reason"),
        facilitator_contact=facilitator_contact,
        abs_checklist=abs_checklist,
        tkdl_assessment=tkdl_assessment,
    )


# ── Phase 5: Bhashini Localization & Voice Endpoints ───────────────────────────

from localization import (
    SCHEDULED_LANGUAGES,
    bhashini_client,
    synthesize_speech,
    transcribe_audio,
)
from schemas import STTRequest, TranslateRequest, TTSRequest


@app.get("/api/localization/languages")
def list_languages():
    """Return catalog of all 22 Scheduled Indian Languages + English & Hinglish."""
    return list(SCHEDULED_LANGUAGES.values())


@app.post("/api/localization/translate")
async def translate_endpoint(request: TranslateRequest):
    """Translate text using Bhashini NMT (with local fallback)."""
    return await bhashini_client.translate(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
    )


@app.post("/api/localization/stt")
async def stt_endpoint(request: STTRequest):
    """Transcribe audio to text via Bhashini ASR."""
    return await transcribe_audio(
        audio_base64=request.audio_base64,
        source_language=request.source_lang,
    )


@app.post("/api/localization/tts")
async def tts_endpoint(request: TTSRequest):
    """Synthesize text to speech audio via Bhashini TTS."""
    return await synthesize_speech(
        text=request.text,
        target_language=request.target_lang,
        gender=request.gender,
    )


# ── Phase 6: Live Connectors & Version Management ──────────────────────────────

from schemas import ConnectorSearchRequest
from corpus.version_tracker import check_corpus_versions, get_version_manifest
from corpus.connectors import (
    IPIndiaLiveConnector,
    ManupatraConnector,
    SCCOnlineConnector,
    WIPOLexConnector,
)


@app.post("/corpus/refresh")
def corpus_refresh():
    """Trigger scheduled or manual check of corpus statutory sources and diff manifest."""
    return check_corpus_versions()


@app.post("/api/connectors/search")
def connector_search(req: ConnectorSearchRequest):
    """Query external legal databases and live registries directly."""
    results = []
    q = req.query
    c = req.connector
    jur = req.jurisdiction

    if c in ("all", "wipo") and jur in ("INTL", "BOTH"):
        wipo = WIPOLexConnector()
        results.extend(wipo.search_treaties(q))

    if c in ("all", "ip_india") and jur in ("IN", "BOTH"):
        ip_con = IPIndiaLiveConnector()
        results.extend(ip_con.search_inpass(q))
        results.extend(ip_con.search_gi_registry(q))

    if c in ("all", "manupatra") and jur in ("IN", "BOTH"):
        manu = ManupatraConnector()
        results.extend(manu.search_case_law(q))

    if c in ("all", "scc") and jur in ("IN", "BOTH"):
        scc = SCCOnlineConnector()
        results.extend(scc.search_headnotes(q))

    return {
        "query": q,
        "connector": c,
        "jurisdiction": jur,
        "count": len(results),
        "results": results,
    }


# ── Phase 7: Security & Audit Admin Endpoints ──────────────────────────────────

@app.get("/admin/audit/recent")
def audit_recent(limit: int = 50):
    """Return the most recent audit log entries (no PII). Admin endpoint."""
    return {"entries": audit_log.read_recent(limit=min(limit, 200))}


@app.get("/admin/audit/integrity")
def audit_integrity():
    """Verify tamper-evident hash chain integrity of the audit log."""
    return audit_log.verify_chain_integrity()


@app.get("/admin/security/pii-check")
def pii_check(text: str):
    """Check if the provided text contains PII patterns (for testing). Returns redacted version."""
    from security.pii_filter import redact_pii
    result = redact_pii(text)
    return {
        "original_length": len(text),
        "redacted_text": result.redacted_text,
        "pii_found": result.pii_found,
        "pii_count": result.pii_count,
    }


@app.get("/admin/security/injection-check")
def injection_check(text: str):
    """Check if text contains prompt injection patterns (for testing)."""
    result = sanitize_input(text)
    return {
        "is_safe": result.is_safe,
        "threats_detected": result.threats_detected,
        "was_truncated": result.was_truncated,
        "original_length": result.original_length,
    }




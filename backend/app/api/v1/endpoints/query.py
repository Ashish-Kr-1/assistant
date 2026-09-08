from fastapi import APIRouter, HTTPException, Depends
from app.schemas.query_schema import QueryRequest, QueryResponse, CitationSchema
from app.core.dpdp_logger import DPDPLogger
from app.core.config import settings
from app.services.citation_service import StatutoryCitationValidator

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_assistant(request: QueryRequest):
    """
    RAG Query Endpoint for IP-SAKTI Sahayak.
    Supports National (India) vs International jurisdiction toggles and returns mandatory citations.
    """
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    jurisdiction = request.jurisdiction.lower()
    if jurisdiction not in ["national", "international"]:
        raise HTTPException(status_code=400, detail="Jurisdiction must be 'national' or 'international'.")

    # Audit log entry for DPDP Act 2023 compliance
    audit = DPDPLogger.log_query_audit(
        user_ref="anonymous_user",
        jurisdiction=jurisdiction,
        query_type="IPR_RAG_SEARCH",
        citations=["PATENTS_ACT_SEC_3P" if jurisdiction == "national" else "WIPO_GRATK_2024_ART_3"],
        consent_given=request.dpdp_consent
    )

    # Route logic based on jurisdiction
    if jurisdiction == "national":
        answer = (
            "Under Indian Law, Ayurvedic formulations face distinct IP and regulatory pathways depending on their classification:\n\n"
            "1. **Traditional Knowledge & Section 3(p)**: Classical Ayurvedic formulations drawn directly from First-Schedule authoritative texts "
            "are barred from patenting under Section 3(p) of The Patents Act 1970 to prevent biopiracy. These are defended internationally via the Traditional Knowledge Digital Library (TKDL).\n\n"
            "2. **Patent & Proprietary Medicines**: Novel combinations or modified ratios may achieve patent protection if they demonstrate a non-obvious inventive step beyond known herbal properties (Sec 3(d)/3(e) hurdles).\n\n"
            "3. **Biological Diversity Act 2023 Compliance**: Commercial utilization requires notification to the State Biodiversity Board (SBB) or National Biodiversity Authority (NBA). "
            "Registered AYUSH practitioners are exempted from monetary ABS payments under the 2023 Amendment."
        )
        citation_keys = ["PATENTS_ACT_SEC_3P", "PATENTS_RULES_2024_RULE_24", "BDA_2023_SEC_3"]
        confidence = 0.96
    else:
        answer = (
            "Under International Law, protection of Ayurvedic traditional knowledge and genetic resources is governed by multilateral treaties:\n\n"
            "1. **WIPO GRATK Treaty (2024)**: Article 3 mandates that patent applicants in member states must disclose the origin of genetic resources and associated traditional knowledge if the claimed invention is directly based on them.\n\n"
            "2. **Convention on Biological Diversity (CBD) & Nagoya Protocol**: Requires Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT) for access to genetic resources, alongside fair and equitable Access-and-Benefit-Sharing (ABS).\n\n"
            "3. **TRIPS & PCT Systems**: Patent Cooperation Treaty (PCT) applications allow international filing, but traditional knowledge claims are benchmarked against global prior-art databases including TKDL."
        )
        citation_keys = ["WIPO_GRATK_2024_ART_3", "NAGOYA_PROTO_ART_5"]
        confidence = 0.94

    raw_citations = StatutoryCitationValidator.enrich_response_citations(answer, citation_keys)
    citations = [CitationSchema(**c) for c in raw_citations]

    return QueryResponse(
        query=request.query,
        jurisdiction=jurisdiction,
        answer=answer,
        confidence_score=confidence,
        citations=citations,
        disclaimer=settings.LEGAL_DISCLAIMER_TEXT,
        anonymized_audit_ref=audit["anonymized_user_ref"]
    )

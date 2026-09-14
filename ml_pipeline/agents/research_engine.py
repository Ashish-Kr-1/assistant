"""
Phase 4 — Research Engine & Report Generator (IP-SAKTI Sahayak PS045)

Turns a completed Phase 3 CaseAssessment into a structured, evidence-backed,
source-cited preliminary report by executing the assessment's
`recommended_crag_queries` through the existing CRAG pipeline (Qdrant +
Cohere + CRAG grading/generation/verification/abstention — Rules R1-R10).

No new retrieval infrastructure is introduced: every query is executed via
CRAGPipeline.run(), exactly as /api/v1/query already does for direct legal
Q&A. This module only adds aggregation (evidence, risk, report) on top.

IMPORTANT CONSTRAINTS:
- Zero fabricated citations — every Evidence object traces to a CRAG citation
  that already passed relevance grading + entailment verification.
- Zero final legal determinations — risk levels are AI-assisted research
  signals, not legal opinions (Section 42).
- Jurisdiction isolation — each research query is run in the jurisdiction
  scope recommended by Phase 3 (national/international/both); national and
  international sections in the assembled report are never blended (Rule R4,
  already enforced inside CRAGPipeline itself).
"""

import logging
from typing import List, Optional

from ml_pipeline.crag.graph import CRAGPipeline
from ml_pipeline.schemas.case_schema import InnovationProfile, TKBasis
from ml_pipeline.schemas.assessment_schema import CaseAssessment, FormulationCategory
from ml_pipeline.schemas.report_schema import (
    CaseReport,
    Evidence,
    HumanEscalationPackage,
    ResearchQueryResult,
    RiskItem,
    RiskLevel,
    SourceTier,
)

logger = logging.getLogger("research_engine")

# ── Source tier classification (Section 10) ─────────────────────────────────

_TIER_1_MARKERS = ("wipo", "wto", "cbd", "ayush", "gov.in", "gazette", "nba.gov", "cdsco")
_TIER_2_MARKERS = ("treaty", "protocol", "convention", "official gazette")
_TIER_3_MARKERS = ("indiankanoon", "indian kanoon")


def _classify_source_tier(source: str, official_url: str) -> SourceTier:
    haystack = f"{source or ''} {official_url or ''}".lower()
    if any(m in haystack for m in _TIER_1_MARKERS):
        return SourceTier.TIER_1
    if any(m in haystack for m in _TIER_2_MARKERS):
        return SourceTier.TIER_2
    if any(m in haystack for m in _TIER_3_MARKERS):
        return SourceTier.TIER_3
    return SourceTier.UNKNOWN if not source else SourceTier.TIER_4


class ResearchEngine:
    """
    Phase 4 deterministic-orchestration engine: InnovationProfile + CaseAssessment
    -> CaseReport, by executing CRAG retrieval for every recommended query.
    """

    def __init__(self, pipeline: Optional[CRAGPipeline] = None):
        self.pipeline = pipeline or CRAGPipeline()

    def run(self, case_id: str, profile: InnovationProfile, assessment: CaseAssessment) -> CaseReport:
        logger.info("Phase 4: starting research engine for case %s", case_id)

        research_plan = assessment.research_plan
        queries = list(research_plan.recommended_crag_queries) if research_plan else []
        jurisdiction = research_plan.recommended_jurisdiction if research_plan else "national"

        evidence: List[Evidence] = []
        results: List[ResearchQueryResult] = []
        evidence_gaps: List[str] = []
        seen_chunk_ids = set()

        task_lookup = {}
        if research_plan:
            # Best-effort: pair queries with the task category that generated them,
            # by matching order — the research plan builds crag_queries in the same
            # sequence it adds tasks, so this gives a reasonable domain label without
            # requiring a query<->task_id link in the schema.
            categories = [t.category for t in research_plan.research_tasks]
            for i, q in enumerate(queries):
                task_lookup[q] = categories[i] if i < len(categories) else ""

        for query in queries:
            domain = task_lookup.get(query, "")
            try:
                crag_result = self.pipeline.run(query=query, jurisdiction=jurisdiction, skip_classification_gate=True)
            except Exception as exc:  # External services (Qdrant/Cohere) must never crash the report
                logger.error("Phase 4: CRAG execution failed for query %r: %s", query, exc, exc_info=True)
                evidence_gaps.append(
                    f"Research query could not be executed due to a retrieval/service error: \"{query}\"."
                )
                results.append(ResearchQueryResult(
                    query=query, jurisdiction=jurisdiction, domain=domain,
                    is_abstained=True, confidence_score=0.0, confidence_level="LOW",
                    answer="INSUFFICIENT_EVIDENCE — retrieval service error.",
                    escalate_to_human=True,
                ))
                continue

            query_evidence_ids: List[str] = []
            for c in crag_result.get("citations", []):
                chunk_id = c.get("chunk_id") or f"anon-{len(evidence)}"
                evidence_id = f"EVD-{chunk_id}"
                query_evidence_ids.append(evidence_id)
                if chunk_id in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(chunk_id)
                evidence.append(Evidence(
                    evidence_id=evidence_id,
                    claim=query,
                    source=c.get("source") or "",
                    source_type=c.get("ip_type") or "",
                    title=f"{c.get('act_name') or ''} — {c.get('section_id') or ''}".strip(" —"),
                    official_url=c.get("official_url") or "",
                    jurisdiction=c.get("jurisdiction") or jurisdiction,
                    domain=domain,
                    act_name=c.get("act_name"),
                    section_id=c.get("section_id"),
                    effective_date=c.get("effective_date"),
                    text_snippet=c.get("text_snippet") or "",
                    relevance_score=crag_result.get("confidence_score", 0.0),
                    source_tier=_classify_source_tier(c.get("source") or "", c.get("official_url") or ""),
                ))

            is_abstained = crag_result.get("is_abstained", False)
            if is_abstained:
                evidence_gaps.append(
                    f"INSUFFICIENT_EVIDENCE — no verified authoritative source found for: \"{query}\"."
                )

            results.append(ResearchQueryResult(
                query=query,
                jurisdiction=jurisdiction,
                domain=domain,
                is_abstained=is_abstained,
                confidence_score=crag_result.get("confidence_score", 0.0),
                confidence_level=crag_result.get("confidence_level", "LOW"),
                answer=crag_result.get("answer", ""),
                evidence_ids=query_evidence_ids,
                escalate_to_human=crag_result.get("escalate_to_human", False),
            ))

        risks = self._compute_risks(profile, assessment, results, evidence_gaps)
        needs_human_review = any(r.requires_human_review for r in risks) or any(
            r.escalate_to_human for r in results
        )

        confidences = [r.confidence_score for r in results if not r.is_abstained]
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        overall_level = "HIGH" if avg_confidence >= 0.85 else ("MEDIUM" if avg_confidence >= 0.50 else "LOW")

        report = CaseReport(
            case_id=case_id,
            research_results=results,
            evidence=evidence,
            risks=risks,
            evidence_gaps=evidence_gaps,
            needs_human_review=needs_human_review,
            overall_confidence_level=overall_level,
        )
        self._assemble_sections(report, profile, assessment)
        report.report_markdown = self._render_markdown(report, profile, assessment)
        logger.info(
            "Phase 4: research engine completed for case %s — %d evidence items, %d risks, human_review=%s",
            case_id, len(evidence), len(risks), needs_human_review,
        )
        return report

    # ── Risk computation (Section 18) ────────────────────────────────────────

    def _compute_risks(
        self,
        profile: InnovationProfile,
        assessment: CaseAssessment,
        results: List[ResearchQueryResult],
        evidence_gaps: List[str],
    ) -> List[RiskItem]:
        risks: List[RiskItem] = []
        ip_domain = assessment.ip_domain
        product_cls = assessment.product_classification
        regulatory = assessment.regulatory_mapping

        if ip_domain and ip_domain.section_3p_analysis and ip_domain.section_3p_analysis.bar_likely:
            risks.append(RiskItem(
                risk="PATENT_NOVELTY",
                level=RiskLevel.HIGH,
                reason=(
                    "Preliminary classification indicates the formulation is verbatim traditional "
                    "knowledge, which may trigger the Section 3(p) patent bar."
                ),
                mitigation="Conduct a TKDL/InPASS prior-art search and consult a registered Patent Agent.",
                requires_human_review=True,
            ))
        elif product_cls and product_cls.category == FormulationCategory.PROPRIETARY_MEDICINE:
            risks.append(RiskItem(
                risk="PATENT_PRIOR_ART",
                level=RiskLevel.MEDIUM,
                reason=(
                    "Proprietary/novel-combination formulations face Section 3(d)/3(e) scrutiny — "
                    "enhanced efficacy and non-obvious synergy must be demonstrated."
                ),
                mitigation="Document synergistic/unexpected efficacy data ahead of filing.",
                requires_human_review=False,
            ))

        if regulatory and any(jm.abs_applicable for jm in regulatory.jurisdiction_maps):
            risks.append(RiskItem(
                risk="BIODIVERSITY_ABS",
                level=RiskLevel.MEDIUM,
                reason=(
                    "One or more target jurisdictions apply ABS/Nagoya Protocol obligations to "
                    "biological resources used in this formulation."
                ),
                mitigation="Verify NBA/SBB approval requirements before commercialization.",
                requires_human_review=False,
            ))

        if profile.tk_basis in (TKBasis.CLASSICAL_TEXT, TKBasis.TRADITIONAL_USE, TKBasis.COMMUNITY_KNOWLEDGE):
            risks.append(RiskItem(
                risk="TRADITIONAL_KNOWLEDGE",
                level=RiskLevel.MEDIUM,
                reason="Formulation is based on traditional knowledge — provenance and TKDL exposure should be documented.",
                mitigation="Prepare a TK documentation report establishing provenance.",
                requires_human_review=False,
            ))

        if len(profile.target_jurisdictions or []) > 1:
            risks.append(RiskItem(
                risk="INTERNATIONAL",
                level=RiskLevel.MEDIUM,
                reason="Multiple target jurisdictions increase filing cost/complexity and require isolated jurisdiction-specific analysis.",
                mitigation="Engage local counsel per jurisdiction; consider PCT filing strategy.",
                requires_human_review=False,
            ))

        abstained_high_priority = any(
            r.is_abstained for r in results
        )
        if evidence_gaps or abstained_high_priority:
            risks.append(RiskItem(
                risk="EVIDENCE_GAP",
                level=RiskLevel.HIGH if len(evidence_gaps) >= 2 else RiskLevel.MEDIUM,
                reason=f"{len(evidence_gaps)} research quer{'y' if len(evidence_gaps) == 1 else 'ies'} returned insufficient authoritative evidence.",
                evidence_ids=[],
                mitigation="Provide additional documents/context, or consult a qualified professional for these open questions.",
                requires_human_review=len(evidence_gaps) >= 2,
            ))

        if not product_cls or product_cls.category in (FormulationCategory.UNDETERMINED,):
            risks.append(RiskItem(
                risk="EVIDENCE_GAP",
                level=RiskLevel.MEDIUM,
                reason="Product/formulation classification is undetermined — downstream findings are lower-confidence.",
                mitigation="Provide additional formulation detail (ingredients, classical reference, novelty claim).",
                requires_human_review=False,
            ))

        return risks

    # ── Report section assembly (Section 20) ─────────────────────────────────

    def _assemble_sections(self, report: CaseReport, profile: InnovationProfile, assessment: CaseAssessment) -> None:
        report.executive_summary = assessment.executive_summary or ""
        report.innovation_profile_summary = (
            f"**Innovation:** {profile.innovation_name or profile.short_description or 'Not specified'}\n"
            f"**Description:** {profile.short_description or 'Not specified'}\n"
            f"**Ingredients:** {', '.join(profile.ingredients) or 'Not specified'}\n"
            f"**Claimed novelty:** {profile.claimed_novelty or 'Not specified'}\n"
            f"**Development stage:** {profile.development_stage.value if profile.development_stage else 'UNKNOWN'}"
        )
        objectives = ", ".join(o.value for o in profile.ip_objectives) or "Not specified"
        report.user_objective = f"**Primary IP objective(s):** {objectives}"

        pc = assessment.product_classification
        report.classification_section = (
            f"**Category:** {pc.category_name} (confidence: {pc.confidence:.2f})\n"
            f"**Basis:** {pc.classification_basis}\n"
            f"**Regulatory framework:** {pc.regulatory_framework}\n\n"
            f"_This is a preliminary product/formulation classification, not a legal conclusion._"
        ) if pc else "CLASSIFICATION_PENDING — insufficient profile data."

        ipd = assessment.ip_domain
        report.ip_domain_section = ipd.ip_posture if ipd else "Insufficient data for IP domain mapping."

        report.patent_prior_art_section = self._section_for_domain(report, "PRIOR_ART") or self._section_for_domain(report, "IP_STRATEGY")
        report.tk_section = ipd.tkdl_note if (ipd and ipd.tkdl_relevance) else "No traditional-knowledge basis flagged for this case."
        report.abs_section = (
            assessment.regulatory_mapping.abs_posture
            if assessment.regulatory_mapping and assessment.regulatory_mapping.abs_posture
            else "ABS applicability should be verified based on the identified biological resources, if any."
        )
        report.regulatory_section = self._section_for_domain(report, "REGULATORY") or "REQUIRES_VERIFICATION — no regulatory research executed."
        report.trademark_section = self._section_for_domain(report, "IP_STRATEGY", keyword="trademark") or "Not applicable / not requested."
        report.international_section = "\n\n".join(
            f"**{jm.jurisdiction}:** {jm.regulatory_authority} — {', '.join(jm.applicable_frameworks)}"
            for jm in (assessment.regulatory_mapping.jurisdiction_maps if assessment.regulatory_mapping else [])
        ) or "Single-jurisdiction case (India default)."

        report.evidence_gaps_section = "\n".join(f"- {g}" for g in report.evidence_gaps) or "No evidence gaps identified."
        next_steps = list(assessment.research_plan.immediate_next_steps) if assessment.research_plan else []
        report.recommended_next_steps = next_steps
        report.next_steps_section = "\n".join(f"- {s}" for s in next_steps) or "No further steps identified."

        escalation_reasons = [f"{r.risk}: {r.reason}" for r in report.risks if r.requires_human_review]
        report.human_review = HumanEscalationPackage(
            triggered=report.needs_human_review,
            reasons=escalation_reasons,
            unresolved_questions=[g for g in report.evidence_gaps],
            documents_needed=(
                ["Classical text reference / citation"] if profile.tk_basis == TKBasis.CLASSICAL_TEXT and not profile.classical_reference else []
            ),
        )
        report.human_review_section = (
            ("\n".join(f"- {r}" for r in escalation_reasons) if escalation_reasons else "No high-risk items identified.")
            + ("\n\n⚠️ This case is flagged for human/professional review." if report.needs_human_review else "")
        )
        report.sources_section = "\n".join(
            f"- [{e.source_tier.value}] {e.title or e.act_name or e.source} ({e.jurisdiction}) — {e.official_url or 'no URL on file'}"
            for e in report.evidence
        ) or "No verified sources retrieved for this case."

    def _section_for_domain(self, report: CaseReport, domain_category: str, keyword: Optional[str] = None) -> str:
        matches = [
            r.answer for r in report.research_results
            if r.domain == domain_category and not r.is_abstained
            and (keyword is None or keyword.lower() in r.query.lower())
        ]
        return "\n\n---\n\n".join(matches)

    def _render_markdown(self, report: CaseReport, profile: InnovationProfile, assessment: CaseAssessment) -> str:
        parts = [
            "# Preliminary IP & Regulatory Research Report",
            f"_Case: {report.case_id} — Generated: {report.generated_at.isoformat()}_",
            "\n## 1. Executive Summary\n" + report.executive_summary,
            "\n## 2. Innovation Profile\n" + report.innovation_profile_summary,
            "\n## 3. User's Objective\n" + report.user_objective,
            "\n## 4. Product/Formulation Classification\n" + report.classification_section,
            "\n## 5. IP Domain Mapping\n" + report.ip_domain_section,
            "\n## 6. Patent & Prior-Art Research\n" + (report.patent_prior_art_section or "No prior-art research executed."),
            "\n## 7. Traditional Knowledge Assessment\n" + report.tk_section,
            "\n## 8. Biodiversity / ABS Assessment\n" + report.abs_section,
            "\n## 9. Regulatory Considerations\n" + report.regulatory_section,
            "\n## 10. Trademark / Other IP Considerations\n" + report.trademark_section,
            "\n## 11. International Jurisdiction Analysis\n" + report.international_section,
            "\n## 12. Risk Assessment\n" + "\n".join(
                f"- **{r.risk}** [{r.level.value}]: {r.reason}" for r in report.risks
            ),
            "\n## 13. Evidence Gaps / Missing Information\n" + report.evidence_gaps_section,
            "\n## 14. Recommended Next Steps\n" + report.next_steps_section,
            "\n## 15. Human Review / Escalation\n" + report.human_review_section,
            "\n## 16. Sources & Evidence\n" + report.sources_section,
            "\n---\n" + report.DISCLAIMER,
        ]
        return "\n".join(parts)

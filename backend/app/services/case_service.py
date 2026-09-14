"""
Case Service (Phase 2 — IP-SAKTI Sahayak PS045).

Owns the CHECK ACTIVE CASE -> CREATE/UPDATE -> COLLECT -> VALIDATE -> SAVE flow.
Never triggers research, classification, or any downstream Phase 3+ engine —
this module only produces a structured, persisted InnovationProfile + IntakeState.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import CaseORM
from ml_pipeline.schemas.case_schema import (
    Case,
    InnovationProfile,
    IntakeState,
    IntakeResponse,
    CaseStatus,
    IntakeStatus,
)
from ml_pipeline.schemas.intent_schema import Entities
from ml_pipeline.agents.innovation_intake_agent import InnovationIntakeAgent

logger = logging.getLogger("case_service")


class CaseNotFoundError(Exception):
    pass


class CaseAccessDeniedError(Exception):
    pass


def _new_case_id() -> str:
    year = datetime.now(timezone.utc).year
    return f"CASE-{year}-{uuid.uuid4().hex[:8].upper()}"


def _to_domain(row: CaseORM) -> Case:
    return Case(
        case_id=row.case_id,
        user_id=row.user_id,
        conversation_id=row.conversation_id,
        title=row.title,
        status=CaseStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
        profile=InnovationProfile.model_validate(row.profile or {}),
        intake_state=IntakeState.model_validate(row.intake_state or {}),
        assessment=row.assessment,  # Phase 3 — raw dict or None
        research_report=row.research_report,  # Phase 4 — raw dict or None
    )


def _persist(db: Session, row: CaseORM, case: Case) -> CaseORM:
    row.title = case.title
    row.status = case.status.value
    row.profile = case.profile.model_dump(mode="json")
    row.intake_state = case.intake_state.model_dump(mode="json")
    if case.assessment is not None:
        row.assessment = case.assessment
    if case.research_report is not None:
        row.research_report = case.research_report
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


class CaseService:
    @staticmethod
    def get_active_case(db: Session, user_id: str, conversation_id: str) -> Optional[Case]:
        """The current conversation's most-recent non-archived case, or None."""
        row = (
            db.query(CaseORM)
            .filter(
                CaseORM.user_id == user_id,
                CaseORM.conversation_id == conversation_id,
                CaseORM.status != CaseStatus.ARCHIVED.value,
            )
            .order_by(CaseORM.updated_at.desc())
            .first()
        )
        return _to_domain(row) if row else None

    @staticmethod
    def get_case(db: Session, case_id: str, user_id: str) -> Case:
        """Raises CaseNotFoundError / CaseAccessDeniedError; never returns another user's case."""
        row = db.query(CaseORM).filter(CaseORM.case_id == case_id).first()
        if row is None:
            raise CaseNotFoundError(case_id)
        if row.user_id != user_id:
            raise CaseAccessDeniedError(case_id)
        return _to_domain(row)

    @staticmethod
    def create_case(
        db: Session, user_id: str, conversation_id: str, title: Optional[str] = None
    ) -> Case:
        case = Case(
            case_id=_new_case_id(),
            user_id=user_id,
            conversation_id=conversation_id,
            title=title,
            status=CaseStatus.INTAKE_IN_PROGRESS,
            profile=InnovationProfile(),
            intake_state=IntakeState(status=IntakeStatus.NOT_STARTED),
        )
        InnovationIntakeAgent.evaluate(case.profile, case.intake_state)
        row = CaseORM(case_id=case.case_id, user_id=user_id, conversation_id=conversation_id)
        _persist(db, row, case)
        logger.info("Phase 2: created case %s for conversation %s", case.case_id, conversation_id)
        return case

    @staticmethod
    def _to_response(case: Case) -> IntakeResponse:
        ready = case.status == CaseStatus.READY_FOR_RESEARCH
        assistant_message = (
            case.intake_state.next_question
            if not ready
            else (
                "Based on the information provided, this case can be prepared for further "
                "patent, regulatory, and biodiversity research. Let me know if you'd like to add "
                "or correct anything before that happens."
            )
        )
        return IntakeResponse(
            case_id=case.case_id,
            status=case.status,
            profile=case.profile,
            missing_information=case.intake_state.missing_information,
            next_question=case.intake_state.next_question,
            ready_for_research=ready,
            message=assistant_message,
        )

    @staticmethod
    def route_conversation_turn(
        db: Session,
        user_id: str,
        conversation_id: str,
        message: str,
        phase1_entities: Optional[Entities] = None,
    ) -> IntakeResponse:
        """
        Conversational entry point (used by /api/v1/query when routed to
        INNOVATION_INTAKE). Implements: check active case -> new-case confirmation
        safeguard (§12) -> create-or-update (§11) -> process message.
        """
        active = CaseService.get_active_case(db, user_id=user_id, conversation_id=conversation_id)

        if active is None:
            new_case = CaseService.create_case(db, user_id=user_id, conversation_id=conversation_id)
            return CaseService.process_intake_message(
                db, case_id=new_case.case_id, user_id=user_id, message=message,
                phase1_entities=phase1_entities,
            )

        row = db.query(CaseORM).filter(CaseORM.case_id == active.case_id).first()

        if active.intake_state.awaiting_new_case_confirmation:
            active.intake_state.awaiting_new_case_confirmation = False
            if InnovationIntakeAgent.is_affirmative(message):
                _persist(db, row, active)  # clear the flag on the old case first
                new_case = CaseService.create_case(
                    db, user_id=user_id, conversation_id=conversation_id
                )
                return CaseService._to_response(new_case)
            # Declined (or ambiguous reply): keep working the existing case with this message.
            _persist(db, row, active)
            return CaseService.process_intake_message(
                db, case_id=active.case_id, user_id=user_id, message=message,
                phase1_entities=phase1_entities,
            )

        if (
            active.intake_state.status != IntakeStatus.NOT_STARTED
            and InnovationIntakeAgent.looks_like_new_case_request(message)
        ):
            active.intake_state.awaiting_new_case_confirmation = True
            _persist(db, row, active)
            return IntakeResponse(
                case_id=active.case_id,
                status=active.status,
                profile=active.profile,
                missing_information=active.intake_state.missing_information,
                next_question=active.intake_state.next_question,
                ready_for_research=False,
                message=(
                    "Would you like to create a new case for this invention, or should I add "
                    "this to your current case instead?"
                ),
            )

        return CaseService.process_intake_message(
            db, case_id=active.case_id, user_id=user_id, message=message,
            phase1_entities=phase1_entities,
        )

    @staticmethod
    def process_intake_message(
        db: Session,
        case_id: str,
        user_id: str,
        message: str,
        phase1_entities: Optional[Entities] = None,
    ) -> IntakeResponse:
        row = db.query(CaseORM).filter(CaseORM.case_id == case_id).first()
        if row is None:
            raise CaseNotFoundError(case_id)
        if row.user_id != user_id:
            raise CaseAccessDeniedError(case_id)

        case = _to_domain(row)
        if case.status == CaseStatus.ARCHIVED:
            # Archived cases are read-only; do not silently resurrect them.
            return IntakeResponse(
                case_id=case.case_id,
                status=case.status,
                profile=case.profile,
                missing_information=case.intake_state.missing_information,
                next_question=None,
                ready_for_research=False,
                message="This case is archived and no longer accepting updates.",
            )

        InnovationIntakeAgent.apply_message(
            case.profile, case.intake_state, message, phase1_entities
        )
        InnovationIntakeAgent.evaluate(case.profile, case.intake_state)

        if case.intake_state.status == IntakeStatus.READY:
            case.status = CaseStatus.READY_FOR_RESEARCH
            # Phase 3: Run assessment automatically once case is ready.
            # This is synchronous and deterministic (no LLM, no Qdrant).
            if case.assessment is None:
                try:
                    from ml_pipeline.agents.case_assessment_agent import CaseAssessmentAgent
                    assessment = CaseAssessmentAgent.assess(case.case_id, case.profile)
                    case.assessment = assessment.model_dump(mode="json")
                    logger.info("Phase 3: assessment stored for case %s", case.case_id)
                except Exception as exc:
                    logger.error("Phase 3: assessment failed for case %s: %s", case.case_id, exc)
        else:
            case.status = CaseStatus.INTAKE_IN_PROGRESS

        if case.title is None and case.profile.short_description:
            case.title = case.profile.short_description[:80]

        _persist(db, row, case)
        return CaseService._to_response(case)

    @staticmethod
    def update_profile_fields(db: Session, case_id: str, user_id: str, patch: dict) -> Case:
        """Direct structured PATCH — merges only the provided fields (no field erasure)."""
        row = db.query(CaseORM).filter(CaseORM.case_id == case_id).first()
        if row is None:
            raise CaseNotFoundError(case_id)
        if row.user_id != user_id:
            raise CaseAccessDeniedError(case_id)

        case = _to_domain(row)
        current = case.profile.model_dump(mode="json")
        for key, value in patch.items():
            if key not in current or value is None:
                continue
            if isinstance(current.get(key), list) and isinstance(value, list):
                from ml_pipeline.agents.innovation_intake_agent import _dedupe_preserve_order
                if current[key] and isinstance(current[key][0], str):
                    current[key] = _dedupe_preserve_order(current[key] + value)
                    continue
            current[key] = value
        case.profile = InnovationProfile.model_validate(current)
        InnovationIntakeAgent.evaluate(case.profile, case.intake_state)
        case.status = (
            CaseStatus.READY_FOR_RESEARCH
            if case.intake_state.status == IntakeStatus.READY
            else CaseStatus.INTAKE_IN_PROGRESS
        )
        # Phase 3: re-run assessment after PATCH if case is now ready.
        if case.status == CaseStatus.READY_FOR_RESEARCH and case.assessment is None:
            try:
                from ml_pipeline.agents.case_assessment_agent import CaseAssessmentAgent
                assessment = CaseAssessmentAgent.assess(case.case_id, case.profile)
                case.assessment = assessment.model_dump(mode="json")
                logger.info("Phase 3 (PATCH): assessment stored for case %s", case.case_id)
            except Exception as exc:
                logger.error("Phase 3 (PATCH): assessment failed for case %s: %s", case.case_id, exc)
        _persist(db, row, case)
        return case

    @staticmethod
    def assess_case(db: Session, case_id: str, user_id: str) -> Case:
        """
        Explicitly trigger or re-run Phase 3 assessment for a READY_FOR_RESEARCH case.
        Idempotent — can be called multiple times (overwrites prior assessment).
        """
        row = db.query(CaseORM).filter(CaseORM.case_id == case_id).first()
        if row is None:
            raise CaseNotFoundError(case_id)
        if row.user_id != user_id:
            raise CaseAccessDeniedError(case_id)

        case = _to_domain(row)
        if case.status == CaseStatus.INTAKE_IN_PROGRESS:
            # Best-effort: run even if intake isn't fully complete (partial assessment).
            logger.warning("Phase 3: running assessment on INTAKE_IN_PROGRESS case %s", case_id)

        from ml_pipeline.agents.case_assessment_agent import CaseAssessmentAgent
        assessment = CaseAssessmentAgent.assess(case.case_id, case.profile)
        case.assessment = assessment.model_dump(mode="json")
        logger.info("Phase 3 (explicit): assessment stored for case %s", case_id)
        _persist(db, row, case)
        return case

    @staticmethod
    def run_research(db: Session, case_id: str, user_id: str) -> Case:
        """
        Phase 4 — Executes the Research Engine: runs every Phase 3
        recommended_crag_query through the CRAG pipeline (Qdrant + CRAG
        grading/verification/abstention), aggregates evidence and risk, and
        assembles a structured, source-cited preliminary report.

        Requires a completed Phase 3 assessment (auto-runs it first if missing).
        Idempotent — re-running overwrites the prior report.
        """
        row = db.query(CaseORM).filter(CaseORM.case_id == case_id).first()
        if row is None:
            raise CaseNotFoundError(case_id)
        if row.user_id != user_id:
            raise CaseAccessDeniedError(case_id)

        case = _to_domain(row)

        from ml_pipeline.schemas.assessment_schema import CaseAssessment
        from ml_pipeline.agents.case_assessment_agent import CaseAssessmentAgent
        from ml_pipeline.agents.research_engine import ResearchEngine
        from ml_pipeline.crag.pipeline_singleton import get_crag_pipeline

        if case.assessment is None:
            logger.info("Phase 4: no Phase 3 assessment yet for case %s — running it first.", case_id)
            assessment_obj = CaseAssessmentAgent.assess(case.case_id, case.profile)
            case.assessment = assessment_obj.model_dump(mode="json")
        else:
            assessment_obj = CaseAssessment.model_validate(case.assessment)

        engine = ResearchEngine(pipeline=get_crag_pipeline())
        report = engine.run(case.case_id, case.profile, assessment_obj)
        case.research_report = report.model_dump(mode="json")
        logger.info("Phase 4: research report stored for case %s", case_id)
        _persist(db, row, case)
        return case

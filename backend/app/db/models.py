"""
SQLAlchemy ORM models (Phase 2 — Charaka IP PS045).

A single `cases` table holds the Case envelope plus the InnovationProfile and
IntakeState as JSON columns. This keeps persistence simple (no research report
tables — those belong to later phases) while satisfying the essential
requirement: case_id + user_id + conversation_id are persisted and queryable.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, JSON, Index
from app.db.session import Base


class CaseORM(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    conversation_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    status = Column(String, nullable=False, default="INTAKE_IN_PROGRESS")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))

    # JSON-serialized InnovationProfile / IntakeState / CaseAssessment (Pydantic .model_dump(mode="json")).
    profile = Column(JSON, nullable=False, default=dict)
    intake_state = Column(JSON, nullable=False, default=dict)
    # Phase 3 — Innovation Classification & Legal Domain Mapping output (nullable until assessed).
    assessment = Column(JSON, nullable=True, default=None)
    # Phase 4 — Research Engine / structured report output (nullable until research is run).
    research_report = Column(JSON, nullable=True, default=None)

    __table_args__ = (
        Index("ix_cases_user_conversation", "user_id", "conversation_id"),
    )

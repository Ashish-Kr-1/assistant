"""
Phase 2 — Innovation Intake + Case Creation API.

POST   /cases                  create a case
POST   /cases/{case_id}/intake process the next intake message
GET    /cases/{case_id}        retrieve a case
PATCH  /cases/{case_id}        directly merge structured profile fields

Ownership: user_id is client-supplied until a real auth system exists in this
project (there is none yet — see final report assumptions). Every read/write
below checks the stored case's user_id against the caller-supplied user_id and
returns 403 on mismatch, so the enforcement point is already in place and only
needs the identity source swapped once auth lands.
"""

from typing import Optional

from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.case_schema import CreateCaseRequest, IntakeMessageRequest, CasePatchRequest
from app.services.case_service import (
    CaseService, CaseNotFoundError, CaseAccessDeniedError,
)
from ml_pipeline.schemas.case_schema import Case, IntakeResponse

router = APIRouter()


@router.post("/cases", response_model=Case)
async def create_case(request: CreateCaseRequest, db: Session = Depends(get_db)):
    """
    Creates a new case for this user_id + conversation_id.
    Per Rule (Phase 2 §11), callers that want "check active case first" behavior
    should call GET /cases/active?... — this endpoint always creates a new case,
    matching the explicit "new case" confirmation flow in §12.
    """
    return CaseService.create_case(
        db, user_id=request.user_id, conversation_id=request.conversation_id, title=request.title
    )


@router.get("/cases/active", response_model=Optional[Case])
async def get_active_case(conversation_id: str, user_id: str = "anonymous_user", db: Session = Depends(get_db)):
    """Returns the current conversation's active (non-archived) case, or null if none exists."""
    return CaseService.get_active_case(db, user_id=user_id, conversation_id=conversation_id)


@router.get("/cases/{case_id}", response_model=Case)
async def get_case(case_id: str, user_id: str = "anonymous_user", db: Session = Depends(get_db)):
    try:
        return CaseService.get_case(db, case_id=case_id, user_id=user_id)
    except CaseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    except CaseAccessDeniedError:
        raise HTTPException(status_code=403, detail="This case belongs to a different user.")


@router.post("/cases/{case_id}/intake", response_model=IntakeResponse)
async def intake_message(case_id: str, request: IntakeMessageRequest, db: Session = Depends(get_db)):
    """
    Processes one progressive-intake message against an existing case.
    Never launches research, classification, or any Phase 3+ engine.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message cannot be empty.")
    try:
        return CaseService.process_intake_message(
            db, case_id=case_id, user_id=request.user_id, message=message
        )
    except CaseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    except CaseAccessDeniedError:
        raise HTTPException(status_code=403, detail="This case belongs to a different user.")


@router.patch("/cases/{case_id}", response_model=Case)
async def patch_case(case_id: str, request: CasePatchRequest, db: Session = Depends(get_db)):
    try:
        return CaseService.update_profile_fields(
            db, case_id=case_id, user_id=request.user_id, patch=request.profile_patch
        )
    except CaseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    except CaseAccessDeniedError:
        raise HTTPException(status_code=403, detail="This case belongs to a different user.")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid profile_patch: {e.errors()}")

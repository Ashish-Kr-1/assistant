from typing import Optional
from pydantic import BaseModel, Field


class CreateCaseRequest(BaseModel):
    conversation_id: str = Field(..., description="Client-managed conversation/session identifier.")
    user_id: str = Field("anonymous_user", description="Caller identity. Trusted from the client "
                          "only until a real auth system is wired in (see Phase 2 assumptions).")
    title: Optional[str] = Field(None, description="Optional human-readable case title.")


class IntakeMessageRequest(BaseModel):
    message: str = Field(..., description="The user's next free-text intake message.")
    user_id: str = Field("anonymous_user", description="Must match the case owner.")


class CasePatchRequest(BaseModel):
    user_id: str = Field("anonymous_user", description="Must match the case owner.")
    profile_patch: dict = Field(
        default_factory=dict,
        description="Partial InnovationProfile fields to merge in. List fields are merged/deduped, "
                     "not overwritten; unspecified fields are left untouched.",
    )

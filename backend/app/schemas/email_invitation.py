import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class EmailInvitationCreate(BaseModel):
    email: str


class EmailInvitationResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    email: str
    status: str
    inviter_name: str
    group_name: str
    created_at: datetime
    expires_at: datetime
    responded_at: datetime | None = None

    model_config = {"from_attributes": True}


class PendingInvitationResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    group_name: str
    group_description: str | None = None
    inviter_name: str
    member_count: int
    created_at: datetime
    expires_at: datetime


class EmailInvitationAction(BaseModel):
    action: Literal["accept", "decline"]

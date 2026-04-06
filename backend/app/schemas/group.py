import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.user import UserResponse


class GroupCreate(BaseModel):
    name: str
    description: str | None = None
    default_currency: str = "TWD"


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    default_currency: str | None = None
    cover_image_url: str | None = None


class GroupMemberResponse(BaseModel):
    user: UserResponse
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    default_currency: str
    cover_image_url: str | None = None
    created_by: uuid.UUID
    created_at: datetime
    members: list[GroupMemberResponse] = []

    model_config = {"from_attributes": True}


class SimplifiedDebt(BaseModel):
    from_user_id: uuid.UUID
    from_user_name: str
    to_user_id: uuid.UUID
    to_user_name: str
    amount: Decimal
    currency: str


class GroupListResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    default_currency: str
    member_count: int
    admin_count: int = 1
    created_at: datetime
    created_by: uuid.UUID
    my_role: str
    sort_order: int
    is_settled: bool = True
    unsettled_debts: list[SimplifiedDebt] = []

    model_config = {"from_attributes": True}


class ReorderGroupsRequest(BaseModel):
    group_ids: list[uuid.UUID]


class AddMemberRequest(BaseModel):
    user_id: uuid.UUID


class InviteTokenResponse(BaseModel):
    invite_token: str
    created_at: datetime


class InviteInfoResponse(BaseModel):
    group_id: uuid.UUID
    group_name: str
    group_description: str | None
    member_count: int

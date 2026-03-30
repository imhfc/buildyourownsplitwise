import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr

from app.schemas.user import UserResponse


class FriendRequestCreate(BaseModel):
    friend_email: EmailStr


class FriendRequestUpdate(BaseModel):
    action: str  # "accept" / "reject"


class FriendRequestResponse(BaseModel):
    id: uuid.UUID
    user: UserResponse
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FriendBalanceSummary(BaseModel):
    friend: UserResponse
    balance: Decimal  # positive = friend owes you, negative = you owe friend
    currency: str


class FriendListResponse(BaseModel):
    friend: UserResponse
    friendship_id: uuid.UUID
    since: datetime


class FriendSearchResult(BaseModel):
    user: UserResponse
    is_friend: bool
    has_pending_request: bool

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


ActivityType = Literal[
    "expense_added",
    "expense_updated",
    "expense_deleted",
    "settlement_created",
    "settlement_confirmed",
    "settlement_rejected",
    "member_added",
    "member_removed",
]


class UnreadCountResponse(BaseModel):
    count: int


class ActivityItem(BaseModel):
    id: uuid.UUID
    type: ActivityType
    group_id: uuid.UUID
    group_name: str
    actor_name: str
    description: str | None = None
    to_name: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    timestamp: datetime

    model_config = {"from_attributes": True}

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ReminderCreate(BaseModel):
    to_user: uuid.UUID
    amount: Decimal
    currency: str


class BatchReminderCreate(BaseModel):
    reminders: list[ReminderCreate]


class ReminderResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    from_user: uuid.UUID
    from_user_name: str
    to_user: uuid.UUID
    to_user_name: str
    amount: Decimal
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchReminderResponse(BaseModel):
    sent: list[ReminderResponse]
    skipped: list[dict]  # {"to_user": uuid, "reason": str}

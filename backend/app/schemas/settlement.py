import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SettlementSuggestion(BaseModel):
    from_user_id: uuid.UUID
    from_user_name: str
    to_user_id: uuid.UUID
    to_user_name: str
    amount: Decimal
    currency: str


class SettlementCreate(BaseModel):
    to_user: uuid.UUID
    amount: Decimal
    currency: str
    note: str | None = None


class SettlementResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    from_user: uuid.UUID
    from_user_name: str
    to_user: uuid.UUID
    to_user_name: str
    amount: Decimal
    currency: str
    note: str | None
    settled_at: datetime

    model_config = {"from_attributes": True}

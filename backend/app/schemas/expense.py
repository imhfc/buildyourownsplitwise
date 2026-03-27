import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ExpenseSplitInput(BaseModel):
    user_id: uuid.UUID
    amount: Decimal | None = None  # for exact split
    shares: Decimal | None = None  # for ratio/shares split


class ExpenseCreate(BaseModel):
    description: str
    total_amount: Decimal
    currency: str = "TWD"
    paid_by: uuid.UUID
    split_method: str = "equal"  # equal/ratio/exact/shares
    splits: list[ExpenseSplitInput] = []
    note: str | None = None


class ExpenseSplitResponse(BaseModel):
    user_id: uuid.UUID
    user_display_name: str
    amount: Decimal
    shares: Decimal | None

    model_config = {"from_attributes": True}


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    description: str
    total_amount: Decimal
    currency: str
    exchange_rate_to_base: Decimal
    base_currency: str
    paid_by: uuid.UUID
    payer_display_name: str
    split_method: str
    splits: list[ExpenseSplitResponse]
    note: str | None
    receipt_image_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


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

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ExpenseSplitInput(BaseModel):
    user_id: uuid.UUID
    amount: Decimal | None = None  # for exact split
    shares: Decimal | None = None  # for ratio/shares split


class ExpensePayerInput(BaseModel):
    user_id: uuid.UUID
    amount: Decimal


class ExpenseCreate(BaseModel):
    description: str
    total_amount: Decimal
    currency: str | None = None  # None = 使用群組預設幣別
    paid_by: uuid.UUID  # 單人付款（向下相容）
    payers: list[ExpensePayerInput] | None = None  # 多人付款（優先於 paid_by）
    split_method: str = "equal"  # equal/ratio/exact/shares
    splits: list[ExpenseSplitInput] = []
    note: str | None = None
    expense_date: date | None = None


class ExpenseUpdate(BaseModel):
    description: str | None = None
    total_amount: Decimal | None = None
    currency: str | None = None
    paid_by: uuid.UUID | None = None
    payers: list[ExpensePayerInput] | None = None
    split_method: str | None = None
    splits: list[ExpenseSplitInput] | None = None
    note: str | None = None
    expense_date: date | None = None


class ExpensePayerResponse(BaseModel):
    user_id: uuid.UUID
    user_display_name: str
    amount: Decimal

    model_config = {"from_attributes": True}


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
    base_amount: Decimal  # 約當預設幣別金額（= total_amount * exchange_rate_to_base）
    paid_by: uuid.UUID
    payer_display_name: str
    payers: list[ExpensePayerResponse] = []  # 多人付款明細（空 = 單人付款）
    split_method: str
    splits: list[ExpenseSplitResponse]
    note: str | None
    receipt_image_url: str | None
    expense_date: date | None
    created_at: datetime

    model_config = {"from_attributes": True}

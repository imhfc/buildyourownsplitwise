import uuid
from decimal import Decimal

from pydantic import BaseModel


class UserBalance(BaseModel):
    user_id: uuid.UUID
    display_name: str
    balance: Decimal  # positive = owed to them, negative = they owe


class GroupBalanceSummary(BaseModel):
    group_id: uuid.UUID
    group_name: str
    currency: str
    balances: list[UserBalance]


class OverallBalance(BaseModel):
    total_owed_to_you: Decimal  # 別人欠你的總額
    total_you_owe: Decimal  # 你欠別人的總額
    net_balance: Decimal
    currency: str
    by_group: list[GroupBalanceSummary]

import uuid
from decimal import Decimal

from pydantic import BaseModel


class UserBalance(BaseModel):
    user_id: uuid.UUID
    display_name: str
    balance: Decimal  # positive = owed to them, negative = they owe


class CurrencyBalance(BaseModel):
    """單一幣別內的所有使用者餘額"""
    currency: str
    balances: list[UserBalance]


class GroupBalanceSummary(BaseModel):
    """群組餘額摘要 — 按幣別分列"""
    group_id: uuid.UUID
    group_name: str
    by_currency: list[CurrencyBalance]


class CurrencyTotal(BaseModel):
    """單一幣別的應收/應付彙總"""
    currency: str
    owed_to_you: Decimal
    you_owe: Decimal
    net_balance: Decimal


class OverallBalance(BaseModel):
    """跨群組餘額總覽 — 按幣別分列，嚴禁跨幣別加總"""
    totals_by_currency: list[CurrencyTotal]
    by_group: list[GroupBalanceSummary]

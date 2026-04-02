import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


# --- 結算建議 ---

class SettlementSuggestion(BaseModel):
    from_user_id: uuid.UUID
    from_user_name: str
    to_user_id: uuid.UUID
    to_user_name: str
    amount: Decimal
    currency: str


class ExchangeRateInfo(BaseModel):
    """統一幣別結算時回傳的匯率資訊"""
    from_currency: str
    to_currency: str
    rate: Decimal
    fetched_at: datetime


class CurrencyGroupSuggestions(BaseModel):
    """分幣別結算：每個幣別一組建議"""
    currency: str
    suggestions: list[SettlementSuggestion]


class UnifiedSuggestions(BaseModel):
    """統一幣別結算：所有建議轉換為目標幣別"""
    target_currency: str
    suggestions: list[SettlementSuggestion]
    exchange_rates: list[ExchangeRateInfo]


class SettlementSuggestionsResponse(BaseModel):
    """結算建議的統一回傳結構"""
    mode: str  # "by_currency" | "unified"
    by_currency: list[CurrencyGroupSuggestions] | None = None
    unified: UnifiedSuggestions | None = None


# --- 建立/確認/回應 ---

class SettlementCreate(BaseModel):
    to_user: uuid.UUID
    amount: Decimal
    currency: str
    note: str | None = None
    # 統一幣別結算時的匯率鎖定資訊
    original_currency: str | None = None
    original_amount: Decimal | None = None
    locked_rate: Decimal | None = None


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
    status: str
    settled_at: datetime
    confirmed_at: datetime | None = None
    original_currency: str | None = None
    original_amount: Decimal | None = None
    locked_rate: Decimal | None = None

    model_config = {"from_attributes": True}

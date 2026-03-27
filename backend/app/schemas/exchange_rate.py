from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ExchangeRateResponse(BaseModel):
    source_currency: str
    target_currency: str
    rate: Decimal
    source: str
    fetched_at: datetime

    model_config = {"from_attributes": True}


class ExchangeRateConvert(BaseModel):
    from_currency: str
    to_currency: str
    amount: Decimal


class ExchangeRateConvertResponse(BaseModel):
    from_currency: str
    to_currency: str
    original_amount: Decimal
    converted_amount: Decimal
    rate: Decimal
    fetched_at: datetime

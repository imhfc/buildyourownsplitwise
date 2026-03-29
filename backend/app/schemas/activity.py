import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class ActivityItem(BaseModel):
    type: Literal["expense_added", "settlement_created"]
    group_id: uuid.UUID
    group_name: str
    actor_name: str
    description: str | None = None  # for expense_added
    to_name: str | None = None       # for settlement_created
    amount: Decimal
    currency: str
    timestamp: datetime

    model_config = {"from_attributes": True}

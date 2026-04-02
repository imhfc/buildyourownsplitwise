import uuid
from datetime import datetime

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    icon: str | None = None
    color: str | None = None
    group_id: uuid.UUID | None = None


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    icon: str | None
    color: str | None
    is_default: bool
    group_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])

_STATUS_MAP = {
    ForbiddenError: 403,
    NotFoundError: 404,
    ValidationError: 400,
}


def _handle(e: Exception):
    for exc_type, code in _STATUS_MAP.items():
        if isinstance(e, exc_type):
            raise HTTPException(status_code=code, detail=e.message)
    raise


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    group_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await category_service.list_categories(db, group_id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await category_service.create_category(db, current_user.id, data)
    except (ForbiddenError, NotFoundError, ValidationError) as e:
        _handle(e)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await category_service.delete_category(db, category_id, current_user.id)
    except (ForbiddenError, NotFoundError, ValidationError) as e:
        _handle(e)

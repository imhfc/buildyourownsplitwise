import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.services import expense_service
from app.services.group_service import check_membership

router = APIRouter(prefix="/groups/{group_id}/expenses", tags=["expenses"])

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


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    group_id: uuid.UUID,
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await expense_service.create_expense(db, group_id, current_user.id, data)
    except (ForbiddenError, ValidationError) as e:
        _handle(e)


@router.get("", response_model=list[ExpenseResponse])
async def list_expenses(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await expense_service.list_expenses(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await check_membership(db, group_id, current_user.id)
        return await expense_service.get_expense_detail(db, expense_id)
    except (ForbiddenError, NotFoundError) as e:
        _handle(e)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await expense_service.delete_expense(db, group_id, expense_id, current_user.id)
    except (ForbiddenError, NotFoundError) as e:
        _handle(e)
